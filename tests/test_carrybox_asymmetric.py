"""Wall5 privileged value boundaries; actor/deployment remain depth and proprio only."""
import copy,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import torch
import test_carrybox as base
import test_carrybox_wall5 as legacy
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic,CarryBoxWall5PPO
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.carrybox_wall5 import GROUND_DATASET_PATH
from isaaclab.utils.math import quat_apply,quat_mul,quat_from_euler_xyz

def observations():
    o=base.observations();o['perception']=torch.rand(4,4,27,48);o['critic_state']=torch.randn(4,123)
    o['amp']=torch.zeros(4,600);o['box_pose_target']=torch.cat((o['box_pose_target'],torch.ones(4,1)),-1)
    return o

def policy(o):
    return CarryBoxWall5ActorCritic(o,{'policy':['proprio','perception'],'critic':['critic_state']},29,
                                    actor_hidden_dims=(32,),critic_hidden_dims=(32,))

def environment():
    n=4;z=torch.zeros(n);q=quat_from_euler_xyz(z+.2,z-.3,z+.8)
    r=NS(root_link_quat_w=q,root_link_pos_w=torch.randn(n,3),root_link_lin_vel_w=torch.randn(n,3),
         root_ang_vel_b=torch.randn(n,3),projected_gravity_b=torch.randn(n,3),joint_pos=torch.randn(n,29),
         default_joint_pos=torch.zeros(n,29),joint_vel=torch.randn(n,29),default_joint_vel=torch.zeros(n,29))
    r.body_link_pos_w=torch.randn(n,7,3)
    def find_bodies(names,preserve_order=False):
        assert names==list(task.AMP_BODY_NAMES) and preserve_order
        return [4,0,6,2,1],names
    box=NS(root_pos_w=torch.randn(n,3),root_quat_w=quat_from_euler_xyz(z-.1,z+.5,z-.7))
    return NS(scene={'robot':NS(data=r,find_bodies=find_bodies),'box':NS(data=box)},action_manager=NS(action=torch.randn(n,29)),
              cfg=NS(scene=NS(box=NS(spawn=NS(size=(.30,.30,.25))))))

class AsymmetricTests(unittest.TestCase):
    def setUp(self):torch.manual_seed(42)

    def test_physical_frames_sign_invariance_and_actual_size(self):
        e=environment();r=e.scene['robot'].data;b=e.scene['box'].data;a=task.critic_state(e)
        self.assertEqual(a.shape,(4,123));self.assertFalse(a.requires_grad)
        torch.testing.assert_close(a[:,:93],task.base.proprioception(e))
        torch.testing.assert_close(quat_apply(r.root_link_quat_w,a[:,93:96]),r.root_link_lin_vel_w)
        torch.testing.assert_close(quat_apply(r.root_link_quat_w,a[:,96:99]),b.root_pos_w-r.root_link_pos_w)
        ends=a[:,108:].reshape(4,5,3)
        torch.testing.assert_close(quat_apply(r.root_link_quat_w[:,None].expand(-1,5,-1),ends),
                                   r.body_link_pos_w[:,[4,0,6,2,1]]-r.root_link_pos_w[:,None])
        r.root_link_quat_w.neg_();b.root_quat_w.neg_();torch.testing.assert_close(task.critic_state(e),a)
        z=torch.zeros(4);rotation=quat_from_euler_xyz(z,z,z+1.1);translation=torch.tensor([100.,200.,3.])
        r.body_link_pos_w=quat_apply(rotation[:,None].expand(-1,7,-1),r.body_link_pos_w)+translation
        r.root_link_pos_w=quat_apply(rotation,r.root_link_pos_w)+translation
        b.root_pos_w=quat_apply(rotation,b.root_pos_w)+translation
        r.root_link_lin_vel_w=quat_apply(rotation,r.root_link_lin_vel_w)
        r.root_link_quat_w=quat_mul(rotation,r.root_link_quat_w);b.root_quat_w=quat_mul(rotation,b.root_quat_w)
        torch.testing.assert_close(task.critic_state(e),a,atol=2e-5,rtol=2e-5)
        e.cfg.scene.box.spawn.size=(.4,.5,.6)
        torch.testing.assert_close(task.critic_state(e)[:,105:108],torch.tensor([[.4,.5,.6]]).expand(4,-1))

    def test_actor_identical_and_no_privileged_export_or_value_depth_dependency(self):
        o=observations();torch.manual_seed(5);old=base.policy(o);torch.manual_seed(5);p=policy(o)
        for name in ('actor','perception_encoder','pose_head'):
            for x,y in zip(getattr(old,name).parameters(),getattr(p,name).parameters()):torch.testing.assert_close(x,y,rtol=0,atol=0)
        action=p.act_inference(o).detach();value=p.evaluate(o).detach();changed=o.clone()
        changed['critic_state']+=100;changed['box_pose_target']*=100;changed['amp']+=100
        torch.testing.assert_close(p.act_inference(changed),action,rtol=0,atol=0)
        self.assertFalse(torch.equal(p.evaluate(changed),value))
        torch.testing.assert_close(p.evaluate({'critic_state':o['critic_state']}),value)
        torch.testing.assert_close(p.act_inference({'proprio':o['proprio'],'perception':o['perception']}),action)
        exported=torch.jit.script(DepthPolicyExport(p,o));torch.testing.assert_close(exported(o['proprio'],o['perception']),action)
        self.assertFalse(any('critic' in k for k in exported.state_dict()))

    def test_value_gradients_never_reach_depth_actor_or_pose_head(self):
        o=observations();p=policy(o);alg=CarryBoxWall5PPO(p,device='cpu',amp_coef=0.)
        calls=[];hook=p.perception_encoder.register_forward_hook(lambda *args:calls.append(1))
        values,pose=alg._training_outputs(o);hook.remove();self.assertEqual(len(calls),1)
        torch.testing.assert_close(values,p.evaluate(o));values.square().mean().backward()
        self.assertTrue(any(x.grad is not None and x.grad.abs().sum()>0 for x in p.critic.parameters()))
        for m in (p.perception_encoder,p.actor,p.pose_head):self.assertTrue(all(x.grad is None for x in m.parameters()))
        p.zero_grad();(p.act_inference(o).square().mean()+p.predict_box_pose(o).square().mean()).backward()
        self.assertTrue(all(x.grad is None for x in p.critic.parameters()))
        self.assertTrue(any(x.grad is not None and x.grad.abs().sum()>0 for x in p.perception_encoder.parameters()))

    def test_terminal_snapshot_before_physics_reset_and_partial_survivors(self):
        e=environment();obj=task.Wall5CarryBoxEnv.__new__(task.Wall5CarryBoxEnv)
        obj.scene=e.scene;obj.cfg=e.cfg;obj.action_manager=e.action_manager;obj._carrybox_in_step=True
        ids=torch.tensor([0,2]);expected=task.critic_state(obj).clone()
        def parent_reset(env,indices):
            env._carrybox_terminal={'env_ids':indices.clone(),'obs':{'amp':torch.zeros(2,600)}}
            env.scene['box'].data.root_pos_w[indices]+=10
        with patch.object(task.WalledCarryBoxEnv,'_reset_idx',parent_reset):obj._reset_idx(ids)
        torch.testing.assert_close(obj._carrybox_terminal['obs']['critic_state'],expected[ids])
        torch.testing.assert_close(task.critic_state(obj)[[1,3]],expected[[1,3]])
        self.assertFalse(torch.equal(task.critic_state(obj)[ids],expected[ids]))

    def test_timeout_bootstraps_terminal_privileged_state(self):
        o=observations();p=policy(o);alg=CarryBoxWall5PPO(p,device='cpu',amp_coef=0.)
        alg.init_storage('rl',4,1,o,[29]);terminal=torch.randn(2,123)*5
        done=torch.tensor([True,True,False,False]);timeout=torch.tensor([True,False,False,False]);reward=torch.ones(4)
        with torch.inference_mode():
            alg.act(o);expected=reward.clone();expected[0]+=alg.gamma*p.evaluate({'critic_state':terminal})[0,0]
            new=o.clone();new['critic_state']+=1000
            alg.process_env_step(new,reward,done,{'time_outs':timeout,'terminal_observations':{'env_ids':torch.tensor([0,1]),'obs':{'critic_state':terminal}}})
        torch.testing.assert_close(alg.storage.rewards[0,:,0],expected)

    def test_ppo_amp_update_restore_and_old_contract_rejection(self):
        o=observations()
        def make():
            a=CarryBoxWall5PPO(policy(o),device='cpu',amp_coef=.25,amp_data_dir=GROUND_DATASET_PATH,
                              num_learning_epochs=1,num_mini_batches=1,pose_aux_coef=1.0,schedule='adaptive',desired_kl=.01)
            a.init_storage('rl',4,2,o,[29]);return a
        a=make();before=copy.deepcopy(a.policy.state_dict())
        with torch.inference_mode():
            for _ in range(2):a.act(o);a.process_env_step(o,torch.ones(4),torch.zeros(4,dtype=torch.bool),{})
            a.compute_returns(o)
        result=a.update();self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in result.values()))
        self.assertEqual(a.motion_metadata['clip_count'],13)
        for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
            self.assertTrue(any(not torch.equal(before[k],v) for k,v in a.policy.state_dict().items() if k.startswith(prefix)))
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/'model.pt');r=legacy.runner(a);r.env=NS(unwrapped=NS(checkpoint_contract=lambda:{'migration_revision':22}));r.save(path)
            restored=make();rr=legacy.runner(restored);rr.env=r.env;rr.load(path)
            torch.testing.assert_close(restored.policy.act_inference(o),a.policy.act_inference(o))
            torch.testing.assert_close(restored.policy.evaluate(o),a.policy.evaluate(o))
            bad=torch.load(path,weights_only=False);bad['environment_contract']['migration_revision']=21;torch.save(bad,path)
            with self.assertRaisesRegex(ValueError,'environment variant/contract'):rr.load(path)

if __name__=='__main__':unittest.main()
