"""Equivalence safeguards for wall5-only performance changes."""
import ast,copy,types,unittest
from unittest.mock import patch
from pathlib import Path
import torch
import test_carrybox as fixtures
from perceptual_ball.carrybox_wall5 import Wall5MotionLibrary,GROUND_DATASET_PATH
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxPPO
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5PPO
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/carrybox/wall5_perf_20261018/baseline_source/source/perceptual_ball/perceptual_ball'

def original_windows():
    import perceptual_ball.carrybox_wall5 as module
    tree=ast.parse((BASE/'carrybox_wall5.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Wall5MotionLibrary')
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='windows')
    scope=dict(vars(module));exec(compile(ast.Module(body=[fn],type_ignores=[]),'<baseline windows>','exec'),scope)
    return scope['windows']

class PerfTests(unittest.TestCase):
    def test_native_windows_boundary_sign_and_rng(self):
        lib=Wall5MotionLibrary(GROUND_DATASET_PATH,device='cpu');old=original_windows()
        ids=torch.arange(lib.num_clips).repeat(3)
        maxstart=lib.lengths[ids].float()-1-(lib.window_length-1)*lib.fps/lib.env_fps
        starts=torch.cat((maxstart[:lib.num_clips]*0,maxstart[:lib.num_clips]*.371,maxstart[:lib.num_clips]))
        expected=old(lib,ids,starts);actual=lib.windows(ids,starts)
        torch.testing.assert_close(actual,expected,atol=2e-6,rtol=2e-5)
        # Force antipodal representations in both the native clips and packed raw buffer.
        for clip in lib.clips:clip[2][1::2].neg_()
        if hasattr(lib,'_raw_frames'):
            # raw fields: joints29, quaternion4, angular3, ends15, linear3, box3.
            lib._raw_frames[:,29:33]=torch.cat([c[2] for c in lib.clips])
        torch.testing.assert_close(lib.windows(ids,starts),old(lib,ids,starts),atol=2e-6,rtol=2e-5)
        torch.manual_seed(37);rng=torch.get_rng_state();new=lib.sample_expert_amp_obs(123);after=torch.get_rng_state()
        torch.set_rng_state(rng)
        with patch.object(lib,'windows',types.MethodType(old,lib)):previous=lib.sample_expert_amp_obs(123)
        torch.testing.assert_close(new,previous,atol=2e-6,rtol=2e-5);self.assertTrue(torch.equal(after,torch.get_rng_state()))
        for invalid in (starts-1000,starts+1000,starts*torch.nan):
            with self.assertRaises(ValueError):lib.windows(ids,invalid)

    def test_shared_cnn_outputs_gradient_optimizer_rng(self):
        torch.manual_seed(6);obs=fixtures.observations()
        obs['box_pose_target']=torch.cat((obs['box_pose_target'],torch.tensor([[1.],[0.],[1.],[1.]])),-1)
        policy=fixtures.policy(obs);old=CarryBoxWall5PPO(policy,device='cpu',amp_coef=0.,schedule='adaptive',desired_kl=.01)
        new=CarryBoxWall5PPO(copy.deepcopy(policy),device='cpu',amp_coef=0.,schedule='adaptive',desired_kl=.01)
        values=[];states=[];counts=[]
        for alg,method in ((old,CarryBoxPPO._training_outputs),(new,CarryBoxWall5PPO._training_outputs)):
            torch.manual_seed(123);count=[0]
            handle=alg.policy.perception_encoder.register_forward_hook(lambda *a:count.__setitem__(0,count[0]+1))
            v,pose=method(alg,obs);handle.remove();counts.append(count[0]);states.append(torch.get_rng_state())
            mu=alg.policy.action_mean;sig=alg.policy.action_std
            alg._adapt_learning_rate(torch.zeros_like(mu),torch.ones_like(sig))
            logp=alg.policy.get_actions_log_prob(torch.zeros_like(mu));pos,rot=alg._pose_loss(pose,obs['box_pose_target'])
            loss=(logp.square().mean()+v.square().mean()-.01*alg.policy.entropy.mean()+.1*(pos+rot))
            values.append([v.detach(),pose.detach(),mu.detach(),sig.detach(),loss.detach()]);alg.optimizer.zero_grad();loss.backward()
        self.assertEqual(counts,[3,1]);self.assertTrue(torch.equal(*states));self.assertEqual(old.learning_rate,new.learning_rate)
        for x,y in zip(*values):torch.testing.assert_close(x,y,atol=1e-6,rtol=1e-5)
        for a,b in zip(old.policy.parameters(),new.policy.parameters()):torch.testing.assert_close(a.grad,b.grad,atol=2e-6,rtol=2e-4)
        for a in (old,new):torch.nn.utils.clip_grad_norm_(a.policy.parameters(),1.);a.optimizer.step()
        for a,b in zip(old.policy.parameters(),new.policy.parameters()):torch.testing.assert_close(a,b,atol=2e-6,rtol=2e-5)

if __name__=='__main__':unittest.main()
