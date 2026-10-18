"""One-off reproducible edits after baseline profiling; not a training entry point."""
from pathlib import Path
root=Path(__file__).resolve().parents[3];pkg=root/'source/perceptual_ball/perceptual_ball'
p=pkg/'carrybox_wall5.py';s=p.read_text();start=s.index('    def windows(self, clip_ids, native_starts):')
s=s[:start]+'''        # Cache native states, never task features: interpolation precedes rotations
        # and the nonlinear box-distance cap. Clip offsets keep windows independent.
        self._raw_frames = torch.cat([
            torch.cat((joints, quat, angular, ends.flatten(1), linear, box), -1)
            for (joints, _, quat, angular), (ends, linear, box) in zip(self.clips, self.task_clips)
        ])
        self._clip_offsets = torch.cat((self.lengths.new_zeros(1), self.lengths.cumsum(0)[:-1]))
        self._window_times = torch.arange(self.window_length, device=self.device) * self.fps / self.env_fps

    def windows(self, clip_ids, native_starts):
        if ((~torch.isfinite(native_starts)).any() | (clip_ids < 0).any() | (clip_ids >= self.num_clips).any()):
            raise ValueError('Invalid task AMP window request')
        times = native_starts[:, None] + self._window_times
        last = self.lengths[clip_ids, None] - 1
        if ((times < 0).any() | (times > last + 1.e-5).any()):
            raise ValueError('Task AMP window would cross a clip boundary')
        times = torch.minimum(times, last)
        lo = times.floor().long()
        hi = torch.minimum(lo + 1, last)
        weight = (times - lo).unsqueeze(-1)
        offsets = self._clip_offsets[clip_ids, None]
        a, b = self._raw_frames[lo + offsets], self._raw_frames[hi + offsets]
        raw = a * (1 - weight) + b * weight
        q0, q1 = a[..., 29:33], b[..., 29:33]
        q1 = torch.where((q0*q1).sum(-1, keepdim=True) < 0, -q1, q1)
        q = torch.nn.functional.normalize(q0*(1-weight)+q1*weight, dim=-1)
        result = pack_task_frame(raw[..., :29], q, raw[..., 36:51].reshape(*times.shape, 5, 3),
                                 raw[..., 51:54], raw[..., 33:36], raw[..., 54:57])
        return result.flatten(1)
'''
p.write_text(s)
p=pkg/'tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py';s=p.read_text()
s=s.replace("    support_tops = torch.zeros(len(ids), device=env.device)\n", "    support_tops = torch.zeros(len(ids), device=env.device)\n    if link_velocity:\n        root_batch = torch.empty((len(ids), 13), device=env.device)\n        joint_batch = torch.empty((len(ids), len(inverse)), device=env.device)\n        velocity_batch = torch.empty_like(joint_batch)\n",1)
s=s.replace('''            writer = robot.write_root_link_state_to_sim if link_velocity else robot.write_root_state_to_sim
            writer(root, env_ids=env_ids)
            robot.write_joint_state_to_sim(joints[frames][:,inverse], velocity[frames][:,inverse], env_ids=env_ids)
''','''            if link_velocity:
                # Keep native sampling/RNG order; submit one PhysX write after all
                # clips, avoiding repeated whole-articulation buffer refreshes.
                root_batch[selected] = root
                joint_batch[selected] = joints[frames][:, inverse]
                velocity_batch[selected] = velocity[frames][:, inverse]
            else:
                robot.write_root_state_to_sim(root, env_ids=env_ids)
                robot.write_joint_state_to_sim(joints[frames][:,inverse], velocity[frames][:,inverse], env_ids=env_ids)
''',1)
s=s.replace('''    # base_height is a reference-frame height, not the bottom of the G1 foot
''','''    if link_velocity:
        robot.write_root_link_state_to_sim(root_batch, env_ids=ids)
        robot.write_joint_state_to_sim(joint_batch, velocity_batch, env_ids=ids)
    # base_height is a reference-frame height, not the bottom of the G1 foot
''',1)
p.write_text(s)
p=pkg/'rsl_rl_extensions/carrybox.py';s=p.read_text()
s=s.replace('''    def update(self):
        totals =''','''    def _training_outputs(self, obs):
        self.policy.act(obs)
        return self.policy.evaluate(obs), self.policy.predict_box_pose(obs)

    def update(self):
        totals =''',1)
s=s.replace('''            self.policy.act(obs)
            self._adapt_learning_rate''','''            values, pose_prediction = self._training_outputs(obs)
            self._adapt_learning_rate''',1)
s=s.replace('''            values = self.policy.evaluate(obs)
''','',1)
s=s.replace('self._pose_loss(self.policy.predict_box_pose(obs),', 'self._pose_loss(pose_prediction,',1);p.write_text(s)
p=pkg/'rsl_rl_extensions/carrybox_wall5.py';s=p.read_text()
s=s.replace('''    def _pose_loss(self, prediction, target):
''','''    def _training_outputs(self, obs):
        # The encoder has no dropout/BatchNorm. All three losses backpropagate
        # through this same latent in this optimizer step; never detach/cache it.
        policy = self.policy
        latent = policy.perception_encoder(obs['perception'])
        features = torch.cat((obs['proprio'], latent), -1)
        mean = policy.actor(features)
        policy.distribution = torch.distributions.Normal(mean, policy.log_std.exp().expand_as(mean))
        policy.distribution.sample()  # preserve the former act() RNG consumption
        return policy.critic(features), policy.pose_head(latent)

    def _pose_loss(self, prediction, target):
''',1);p.write_text(s)
print('Applied equivalent Wall5 RSI/AMP/CNN optimizations')
