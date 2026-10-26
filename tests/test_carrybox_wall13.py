"""Wall13 pose-feedback causality, gradient boundaries, optimizer and deployment."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
import torch
import test_carrybox_wall12 as fixtures
from perceptual_ball.carrybox_wall12 import box_pose_loss
from perceptual_ball.carrybox_wall13 import VISUAL_FEEDBACK_CONTRACT
from perceptual_ball.rsl_rl_extensions.carrybox_wall13 import (
    CarryBoxWall13ActorCritic, CarryBoxWall13PPO, CarryBoxWall13OnPolicyRunner)
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport, export_depth_policy


def algorithm():
    _, obs = fixtures.algorithm()
    policy = CarryBoxWall13ActorCritic(obs,
        {'policy':['proprio','perception'],'critic':['critic_state']},29,
        actor_hidden_dims=(32,),critic_hidden_dims=(32,))
    alg = CarryBoxWall13PPO(policy,device='cpu',amp_coef=.25,amp_reward_scale=.5,pose_aux_coef=1.,
        num_learning_epochs=1,num_mini_batches=1,learning_rate=.001,schedule='adaptive')
    alg.init_storage('rl',4,4,obs,[29])
    return alg, obs


def runner(alg):
    r = CarryBoxWall13OnPolicyRunner.__new__(CarryBoxWall13OnPolicyRunner)
    r.alg,r.device,r.current_learning_iteration = alg,'cpu',1
    r.env = NS(unwrapped=NS(checkpoint_contract=lambda: dict(variant='walled13',migration_revision=3,
        visual_feedback=dict(VISUAL_FEEDBACK_CONTRACT))))
    return r


class Wall13Tests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def assert_gradient(self, module, present):
        grads = [p.grad for p in module.parameters()]
        if present:
            self.assertTrue(all(g is not None and torch.isfinite(g).all() for g in grads))
            self.assertGreater(sum(float(g.abs().sum()) for g in grads),0.)
        else:
            self.assertTrue(all(g is None for g in grads))

    def test_prediction_changes_actions_without_privileged_inputs(self):
        alg,obs=algorithm();p=alg.policy
        features=p._features(obs)
        latent=p.perception_encoder(obs['perception'])
        self.assertEqual(features.shape,(4,695))
        torch.testing.assert_close(features[:,:558],obs['proprio'],atol=0,rtol=0)
        torch.testing.assert_close(features[:,558:686],latent,atol=0,rtol=0)
        torch.testing.assert_close(features[:,686:],p.pose_head(latent),atol=0,rtol=0)
        self.assertEqual(p.actor[0].in_features,695)
        self.assertEqual(list(p.box_pose_fusion.parameters()),[])
        self.assertFalse(any('fusion' in k for k in p.state_dict()))
        with torch.no_grad():
            expected=p.act_inference(obs)
            for column in (0,3):
                delta=torch.zeros(9);delta[column]=1.
                hook=p.pose_head.register_forward_hook(lambda m,i,o:o+delta)
                try: changed=p.act_inference(obs)
                finally:hook.remove()
                self.assertGreater(float((changed-expected).abs().max()),1.e-6)
            changed=obs.clone()
            for key in ('critic_state','box_pose_target','amp'):changed[key]+=1000
            torch.testing.assert_close(p.act_inference(changed),expected,atol=0,rtol=0)
            minimal={k:obs[k] for k in ('proprio','perception')}
            torch.testing.assert_close(p.act_inference(minimal),expected,atol=0,rtol=0)

    def test_actor_auxiliary_and_critic_gradient_boundaries(self):
        alg,obs=algorithm();p=alg.policy
        p.act_inference(obs).square().mean().backward()
        for module in (p.actor,p.perception_encoder,p.pose_head):self.assert_gradient(module,True)
        self.assert_gradient(p.critic,False)
        p.zero_grad(set_to_none=True)
        sum(box_pose_loss(p.predict_box_pose(obs),obs['box_pose_target'])).backward()
        for module in (p.perception_encoder,p.pose_head):self.assert_gradient(module,True)
        for module in (p.actor,p.critic,p.box_pose_fusion):self.assert_gradient(module,False)
        p.zero_grad(set_to_none=True)
        p.evaluate(obs).square().mean().backward()
        self.assert_gradient(p.critic,True)
        for module in (p.actor,p.perception_encoder,p.pose_head,p.box_pose_fusion):self.assert_gradient(module,False)

    def test_paired_forward_matches_live_current_and_mixed(self):
        alg,obs=algorithm();p=alg.policy
        mixed={k:obs[k].clone()+.7 for k in ('proprio','perception','critic_state')}
        mixed['perception'].requires_grad_()
        calls=[]
        hook=p.perception_encoder.register_forward_hook(lambda m,i,o:calls.append(len(i[0])))
        value,mixed_mean,mixed_value=alg._paired_training_outputs(obs,mixed)
        hook.remove()
        self.assertEqual(calls,[8])
        torch.testing.assert_close(p.action_mean,p.act_inference(obs))
        torch.testing.assert_close(mixed_mean,p.act_inference(mixed))
        torch.testing.assert_close(value,p.evaluate(obs))
        torch.testing.assert_close(mixed_value,p.evaluate(mixed))
        torch.testing.assert_close(alg._pose_prediction,p.predict_box_pose(obs))
        mixed_mean.square().mean().backward()
        self.assertGreater(float(mixed['perception'].grad.abs().sum()),0.)
        self.assert_gradient(p.pose_head,True)

    def test_joint_update_and_exact_optimizer_resume(self):
        alg,obs=algorithm();groups=alg.optimizer.param_groups
        self.assertEqual([g['weight_decay'] for g in groups],[0.,.001,.1])
        ids=[id(p) for g in groups for p in g['params']]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(set(ids),{id(p) for m in (alg.policy,alg.amp) for p in m.parameters() if p.requires_grad})
        self.assertIs(alg.optimizer,alg.amp_optimizer)
        before=copy.deepcopy(alg.policy.state_dict());obs=fixtures.collect(alg,obs);loss=alg.update()
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in loss.values()))
        self.assertEqual(loss['pose_samples'],12.)
        self.assertIsNone(alg._pose_prediction)
        for prefix in ('pose_head.','perception_encoder.','actor.','critic.'):
            self.assertTrue(any(not torch.equal(v,before[k]) for k,v in alg.policy.state_dict().items() if k.startswith(prefix)))
        self.assertTrue(alg.amp_config['auxiliary']['actor_feedback'])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.pt';runner(alg).save(path)
            other,_=algorithm();runner(other).load(path)
            self.assertEqual(alg.learning_rate,other.learning_rate)
            for a,b in zip(alg.policy.parameters(),other.policy.parameters()):
                torch.testing.assert_close(a,b,atol=0,rtol=0)
                for key in alg.optimizer.state[a]:
                    torch.testing.assert_close(alg.optimizer.state[a][key],other.optimizer.state[b][key],atol=0,rtol=0)
            fixtures.collect(other,obs);other.update()
            self.assertEqual({int(v['step']) for v in other.optimizer.state.values()},{2})

    def test_incompatible_contracts_rejected_before_parameter_load(self):
        alg,obs=algorithm();fixtures.collect(alg,obs);alg.update()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.pt';runner(alg).save(path)
            original=torch.load(path,weights_only=False)
            for mode in ('rev1','rev2','wall12','aux','fusion'):
                state=copy.deepcopy(original)
                if mode=='rev1':state['environment_contract']['migration_revision']=1
                elif mode=='rev2':state['environment_contract']['migration_revision']=2
                elif mode=='wall12':state['environment_contract']['variant']='walled12'
                elif mode=='aux':state['amp']['config']['auxiliary']['actor_feedback']=False
                else:state['amp']['config']['visual_feedback']['fusion']='none'
                for v in state['model_state_dict'].values():v.add_(1.)
                torch.save(state,path)
                before=copy.deepcopy(alg.policy.state_dict())
                with self.assertRaises(ValueError):runner(alg).load(path)
                for key,v in alg.policy.state_dict().items():torch.testing.assert_close(v,before[key],atol=0,rtol=0)

    def test_export_retains_pose_without_fusion_and_dynamic_batch_actions(self):
        import onnx
        import onnxruntime as ort
        alg,obs=algorithm();p=alg.policy.eval()
        wrapper=DepthPolicyExport(p,obs)
        self.assertTrue(any(k.startswith('pose_head.') for k in wrapper.state_dict()))
        self.assertFalse(any('fusion' in k for k in wrapper.state_dict()))
        self.assertFalse(any('critic' in k or 'amp' in k for k in wrapper.state_dict()))
        with torch.no_grad():
            expected=p.act_inference(obs)
            wrapper.pose_head[-1].bias[0]+=1.
            self.assertGreater(float((wrapper(obs['proprio'],obs['perception'])-expected).abs().max()),1.e-6)
        with tempfile.TemporaryDirectory() as directory:
            export_depth_policy(p,obs,directory)
            manifest=json.loads((Path(directory)/'manifest.json').read_text())
            self.assertEqual(manifest['box_pose_feedback'],VISUAL_FEEDBACK_CONTRACT)
            graph=onnx.load(Path(directory)/'policy.onnx');onnx.checker.check_model(graph)
            self.assertEqual([v.name for v in graph.graph.input],['flat','depth'])
            self.assertTrue(any('pose_head' in v.name for v in graph.graph.initializer))
            self.assertFalse(any('fusion' in v.name for v in graph.graph.initializer))
            jit=torch.jit.load(str(Path(directory)/'policy.pt'))
            options=ort.SessionOptions();options.intra_op_num_threads=1
            session=ort.InferenceSession(str(Path(directory)/'policy.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
            for n in (1,4):
                with torch.no_grad():reference=p.act_inference(obs[:n])
                torch.testing.assert_close(jit(obs['proprio'][:n],obs['perception'][:n]),reference,rtol=1.e-5,atol=1.e-6)
                actual=session.run(None,{'flat':obs['proprio'][:n].numpy(),'depth':obs['perception'][:n].numpy()})[0]
                torch.testing.assert_close(torch.from_numpy(actual),reference,rtol=1.e-5,atol=1.e-6)


if __name__=='__main__':
    unittest.main()
