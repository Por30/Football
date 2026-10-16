"""Wall5 stage-A contracts: real expert tensors, PPO updates, reset history and restore."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import torch
import test_carrybox as base
import test_carrybox_amp as legacy
from perceptual_ball.carrybox_amp import FindBoxMotionLibrary, SOURCE_JOINT_NAMES
from perceptual_ball.carrybox_wall5 import Wall5MotionLibrary, project_frame
from perceptual_ball.carrybox_walled import YawCurriculum
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5PPO, CarryBoxWall5OnPolicyRunner, Wall5AMP
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled import record_episode_metrics
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport

CircularBuffer = base.fixtures.module('wall5_test_circular_buffer',
    Path('/home/cao/IsaacLab/source/isaaclab/isaaclab/utils/buffers/circular_buffer.py')).CircularBuffer


def algorithm(steps=4, dt=.02):
    obs = base.observations()
    obs['amp'] = torch.zeros(4, 350)
    alg = CarryBoxWall5PPO(base.policy(obs), device='cpu', amp_coef=.25, control_dt=dt,
                          num_learning_epochs=1, num_mini_batches=1, schedule='fixed')
    alg.init_storage('rl', 4, steps, obs, [29])
    return alg, obs


def runner(alg, cls=CarryBoxWall5OnPolicyRunner):
    obj = cls.__new__(cls)
    obj.alg, obj.device, obj.current_learning_iteration = alg, 'cpu', 1
    return obj


class Wall5Tests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_online_expert_features_and_original_data_unchanged(self):
        old, new = FindBoxMotionLibrary(), Wall5MotionLibrary()
        ids = torch.arange(old.num_clips)
        a = old.windows(ids, torch.zeros(len(ids))).reshape(-1, 10, 64)
        b = new.windows(ids, torch.zeros(len(ids)))
        self.assertEqual(b.shape, (15, 350))
        torch.testing.assert_close(b, project_frame(a).flatten(1), rtol=0, atol=0)
        self.assertEqual(old.metadata['manifest_sha256'], new.metadata['manifest_sha256'])
        self.assertNotEqual(old.metadata['feature_schema'], new.metadata['feature_schema'])
        for x, y in zip(old.clips, new.clips):
            for xx, yy in zip(x, y):
                torch.testing.assert_close(xx, yy, rtol=0, atol=0)  # RSI velocities preserved.
        frame = a[:, 0]
        robot = NS(joint_names=list(reversed(SOURCE_JOINT_NAMES)), data=NS(
            joint_pos=frame[:, :29].flip(-1), joint_vel=frame[:, 29:58].flip(-1),
            projected_gravity_b=frame[:, 58:61], root_ang_vel_b=frame[:, 61:]))
        env = NS(scene={'robot': robot})
        torch.testing.assert_close(task.amp_frame(env), b.reshape(-1, 10, 35)[:, 0], rtol=0, atol=0)
        altered = frame.clone(); altered[:, 29:58] += 10000
        torch.testing.assert_close(project_frame(altered), project_frame(frame), rtol=0, atol=0)
        for column in (0, 58, 61):
            altered = frame.clone(); altered[:, column] += 1
            self.assertFalse(torch.equal(project_frame(altered), project_frame(frame)))

    def test_raw_discriminator_and_complete_disjoint_optimizer_groups(self):
        alg, obs = algorithm()
        d = alg.amp
        x = torch.full((4, 350), 20.)
        with torch.no_grad():
            expected = d.amp_linear(d.trunk(x))
            d.obs_mean.fill_(999); d.obs_std.fill_(999)
            torch.testing.assert_close(d(x), expected, rtol=0, atol=0)
            self.assertFalse(torch.equal(d(x), d(x.clamp(-10, 10))))
        with self.assertRaises(RuntimeError): d.set_statistics(x)
        groups = alg.amp_optimizer.param_groups
        self.assertEqual([g['weight_decay'] for g in groups], [.001, .1])
        self.assertEqual([g['lr'] for g in groups], [5e-5, 5e-5])
        first, second = ({id(p) for p in g['params']} for g in groups)
        self.assertFalse(first & second)
        self.assertEqual(first | second, {id(p) for p in d.parameters()})
        self.assertEqual(d.trunk[0].in_features, 350)
        self.assertEqual(alg.learning_rate, 1e-3)  # factory default, production cfg tested in sim.
        expected = alg.policy.act_inference(obs), alg.policy.evaluate(obs)
        changed = obs.clone(); changed['amp'] += 1000; changed['box_pose_target'] += 1000
        torch.testing.assert_close(alg.policy.act_inference(changed), expected[0], rtol=0, atol=0)
        torch.testing.assert_close(alg.policy.evaluate(changed), expected[1], rtol=0, atol=0)

    def test_reward_endpoints_first_step_and_dt_invariance(self):
        for dt in (.01, .02, .04):
            alg, obs = algorithm(dt=dt)
            reward = torch.tensor([1., -1., .1, -.1])
            for style in (0., 1.):
                extra = {}
                with patch.object(alg, '_ensure_motion_library'), patch.object(alg.amp, 'predict_reward', return_value=torch.full((4,), style)):
                    mixed = alg._process_amp(obs, reward, torch.zeros(4, dtype=torch.bool), extra)
                torch.testing.assert_close(mixed, .75 * reward + .125 * style)
                self.assertTrue(alg.amp_valid[0].all())
                self.assertEqual(extra['log']['AMP/valid_fraction'], 1.)
                self.assertAlmostEqual(extra['log']['Reward/amp_per_step'], .125 * style)
                self.assertAlmostEqual(extra['log']['Reward/mixed_per_step'], mixed.mean().item())

    def test_short_terminal_partial_reset_update_and_roundtrip(self):
        alg, obs = algorithm()
        history = CircularBuffer(10, 4, 'cpu')
        initial = torch.arange(4.)[:, None].expand(-1, 35).clone() / 10
        history.append(initial)
        obs['amp'] = history.buffer.flatten(1)
        before_policy = copy.deepcopy(alg.policy.state_dict())
        before_disc = copy.deepcopy(alg.amp.state_dict())
        with torch.inference_mode():
            for step in range(4):
                alg.act(obs)
                frame = initial + (step + 1) / 100
                history.append(frame)
                terminal_motion = history.buffer.clone()
                done = torch.tensor([step == 0, step == 2, True, False])
                ids = done.nonzero().flatten()
                next_obs = obs.clone()
                terminal = {'env_ids': ids, 'obs': {'amp': terminal_motion[ids].flatten(1)}}
                # Equivalent to ObservationManager reset: fill new envs with new first frame.
                history.reset(ids)
                reset_frame = frame.clone(); reset_frame[ids] += 10
                # Avoid adding a second frame for survivors in this buffer-level fixture.
                history._buffer[:, ids] = reset_frame[ids]
                history._num_pushes[ids] = 1
                next_obs['amp'] = history.buffer.flatten(1)
                alg.process_env_step(next_obs, torch.ones(4), done, {'terminal_observations': terminal})
                torch.testing.assert_close(alg.amp_rollout[step], terminal_motion.flatten(1))
                self.assertTrue(alg.amp_valid[step].all())
                for env_id in ids:
                    torch.testing.assert_close(history.buffer[env_id], reset_frame[env_id].expand(10, 35))
                obs = next_obs
            alg.compute_returns(obs)
        losses = alg.update()
        self.assertEqual(losses['amp_valid_samples'], 16.)
        self.assertTrue(all(torch.isfinite(torch.tensor(x)) for x in losses.values()))
        self.assertFalse(torch.equal(before_disc['amp_linear.weight'], alg.amp.amp_linear.weight))
        self.assertTrue(any(not torch.equal(v, before_policy[k]) for k, v in alg.policy.state_dict().items()))
        self.assertTrue(alg.optimizer.state and alg.amp_optimizer.state)
        wrapped = torch.jit.script(DepthPolicyExport(alg.policy, obs))
        with torch.inference_mode():
            torch.testing.assert_close(wrapped(obs['proprio'], obs['perception']), alg.policy.act_inference(obs))
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'model.pt')
            runner(alg).save(path)
            fresh, _ = algorithm()
            for load_optimizer in (True, False):
                runner(fresh).load(path, load_optimizer=load_optimizer)
                for k, v in alg.amp.state_dict().items():
                    torch.testing.assert_close(fresh.amp.state_dict()[k], v, rtol=0, atol=0)
            self.assertIsNone(fresh.motion_library)
            self.assertTrue(fresh.amp_statistics_initialized)
            fresh._ensure_motion_library()
            self.assertEqual(fresh.motion_metadata, alg.motion_metadata)
            old, _ = legacy.amp_algorithm()
            for load_optimizer in (True, False):
                with self.assertRaisesRegex(ValueError, 'AMP objective'):
                    runner(old, CarryBoxOnPolicyRunner).load(path, load_optimizer=load_optimizer)
            runner(old, CarryBoxOnPolicyRunner).save(path)
            for load_optimizer in (True, False):
                with self.assertRaisesRegex(ValueError, 'AMP objective'):
                    runner(fresh).load(path, load_optimizer=load_optimizer)

    def test_real_circular_buffer_reset_no_cross_episode_or_survivor_duplication(self):
        history = CircularBuffer(10, 2, 'cpu')
        history.append(torch.tensor([[1.], [2.]]))
        torch.testing.assert_close(history.buffer[:, :, 0], torch.tensor([[1.] * 10, [2.] * 10]))
        history.append(torch.tensor([[3.], [4.]]))
        saved = history.buffer.clone()
        history.reset([0])
        history.append(torch.tensor([[10.], [5.]]))
        torch.testing.assert_close(history.buffer[0, :, 0], torch.full((10,), 10.))
        torch.testing.assert_close(history.buffer[1, :, 0], torch.tensor([2.] * 8 + [4., 5.]))
        torch.testing.assert_close(saved[0, :, 0], torch.tensor([1.] * 9 + [3.]))

    def test_metrics_count_first_steps_and_curriculum_matches_wall4(self):
        s = NS(skills=torch.tensor([0, 1, 2]), achieved=torch.zeros(3, dtype=torch.bool), actual_episode_steps=torch.tensor([1, 3, 10]))
        for name in ('episode_counts', 'success_counts', 'episode_steps', 'valid_amp_steps', 'tipped_counts', 'fell_counts'):
            setattr(s, name, torch.zeros(3, dtype=torch.long))
        env = NS(_walled=s, _carrybox_in_step=True, amp_warmup_steps=0,
                 termination_manager=NS(get_term=lambda name: torch.zeros(3, dtype=torch.bool)))
        record_episode_metrics(env, torch.arange(3))
        self.assertEqual(s.valid_amp_steps.tolist(), [1, 3, 10])
        a, b = YawCurriculum('walled4'), YawCurriculum('walled5')
        for iteration in (50000, 55000, 60000, 70000, 80000):
            a.set_iteration(iteration); b.set_iteration(iteration)
            self.assertEqual(a.degrees, b.degrees)


if __name__ == '__main__':
    unittest.main()
