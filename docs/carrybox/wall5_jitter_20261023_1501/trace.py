"""Read-only physical-step telemetry shared by video and counterfactuals."""
from pathlib import Path
import json
import numpy as np
import torch
import omni.physics.tensors as physics

class JitterTrace:
    def __init__(self, env, directory, label):
        self.env, self.directory, self.label = env, Path(directory), label
        self.active = False
        self.robot = env.scene['robot']
        self.term = env.action_manager.get_term('joint_pos')
        self.rows = []
        self.actions, self.resets, self.rewards = [], [], []
        self.physics = physics.create_simulation_view('torch')
        self.physics.set_subspace_roots('/')
        self.contacts = []
        self.foot_contacts = []
        self.peaks = []
        self.last_timestamp = None
        for i in range(env.num_envs):
            prefix = f'/World/envs/env_{i}/Robot/'
            view = self.physics.create_rigid_contact_view(prefix+'*',
                filter_patterns=[prefix+n for n in self.robot.body_names], max_contact_data_count=8192)
            assert len(view.sensor_paths) == len(self.robot.body_names)
            assert set(x.rsplit('/',1)[-1] for x in view.sensor_paths) == set(self.robot.body_names)
            self.contacts.append(view)
            self.foot_contacts.append(self.physics.create_rigid_contact_view(
                prefix+'*ankle_roll_link', filter_patterns=[], max_contact_data_count=512))
            self.peaks.append(None)
        original = env.scene.update
        def update(dt):
            result = original(dt)
            if self.active and getattr(env, '_carrybox_in_step', False):
                d = self.robot.data
                if self.last_timestamp is not None:
                    assert abs(d._sim_timestamp-self.last_timestamp-env.physics_dt) < 1e-7
                self.last_timestamp = d._sim_timestamp
                forces = [v.get_contact_force_matrix(env.physics_dt).norm(dim=-1) for v in self.contacts]
                for i,f in enumerate(forces):
                    assert f.shape == (len(self.robot.body_names), len(self.robot.body_names))
                    for a,path in enumerate(self.contacts[i].sensor_paths):
                        f[a,self.robot.body_names.index(path.rsplit('/',1)[-1])] = 0.
                    self.peaks[i] = f.clone() if self.peaks[i] is None else torch.maximum(self.peaks[i], f)
                row = dict(timestamp=torch.tensor(d._sim_timestamp), physical_step=torch.tensor(env._sim_step_counter), q=d.joint_pos, qd=d.joint_vel, target=d.joint_pos_target,
                    torque=d.applied_torque, root=d.root_state_w,
                    self_contact_max=torch.stack([f.max() for f in forces]),
                    self_contact_count=torch.stack([(f > 1.).sum() for f in forces]),
                    # Unfiltered ankle net force is a separate external-contact diagnostic.
                    foot_net=torch.stack([v.get_net_contact_forces(env.physics_dt) for v in self.foot_contacts]),
                    delay_index=self.term.delay.index,
                    saturation=self.term.target_saturation,processed=self.term.processed_actions)
                self.rows.append({k:v.detach().cpu().numpy().copy() for k,v in row.items()})
            return result
        env.scene.update = update
    def initial(self, obs):
        robot, box = self.robot.data, self.env.scene['box'].data
        result=dict(root=robot.root_state_w.clone().cpu(),q=robot.joint_pos.clone().cpu(),
            qd=robot.joint_vel.clone().cpu(), box=box.root_state_w.clone().cpu(),
            joint_stiffness=robot.joint_stiffness.clone().cpu(),joint_damping=robot.joint_damping.clone().cpu(),
            delay_index=self.term.delay.index.clone().cpu(),
            obs={k:v.clone().cpu() for k,v in obs.items()})
        result['objects']={name:obj.data.root_state_w.clone().cpu() for name,obj in self.env.scene.rigid_objects.items()}
        result['materials']=self.robot.root_physx_view.get_material_properties().clone().cpu()
        result['delay_buffer']=self.term.delay.buffer.clone().cpu()
        result['event_timers']={str(i):x.clone().cpu() for i,x in enumerate(self.env.event_manager._interval_term_time_left)}
        torch.save(result,self.directory/f'{self.label}_initial.pt')
        return result
    def before(self, action):
        self.actions.append(action.detach().cpu().numpy().copy())
    def after(self, reward, done):
        self.resets.append(done.detach().cpu().numpy().copy())
        self.rewards.append(reward.detach().cpu().numpy().copy())
    def finish(self):
        self.active = False
        assert len(self.rows) == 4*len(self.actions) == 4000, (len(self.rows),len(self.actions))
        data={k:np.stack([r[k] for r in self.rows]) for k in self.rows[0]}
        data.update(action=np.stack(self.actions),reset=np.stack(self.resets),reward=np.stack(self.rewards))
        assert all(np.isfinite(v).all() for v in data.values())
        np.savez_compressed(self.directory/f'{self.label}_trace.npz',**data)
        pairs=[]
        for i,peak in enumerate(self.peaks):
            for a,b in (peak > .1).nonzero().tolist():
                pairs.append(dict(env_id=i,a=self.contacts[i].sensor_paths[a].rsplit('/',1)[-1],
                    b=self.robot.body_names[b],peak_n=float(peak[a,b])))
        meta=dict(label=self.label,physical_hz=200,policy_hz=50,physics_steps=4000,control_steps=1000,
            joint_names=self.robot.joint_names,body_names=self.robot.body_names,
            internal_contact_pairs=pairs,
            pair_sensor_paths=[list(v.sensor_paths) for v in self.contacts],
            self_collision_enabled=self.env.cfg.scene.robot.spawn.articulation_props.enabled_self_collisions,
            torque_semantics='IsaacLab implicit actuator applied_torque PD estimate; not solver measured motor torque',
            note='Physical rows sampled after scene.update, before policy-level reset; masked by first episode in analysis. Foot net forces are not pair self forces.')
        (self.directory/f'{self.label}_trace.json').write_text(json.dumps(meta,indent=2)+'\n')
