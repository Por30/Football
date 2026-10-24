"""Wall10 learning and task boundaries using production tensors and real motion data."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import torch
from tensordict import TensorDict
import test_carrybox as fixtures
from perceptual_ball.carrybox_wall10 import Wall10MotionLibrary, lift_hold_mask, task_rewards
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import (
    CarryBoxWall10ActorCritic, CarryBoxWall10PPO, CarryBoxWall10OnPolicyRunner)
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport


def algorithm(steps=4):
    obs = TensorDict(dict(proprio=torch.randn(4, 558) * .05, perception=torch.rand(4, 4, 27, 48),
                         critic_state=torch.randn(4, 123) * .05, amp=torch.zeros(4, 600),
                         box_pose_target=torch.zeros(4, 9)), [4])
    policy = CarryBoxWall10ActorCritic(obs, {'policy': ['proprio', 'perception'], 'critic': ['critic_state']},
                                     29, actor_hidden_dims=(32,), critic_hidden_dims=(32,))
    alg = CarryBoxWall10PPO(policy, device='cpu', amp_coef=.25, amp_reward_scale=.5, pose_aux_coef=0.,
                           num_learning_epochs=1, num_mini_batches=1, learning_rate=1.e-3, schedule='adaptive')
    alg.init_storage('rl', 4, steps, obs, [29])
    return alg, obs


def runner(alg):
    result = CarryBoxWall10OnPolicyRunner.__new__(CarryBoxWall10OnPolicyRunner)
    result.alg, result.device, result.current_learning_iteration = alg, 'cpu', 1
    return result


class Wall10Tests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_retained_source_clip_weights_time_jitter_and_boundaries(self):
        lib = Wall10MotionLibrary()
        self.assertEqual(lib.num_clips, 15)
        for group, total in [('loco_direction', 11/28), ('pickUp', 12/28), ('carryWith', 5/28)]:
            self.assertAlmostEqual(float(lib.weights[[i for i,g in enumerate(lib.clip_groups) if g == group]].sum()), total, places=6)
        obs = lib.sample_expert_amp_obs(1024)
        self.assertEqual(obs.shape, (1024, 600))
        self.assertTrue(torch.isfinite(obs).all())
        self.assertLessEqual(float(obs.reshape(-1, 60)[:, 45:47].norm(dim=-1).max()), .700001)
        ids = torch.arange(15)
        expected = lib.frames[lib.offsets]
        torch.testing.assert_close(lib.windows(ids, torch.zeros(15)).reshape(15, 10, 60)[:, 0], expected)
        with self.assertRaisesRegex(ValueError, 'boundary'):
            lib.windows(ids, lib.lengths.float() - 1)

    def test_actor_export_privilege_boundary_and_critic_gradient(self):
        alg, obs = algorithm()
        actor = alg.policy.act_inference(obs).detach()
        changed = obs.clone()
        for key in ('critic_state', 'amp', 'box_pose_target'):
            changed[key] += 1000
        torch.testing.assert_close(alg.policy.act_inference(changed), actor, rtol=0, atol=0)
        self.assertFalse(torch.equal(alg.policy.evaluate(changed), alg.policy.evaluate(obs)))
        alg.policy.evaluate(obs).sum().backward()
        self.assertTrue(all(p.grad is None for p in alg.policy.perception_encoder.parameters()))
        self.assertTrue(any(p.grad is not None for p in alg.policy.critic.parameters()))
        export = torch.jit.script(DepthPolicyExport(alg.policy, obs))
        torch.testing.assert_close(export(obs['proprio'], obs['perception']), actor)

    def test_source_amp_raw_input_initialization_and_optimizer_membership(self):
        alg, _ = algorithm()
        x = torch.randn(4, 600) * 15
        torch.testing.assert_close(alg.amp(x), alg.amp.amp_linear(alg.amp.trunk(x)), rtol=0, atol=0)
        self.assertFalse(any('running' in k or 'obs_std' in k for k in alg.amp.state_dict()))
        self.assertGreater(float(alg.amp.amp_linear.weight.abs().max()), .5)
        self.assertIs(alg.optimizer, alg.amp_optimizer)
        groups = alg.optimizer.param_groups
        self.assertEqual([g['weight_decay'] for g in groups], [0., .001, .1])
        ids = [id(p) for g in groups for p in g['params']]
        expected = {id(p) for model in (alg.policy, alg.amp) for p in model.parameters() if p.requires_grad}
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), expected)

    def test_completion_rejects_ungrasped_moving_tilted_and_drifting_boxes(self):
        n = 8
        clear = torch.full((n,), .2); contacts = torch.ones(n, 2, dtype=torch.bool)
        up = torch.ones(n); root_up = up.clone(); head = torch.full((n,), 1.2)
        speed = torch.zeros(n); yaw = speed.clone(); box_speed = speed.clone(); drift = speed.clone()
        height = torch.full((n,), .72)
        contacts[1, 0] = False; clear[2] = .1; up[3] = .8; root_up[4] = .9
        speed[5] = .16; drift[6] = .36; height[7] = .3
        valid = lift_hold_mask(clear, contacts, up, root_up, head, speed, yaw, box_speed, drift, height)
        self.assertEqual(valid.tolist(), [True, False, False, False, False, False, False, False])

    def test_task_has_no_goal_shortcut_and_held_still_outscores_drifting(self):
        t = lambda x: torch.tensor(x, dtype=torch.float32)
        reward = task_rewards(t([1., .5, .5]), t([.85, 0., 0.]), t([0., 0., 0.]),
            t([0., 0., 0.]), t([.72, .72, .72]), torch.tensor([False, True, True]),
            t([1.2]*3), t([0., 0., 1.]), t([0., 0., 1.]), t([0., 0., 1.]), t([0., 0., 1.]))
        self.assertEqual(float(reward['carryup_task'][0]), 0.)
        self.assertAlmostEqual(float(reward['carryup_task'][1]), 2.7, places=5)
        self.assertEqual(float(reward['standup_task'][0]), 0.)
        self.assertGreater(float(reward['standup_task'][1]), float(reward['standup_task'][2]))

    def test_joint_update_terminal_motion_smoothness_and_checkpoint(self):
        alg, obs = algorithm()
        before = copy.deepcopy(alg.policy.state_dict()); before_d = alg.amp.amp_linear.weight.detach().clone()
        with torch.inference_mode():
            for step in range(4):
                alg.act(obs)
                next_obs = obs.clone()
                next_obs['amp'].fill_(.1 * (step + 1))
                done = torch.tensor([step == 0, False, False, False])
                terminal = next_obs['amp'][:1].clone()
                if done[0]:
                    next_obs['amp'][0].fill_(999)
                extra = {'terminal_observations': {'env_ids': torch.tensor([0]), 'obs': {'amp': terminal}}}
                alg.process_env_step(next_obs, torch.ones(4), done, extra)
                if done[0]:
                    torch.testing.assert_close(alg.amp_rollout[step, 0], terminal[0])
                obs = next_obs
            alg.compute_returns(obs)
        loss = alg.update()
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in loss.values()))
        self.assertEqual(loss['amp_valid_samples'], 12.)
        self.assertTrue(any(not torch.equal(before[k], v) for k,v in alg.policy.state_dict().items() if k.startswith('actor.')))
        self.assertFalse(torch.equal(before_d, alg.amp.amp_linear.weight))
        self.assertEqual({int(v['step']) for v in alg.optimizer.state.values()}, {1})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'model.pt'
            runner(alg).save(path)
            fresh, _ = algorithm(); runner(fresh).load(path)
            with torch.inference_mode():
                torch.testing.assert_close(fresh.policy.act_inference(obs), alg.policy.act_inference(obs), rtol=0, atol=0)
            torch.testing.assert_close(fresh.amp.amp_linear.weight, alg.amp.amp_linear.weight, rtol=0, atol=0)
            self.assertEqual(fresh.learning_rate, alg.learning_rate)
            self.assertIs(fresh.optimizer, fresh.amp_optimizer)
            state = torch.load(path, weights_only=False)
            state['amp']['config']['schema'] = 3
            torch.save(state, path)
            with self.assertRaisesRegex(ValueError, 'AMP objective'):
                runner(fresh).load(path)

    def test_source_reward_mixture_has_no_second_dt(self):
        alg, obs = algorithm()
        reward = torch.tensor([1., -1., .1, -.1])
        for style in (0., 1.):
            with patch.object(alg, '_ensure_motion_library'), patch.object(alg.amp, 'predict_reward', return_value=torch.full((4,), style)):
                mixed = alg._process_amp(obs, reward, torch.zeros(4, dtype=torch.bool), {})
            torch.testing.assert_close(mixed, .75 * reward + .125 * style)


if __name__ == '__main__':
    unittest.main()
