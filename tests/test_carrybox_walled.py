"""Wall migration contracts, using actual tensor/learning/MDP code."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import torch
import test_carrybox as baseline
from perceptual_ball.carrybox_walled import YawCurriculum, PairedDepthBuffer, search_reward
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as mdp
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner, CarryBoxPPO
from rsl_rl.runners import OnPolicyRunner


class WalledTests(unittest.TestCase):
    def test_curriculum_constructor_anchor_knots_and_warm_start(self):
        for variant, initial in [('walled3',10),('walled4',0)]:
            c=YawCurriculum(variant)
            self.assertEqual(c.degrees,initial)
            c.set_iteration(65000)
            self.assertEqual(c.degrees,initial)
            points=([(4000,95),(8000,180),(9000,180)] if variant=='walled3' else
                    [(5000,5),(10000,10),(15000,20),(20000,30),(25000,105),(30000,180),(40000,180)])
            for offset,expected in points:
                c.set_iteration(65000+offset); self.assertEqual(c.degrees,expected)
            fresh=YawCurriculum(variant); fresh.set_iteration(123456); self.assertEqual(fresh.degrees,initial)

    def test_paired_delay_freeze_once_and_partial_reset(self):
        d=torch.zeros(2,2,3); p=torch.zeros(2,9)
        b=PairedDepthBuffer(d,p,2)
        zero=torch.zeros(2,dtype=torch.long); delay=torch.tensor([1,0])
        for step in range(3):
            out,label=b.update(step,d+step,p+step,delay,zero)
            torch.testing.assert_close(out[:,0,0],label[:,0])
        self.assertEqual(out[0,0,0],1)
        old=out.clone()
        b.update(2,d+99,p+99,zero,zero)
        torch.testing.assert_close(b.output_depth,old)
        b.update(3,d+3,p+3,zero,torch.tensor([2,0]))
        b.update(4,d+4,p+4,zero,zero)
        self.assertEqual(b.output_pose[0,0],3)
        b.reset(torch.tensor([0]))
        b.update(4,d+40,p+40,delay,zero)
        self.assertEqual(b.output_pose[0,0],40)
        self.assertEqual(b.output_pose[1,0],4)
        torch.testing.assert_close(b.depth[0],torch.full_like(b.depth[0],40))

    def test_search_gates_direction_and_held_thresholds(self):
        marked=torch.tensor([True,True,False,True,True])
        angles=torch.tensor([1.,-1.,1.,.7,1.])
        distances=torch.tensor([1.,1.,1.,1.,.7])
        rates=torch.tensor([2.,2.,2.,2.,2.])
        reward=search_reward(marked,angles,distances,rates)
        self.assertGreater(reward[0],reward[1]); self.assertEqual(reward[2:].sum(),0)
        data=NS(body_pos_w=torch.tensor([[[0.,0.,.6],[0.,0.,.6]],[[0.,0.,.6],[0.,0.,.6]]]),
                joint_vel=torch.tensor([[2.,0.],[2.,0.]]),joint_acc=torch.tensor([[30.,0.],[30.,0.]]))
        env=NS(_walled=NS(hands=[0,1],arm_ids=[0,1]),scene={'robot':NS(data=data),'box':NS(data=NS(root_pos_w=torch.tensor([[0.,0.,.6],[0.,0.,.3]])))})
        class Scene(dict): pass
        env.scene=Scene(env.scene);env.scene.env_origins=torch.zeros(2,3)
        torch.testing.assert_close(mdp.held_joint_excess(env),torch.tensor([.5,0.]))
        torch.testing.assert_close(mdp.held_joint_excess(env,True,20.),torch.tensor([50.,0.]))

    def test_variant_checkpoint_rejection_and_explicit_transfer(self):
        obs=baseline.observations();obs['perception']=torch.rand(4,4,27,48)
        alg=CarryBoxPPO(baseline.policy(obs),device='cpu',pose_aux_coef=.5,schedule='fixed')
        runner=CarryBoxOnPolicyRunner.__new__(CarryBoxOnPolicyRunner)
        runner.alg=alg;runner.device='cpu';runner.current_learning_iteration=70000
        contract={'variant':'walled3','depth_shape':[4,27,48]}
        runner.env=NS(unwrapped=NS(checkpoint_contract=lambda:copy.deepcopy(contract)))
        before=copy.deepcopy(alg.policy.state_dict())
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'model.pt');runner.save(path)
            runner.load(path)
            contract['variant']='walled4'
            with self.assertRaisesRegex(ValueError,'environment'):runner.load(path)
            runner.warm_start(path)
            self.assertEqual(runner.current_learning_iteration,0)
            for k,v in alg.policy.state_dict().items():torch.testing.assert_close(v,before[k])
        changed=obs.clone();changed['box_pose_target']=torch.rand_like(changed['box_pose_target'])*100
        changed['amp']=torch.rand(4,640)*100
        torch.testing.assert_close(alg.policy.act_inference(obs),alg.policy.act_inference(changed))
        torch.testing.assert_close(alg.policy.evaluate(obs),alg.policy.evaluate(changed))

    def test_runner_iteration_hook_no_absolute_curriculum_jump(self):
        c=YawCurriculum('walled4')
        runner=CarryBoxOnPolicyRunner.__new__(CarryBoxOnPolicyRunner)
        runner.env=NS(unwrapped=NS(set_training_iteration=c.set_iteration))
        runner.current_learning_iteration=90000
        runner.alg=NS(update=lambda:{'loss':1.})
        original=runner.alg.update
        def learn(instance,*args):
            self.assertEqual(c.degrees,0)
            for i in range(3):instance.alg.update()
        with patch.object(OnPolicyRunner,'learn',learn):runner.learn(3)
        self.assertEqual(c.iteration,90003);self.assertAlmostEqual(c.degrees,.003)
        self.assertIs(runner.alg.update,original)

if __name__=='__main__':unittest.main()
