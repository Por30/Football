"""Wall5 sampling, real actuator bounds and minibatch regularization boundaries."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import torch
import test_carrybox_asymmetric as asymmetric
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5PPO, action_mean_bound_loss


class ResetBugTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(13)

    def test_fixed_quota_and_partial_reset_never_switch_skill(self):
        all_ids = torch.arange(4096)
        skills = task.fixed_skill_ids(all_ids, 4096, (.8, 0., .2))
        self.assertEqual(torch.bincount(skills, minlength=3).tolist(), [3277, 0, 819])
        subset = torch.tensor([4095, 0, 2000, 3500, 0])
        for _ in range(4):
            torch.testing.assert_close(task.fixed_skill_ids(subset, 4096, (.8, 0., .2)), skills[subset])
        self.assertEqual(task.fixed_skill_ids(torch.arange(4), 4, (.8, 0., .2)).tolist(), [0, 0, 0, 2])
        for probs in ((.8, 0., .3), (-.1, .9, .2), (float('nan'), 0., 1.)):
            with self.assertRaises(ValueError): task.fixed_skill_ids(all_ids, 4096, probs)


    def test_bounds_pair_offset_asymmetry_wrapper_and_detach(self):
        limits = torch.tensor([[[-.087267, 2.8798], [-.26, .26]]]).repeat(2, 1, 1)
        offset = torch.tensor([[.30, .01], [.31, -.01]], requires_grad=True)
        term = NS(_joint_ids=[0, 1], _offset=offset, _scale=.25)
        env = NS(action_manager=NS(get_term=lambda _: term), scene={'robot': NS(data=NS(joint_pos_limits=limits))})
        bounds = task.action_bounds(env)
        self.assertFalse(bounds.requires_grad)
        expected = torch.tensor([[-1.549068, -1.08, 9., 1.], [-1.589068, -1., 9., 1.08]])
        torch.testing.assert_close(bounds, expected)

    def test_bound_loss_zero_inside_inward_gradient_outside_and_bad_inputs(self):
        bounds = torch.tensor([[-1., -2., 2., 1.], [-.8, -1.8, 2.2, 1.2]])
        mean = torch.tensor([[0., 0.], [-.8, 1.2]], requires_grad=True)
        loss = action_mean_bound_loss(mean, bounds); loss.backward()
        self.assertEqual(loss.item(), 0.); self.assertEqual(mean.grad.abs().sum().item(), 0.)
        mean = torch.tensor([[-3., 4.], [-2.8, 4.2]], requires_grad=True)
        loss = action_mean_bound_loss(mean, bounds); loss.backward()
        torch.testing.assert_close(mean.grad, torch.tensor([[-2., 3.], [-2., 3.]]))
        self.assertAlmostEqual(loss.item(), 13., places=5)
        for invalid in (bounds * float('nan'), bounds.flip(-1)):
            with self.assertRaises(FloatingPointError): action_mean_bound_loss(mean, invalid)
        with self.assertRaises(ValueError): action_mean_bound_loss(mean, bounds[:, :2])

    def test_bound_gradient_reaches_actor_but_never_critic(self):
        obs = asymmetric.observations(); p = asymmetric.policy(obs)
        mean = p.act_inference(obs)
        bounds = torch.cat((torch.full_like(mean, -5.), torch.full_like(mean, -4.)), -1)
        action_mean_bound_loss(mean, bounds).backward()
        self.assertTrue(any(v.grad is not None and v.grad.abs().sum() > 0 for v in p.actor.parameters()))
        self.assertTrue(all(v.grad is None for v in p.critic.parameters()))

    def test_actual_minibatches_std_projection_regularization_and_private_label(self):
        obs = asymmetric.observations(); p = asymmetric.policy(obs)
        obs['action_bounds'] = torch.cat((torch.full((4, 29), -2.), torch.full((4, 29), -.2)), -1)
        alg = CarryBoxWall5PPO(p, device='cpu', amp_coef=0., action_bound_coef=.01, max_action_std=1.,
                              num_learning_epochs=2, num_mini_batches=2, entropy_coef=.01)
        alg.init_storage('rl', 4, 4, obs, [29])
        with torch.inference_mode():
            expected = p.act_inference(obs).clone(); changed = obs.clone(); changed['action_bounds'] += 100
            torch.testing.assert_close(p.act_inference(changed), expected, rtol=0, atol=0)
            for _ in range(4):
                alg.act(obs); alg.process_env_step(obs, torch.ones(4), torch.zeros(4, dtype=torch.bool), {})
            alg.compute_returns(obs)
        original = alg._training_outputs; seen=[]
        def outputs(batch):
            seen.append(p.log_std.exp().max().item())
            return original(batch)
        with patch.object(alg, '_training_outputs', outputs): result = alg.update()
        self.assertEqual(len(seen), 4); self.assertLessEqual(max(seen), 1.)
        self.assertLessEqual(p.log_std.exp().max().item(), 1.)
        self.assertGreater(result['action_bounds'], 0.)
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in result.values()))
        self.assertEqual(alg.amp_config['action_regularization']['max_std'], 1.)




    def test_walk_drops_legacy_balance_multiplier_and_keeps_failure_penalty(self):
        from isaaclab.utils.math import quat_from_euler_xyz, quat_apply_inverse
        from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled import failure_event
        class Scene(dict): pass
        n=5; z=torch.zeros(n); pitch=torch.tensor([0., .8, 0., 0., 0.])
        q=quat_from_euler_xyz(z,pitch,z)
        root=torch.tensor([[0.,0.,.7],[0.,0.,.7],[0.,0.,.3],[0.,0.,.3],[0.,0.,.7]])
        box=torch.tensor([[1.,0.,.125],[1.,0.,.125],[1.,0.,.125],[.5,0.,.125],[1.,0.,.125]])
        velocity=torch.tensor([[.85,0.,0.]]).repeat(n,1)
        data=NS(root_link_pos_w=root,root_link_quat_w=q,root_link_lin_vel_w=velocity,
                projected_gravity_b=quat_apply_inverse(q,torch.tensor([[0.,0.,-1.]]).repeat(n,1)))
        scene=Scene(robot=NS(data=data),box=NS(data=NS(root_pos_w=box)));scene.env_origins=torch.zeros(n,3)
        env=NS(scene=scene)
        balance=task.locomotion_stability(env);walk=task.walk_task(env)
        self.assertEqual(balance[0],1.);self.assertLess(balance[1],.01)
        self.assertLess(balance[2],.1);self.assertEqual(balance[3],1.)
        # Revision19 removes this multiplier, while the historical diagnostic
        # above still distinguishes tipping. Termination/one-off failure remain.
        torch.testing.assert_close(walk, torch.full_like(walk, 1.5))
        self.assertAlmostEqual(walk[0].item(),1.5,places=6)
        scene.env_origins+=torch.tensor([100.,200.,5.]);root+=scene.env_origins;box+=scene.env_origins
        torch.testing.assert_close(task.locomotion_stability(env),balance)
        torch.testing.assert_close(task.walk_task(env),walk)
        # No unwanted zero-velocity bonus: 0.85 m/s earns more than rest.
        velocity.zero_();self.assertLess(task.walk_task(env)[0],walk[0])
        env.termination_manager=NS(terminated=torch.tensor([True,True,False,False,True]),
            time_outs=torch.tensor([False,True,False,True,False]),get_term=lambda k:torch.tensor([True,True,True,False,False]))
        torch.testing.assert_close(-50*.02*failure_event(env),torch.tensor([-1.,0.,0.,0.,0.]))

    def test_old_ppo_hook_preserves_unrestricted_default(self):
        import test_carrybox as base
        from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxPPO
        obs=base.observations();p=base.policy(obs);alg=CarryBoxPPO(p,device='cpu',schedule='fixed')
        self.assertEqual(alg._policy_regularization(obs).item(),0.)
        with torch.no_grad():p.log_std.fill_(3.)
        alg._project_policy_parameters()
        torch.testing.assert_close(p.log_std,torch.ones_like(p.log_std))

    def test_explicit_old_weights_warm_start_projects_std_before_first_rollout(self):
        import tempfile
        from pathlib import Path
        from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
        obs=asymmetric.observations();p=asymmetric.policy(obs)
        alg=CarryBoxWall5PPO(p,device='cpu',amp_coef=0.,max_action_std=1.)
        runner=CarryBoxWall5OnPolicyRunner.__new__(CarryBoxWall5OnPolicyRunner)
        runner.alg=alg;runner.device='cpu';runner.environment_contract=lambda:{'migration_revision':17}
        old={k:v.clone() for k,v in p.state_dict().items()};old['log_std'].fill_(1.)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'old.pt';torch.save({'carrybox_schema':2,'model_state_dict':old},path)
            runner.warm_start(path)
        torch.testing.assert_close(p.log_std,torch.zeros_like(p.log_std))
        self.assertEqual(runner.warm_start_info['action_std_projection_max'],1.)
        self.assertEqual(runner.current_learning_iteration,0)
        self.assertFalse(alg.optimizer.state)

if __name__ == '__main__': unittest.main()
