"""Size-aware pose supervision, gradient flow, optimizer and deployment boundaries."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
import torch
import test_carrybox_wall10 as fixtures
from perceptual_ball.carrybox_wall12 import box_rotations, box_symmetry_mask, box_pose_loss
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import CarryBoxWall10ActorCritic
from perceptual_ball.rsl_rl_extensions.carrybox_wall12 import CarryBoxWall12PPO, CarryBoxWall12OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport
from isaaclab.utils.math import matrix_from_quat


def labels(n):
    quat = torch.randn(n, 4)
    quat /= quat.norm(dim=-1, keepdim=True)
    rot = matrix_from_quat(quat)
    return torch.cat((torch.randn(n, 3), rot[..., :2].transpose(-1, -2).flatten(-2),
                      torch.tensor([.21, .30, .25]).expand(n, -1)), -1)


def algorithm():
    _, obs = fixtures.algorithm()
    obs['box_pose_target'] = labels(len(obs))
    policy = CarryBoxWall10ActorCritic(obs, {'policy': ['proprio', 'perception'], 'critic': ['critic_state']},
                                     29, actor_hidden_dims=(32,), critic_hidden_dims=(32,))
    alg = CarryBoxWall12PPO(policy, device='cpu', amp_coef=.25, amp_reward_scale=.5, pose_aux_coef=1.,
                           num_learning_epochs=1, num_mini_batches=1, learning_rate=.001, schedule='adaptive')
    alg.init_storage('rl', 4, 4, obs, [29])
    return alg, obs


def runner(alg):
    r = CarryBoxWall12OnPolicyRunner.__new__(CarryBoxWall12OnPolicyRunner)
    r.alg, r.device, r.current_learning_iteration = alg, 'cpu', 1
    r.env = NS(unwrapped=NS(checkpoint_contract=lambda: dict(variant='walled12')))
    return r


def collect(alg, obs):
    with torch.inference_mode():
        for step in range(4):
            alg.act(obs)
            following = obs.clone()
            following['perception'] = torch.rand_like(obs['perception']) * 2 + .1
            following['box_pose_target'] = labels(4)
            following['amp'].fill_(.01 * step)
            done = torch.tensor([step == 0, False, False, False])
            extra = {'terminal_observations': {'env_ids': torch.tensor([0]),
                     'obs': {'amp': following['amp'][:1].clone()}}}
            alg.process_env_step(following, torch.ones(4), done, extra)
            obs = following
        alg.compute_returns(obs)
    return obs


class Wall12Tests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_proper_rotations_and_all_dimension_symmetry_groups(self):
        s = box_rotations(torch.device('cpu'), torch.float32)
        self.assertEqual(s.shape, (24, 3, 3))
        self.assertEqual(len(s.unique(dim=0)), 24)
        torch.testing.assert_close(s @ s.transpose(-1, -2), torch.eye(3).expand(24, -1, -1))
        torch.testing.assert_close(torch.linalg.det(s), torch.ones(24))
        sizes = torch.tensor([[.21,.30,.25], [.30,.30,.25], [.30,.25,.30], [.25,.30,.30],
                              [.30,.30,.30], [.30,.30001,.25]])
        self.assertEqual(box_symmetry_mask(sizes, s).sum(-1).tolist(), [4,8,8,8,24,4])
        for size in sizes[:5]:
            target = labels(24)
            target[:] = target[0].clone()
            target[:, 9:] = size
            x,y = target[:,3:6], target[:,6:9]
            r = torch.stack((x,y,torch.linalg.cross(x,y)), -1)
            candidate = r @ s  # Right multiplication in the physical box frame.
            prediction = torch.cat((target[:,:3], candidate[...,:2].transpose(-1,-2).flatten(-2)), -1)
            valid = box_symmetry_mask(target[:,9:], s)[0]
            self.assertLess(float(sum(box_pose_loss(prediction[valid], target[valid]))), 1.e-12)
            if (~valid).any():
                self.assertGreater(float(box_pose_loss(prediction[~valid], target[~valid])[1]), .01)

    def test_non_square_quarter_turn_is_not_equivalent(self):
        target = torch.tensor([[0.,0.,1., 1.,0.,0., 0.,1.,0., .21,.30,.25]])
        prediction = torch.tensor([[0.,0.,1., 0.,1.,0., -1.,0.,0.]])
        self.assertGreater(float(box_pose_loss(prediction, target)[1]), .1)
        target[:,9] = .30
        self.assertEqual(float(sum(box_pose_loss(prediction, target))), 0.)

    def test_all_labels_supervised_no_range_mask_and_detached(self):
        target = labels(4).requires_grad_()
        with torch.no_grad():
            target[:,2] = torch.tensor([-4., 0., 5., 100.])
        prediction = target[:,:9].detach().clone().requires_grad_()
        shifted = target.clone()
        shifted[:,0] = shifted[:,0] + torch.arange(1.,5.)
        position, rotation = box_pose_loss(prediction, shifted)
        self.assertAlmostEqual(float(position), 2.5)
        (position + rotation).backward()
        self.assertIsNone(target.grad)
        self.assertTrue((prediction.grad[:,0].abs() > 0).all())
        self.assertGreater(float(sum(box_pose_loss(prediction, target.flip(0)))), 0.)
        with self.assertRaises(ValueError):
            box_pose_loss(prediction, target[:,:9])

    def test_shared_current_latent_aux_gradient_and_actor_boundary(self):
        alg, obs = algorithm()
        changed = obs.clone()
        for key in ('critic_state','amp','box_pose_target'):
            changed[key] += 1000
        with torch.no_grad():
            expected = alg.policy.act_inference(obs)
            torch.testing.assert_close(alg.policy.act_inference(changed), expected, rtol=0, atol=0)
            prediction = alg.policy.predict_box_pose(obs)
        mixed = {k:obs[k]+.7 for k in ('proprio','perception','critic_state')}
        calls=[]
        handle=alg.policy.perception_encoder.register_forward_hook(lambda *args: calls.append(1))
        alg._paired_training_outputs(obs, mixed)
        handle.remove()
        self.assertEqual(len(calls),1)
        torch.testing.assert_close(alg._pose_prediction, prediction)
        sum(box_pose_loss(alg._pose_prediction, obs['box_pose_target'])).backward()
        for module in (alg.policy.perception_encoder, alg.policy.pose_head):
            self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in module.parameters()))
            self.assertGreater(sum(float(p.grad.abs().sum()) for p in module.parameters()),0.)
        self.assertTrue(all(p.grad is None for m in (alg.policy.actor,alg.policy.critic) for p in m.parameters()))
        export = torch.jit.script(DepthPolicyExport(alg.policy,obs))
        torch.testing.assert_close(export(obs['proprio'],obs['perception']), expected)
        self.assertFalse(any('pose' in k or 'critic' in k for k in export.state_dict()))

    def test_joint_update_head_membership_and_exact_resume(self):
        alg,obs=algorithm()
        groups=alg.optimizer.param_groups
        self.assertEqual([g['weight_decay'] for g in groups],[0.,.001,.1])
        ids=[id(p) for g in groups for p in g['params']]
        expected={id(p) for model in (alg.policy,alg.amp) for p in model.parameters() if p.requires_grad}
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(set(ids),expected)
        self.assertIs(alg.optimizer,alg.amp_optimizer)
        before=copy.deepcopy(alg.policy.state_dict())
        obs=collect(alg,obs)
        loss=alg.update()
        self.assertEqual(loss['pose_samples'],12.)
        self.assertAlmostEqual(loss['pose_aux_weighted'],loss['pose_position']+loss['pose_rotation'])
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in loss.values()))
        for prefix in ('pose_head.','perception_encoder.','actor.','critic.'):
            self.assertTrue(any(not torch.equal(v,before[k]) for k,v in alg.policy.state_dict().items() if k.startswith(prefix)))
        self.assertEqual({int(s['step']) for s in alg.optimizer.state.values()},{1})
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.pt'
            runner(alg).save(path)
            restored,_=algorithm(); runner(restored).load(path)
            self.assertEqual(alg.learning_rate,restored.learning_rate)
            self.assertIs(restored.optimizer,restored.amp_optimizer)
            for a,b in zip(alg.policy.parameters(),restored.policy.parameters()):
                torch.testing.assert_close(a,b,atol=0,rtol=0)
                for key in alg.optimizer.state[a]:
                    torch.testing.assert_close(alg.optimizer.state[a][key],restored.optimizer.state[b][key],atol=0,rtol=0)
            original=torch.load(path,weights_only=False)
            for key in ('variant','auxiliary'):
                broken=copy.deepcopy(original)
                if key=='variant': broken['environment_contract']['variant']='walled11'
                else: broken['amp']['config']['auxiliary']['frame']='world'
                torch.save(broken,path)
                with self.assertRaises(ValueError): runner(restored).load(path)
            obs=collect(restored,obs); restored.update()
            self.assertEqual({int(s['step']) for s in restored.optimizer.state.values()},{2})

    def test_nonfinite_auxiliary_target_stops_before_optimizer(self):
        alg,obs=algorithm(); collect(alg,obs)
        before=copy.deepcopy(alg.policy.state_dict())
        alg.storage.observations['box_pose_target'][...,0]=float('nan')
        with self.assertRaises(FloatingPointError): alg.update()
        self.assertFalse(alg.optimizer.state)
        for k,v in alg.policy.state_dict().items():
            torch.testing.assert_close(v,before[k],rtol=0,atol=0)


if __name__ == '__main__':
    unittest.main()
