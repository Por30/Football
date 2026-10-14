"""CPU contracts use production tensors/learning code; only simulator boundaries are doubled."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
import torch
from tensordict import TensorDict
import test_soccer_v3 as fixtures
from perceptual_ball.rsl_rl_extensions.carrybox import (
    CarryBoxActorCritic, CarryBoxPPO, CarryBoxOnPolicyRunner, box_pose_loss, square_box_symmetries)
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_state import LiftHoldState
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox import box_pose_target, lift_geometry
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport


def observations(n=4):
    target = torch.zeros(n, 9)
    target[:, 2] = 1.
    target[:, 3] = target[:, 7] = 1.
    return TensorDict({'proprio': torch.randn(n, 372) * .1, 'perception': torch.rand(n, 4, 32, 48),
                       'box_pose_target': target}, [n])


def policy(obs):
    return CarryBoxActorCritic(obs, {'policy': ['proprio', 'perception'], 'critic': ['proprio', 'perception']},
                              29, actor_hidden_dims=(32,), critic_hidden_dims=(32,))


class CarryBoxTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_labels_never_enter_actor_critic_or_export(self):
        obs = observations()
        model = policy(obs)
        expected = model.act_inference(obs).detach(), model.evaluate(obs).detach()
        changed = obs.clone()
        changed['box_pose_target'] = torch.randn_like(changed['box_pose_target']) * 100
        for current in (changed, {'proprio': obs['proprio'], 'perception': obs['perception']}):
            torch.testing.assert_close(model.act_inference(current), expected[0], rtol=0, atol=0)
            torch.testing.assert_close(model.evaluate(current), expected[1], rtol=0, atol=0)
        wrapper = torch.jit.script(DepthPolicyExport(model, obs))
        torch.testing.assert_close(wrapper(obs['proprio'], obs['perception']), expected[0])
        with self.assertRaises(ValueError):
            CarryBoxActorCritic(obs, {'policy': ['proprio', 'perception'], 'critic': ['box_pose_target']}, 29)

    def test_pose_symmetries_gradients_and_label_permutation(self):
        obs = observations(8)
        target = obs['box_pose_target']
        sym = square_box_symmetries('cpu', torch.float)
        prediction = torch.cat((target[:, :3], sym[..., :2].transpose(-1, -2).flatten(-2)), -1)
        position, rotation = box_pose_loss(prediction, target)
        self.assertEqual(float(position + rotation), 0.)
        changed = target.clone(); changed[:, 0] += 1.
        self.assertGreater(float(sum(box_pose_loss(prediction, changed))), 0.)
        model = policy(obs)
        loss = sum(box_pose_loss(model.predict_box_pose(obs), target))
        loss.backward()
        for module in (model.perception_encoder, model.pose_head):
            grads = [p.grad for p in module.parameters()]
            self.assertTrue(all(g is not None and torch.isfinite(g).all() for g in grads))
            self.assertGreater(sum(float(g.abs().sum()) for g in grads), 0.)
        perm = torch.randperm(8)
        torch.testing.assert_close(sum(box_pose_loss(model.predict_box_pose(obs[perm]), target[perm])), loss)

    def test_pose_frame_quaternion_sign_and_tilt_clearance(self):
        box = NS(root_pos_w=torch.tensor([[1., 2., 3.]]), root_quat_w=torch.tensor([[1., 0., 0., 0.]]),
                 root_lin_vel_w=torch.zeros(1, 3))
        camera = NS(pos_w=torch.tensor([[1., 2., 2.]]), quat_w_ros=torch.tensor([[1., 0., 0., 0.]]))
        env = NS(scene={'box': NS(data=box), 'depth_camera': NS(data=camera)})
        target = box_pose_target(env)
        torch.testing.assert_close(target, torch.tensor([[0., 0., 1., 1., 0., 0., 0., 1., 0.]]))
        box.root_quat_w *= -1
        torch.testing.assert_close(box_pose_target(env), target)
        camera.quat_w_ros[:] = torch.tensor([[2**-.5, 0., 0., 2**-.5]])
        box.root_pos_w[:] = torch.tensor([[2., 2., 2.]])
        torch.testing.assert_close(box_pose_target(env)[:, :3], torch.tensor([[0., -1., 0.]]), atol=1.e-6, rtol=0)
        class Scene(dict): pass
        env.scene = Scene(env.scene); env.scene.env_origins = torch.zeros(1, 3); env.device = 'cpu'
        box.root_quat_w[:] = torch.tensor([[2**-.5, 2**-.5, 0., 0.]])
        box.root_pos_w[:, 2] = .15
        bottom, up, _ = lift_geometry(env)
        self.assertAlmostEqual(float(bottom), 0., places=6)
        self.assertLess(float(up), .01)

    def test_hold_requires_two_contacts_clearance_upright_and_continuity(self):
        state = LiftHoldState(5, 'cpu', hold_steps=3)
        contacts = torch.ones(5, 2, dtype=torch.bool); contacts[1, 0] = False
        clearance = torch.tensor([.2, .2, .01, .2, .2])
        upright = torch.tensor([1., 1., 1., .1, 1.])
        speed = torch.tensor([.1, .1, .1, .1, 1.])
        for step in range(3):
            state.update(step, clearance, contacts, upright, speed)
            state.update(step, clearance, contacts, upright, speed)
        self.assertEqual(state.success.tolist(), [True, False, False, False, False])
        self.assertEqual(state.count[0].item(), 3)
        state.reset(torch.tensor([1])); self.assertTrue(state.success[0])
        contacts[0, 0] = False
        state.update(4, clearance, contacts, upright, speed)
        self.assertEqual(state.count[0].item(), 0)
        state.reset(torch.tensor([0])); self.assertFalse(state.success[0])

    def test_full_ppo_update_timeout_and_checkpoint(self):
        obs = observations()
        model = policy(obs)
        alg = CarryBoxPPO(model, device='cpu', schedule='fixed', num_learning_epochs=1, num_mini_batches=1)
        alg.init_storage('rl', 4, 4, obs, [29])
        before = copy.deepcopy(model.pose_head.state_dict())
        with torch.inference_mode():
            for i in range(4):
                alg.act(obs)
                # Next-frame labels must not replace the labels of the action-time image.
                next_obs = obs.clone()
                next_obs['box_pose_target'][:, 0] += .1
                extra = {'time_outs': torch.tensor([True, False, False, False]),
                         'terminal_observations': {'env_ids': torch.tensor([0]),
                             'obs': {key: obs[key][:1] for key in ('proprio', 'perception')}}}
                alg.process_env_step(next_obs, torch.ones(4), torch.tensor([1, 0, 0, 0]), extra)
                torch.testing.assert_close(alg.storage.observations['box_pose_target'][i], obs['box_pose_target'])
                obs = next_obs
            alg.compute_returns(obs)
        losses = alg.update()
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in losses.values()))
        self.assertTrue(any(not torch.equal(v, before[k]) for k, v in model.pose_head.state_dict().items()))
        runner = CarryBoxOnPolicyRunner.__new__(CarryBoxOnPolicyRunner)
        runner.alg = alg; runner.device = 'cpu'; runner.current_learning_iteration = 4
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'model.pt'); runner.save(path)
            expected = copy.deepcopy(model.state_dict())
            with torch.no_grad(): next(model.parameters()).add_(1.)
            runner.load(path)
            for key, value in model.state_dict().items(): torch.testing.assert_close(value, expected[key])
            self.assertTrue(alg.optimizer.state)
            data = torch.load(path, weights_only=False); data['carrybox_schema'] = -1; torch.save(data, path)
            with self.assertRaises(ValueError): runner.load(path)


if __name__ == '__main__':
    unittest.main()
