"""Measure actual failed-policy NLL saturation and gradients on simulated states."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser);args=parser.parse_args()
app=AppLauncher(args).app
env=None
import copy,json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from tensordict import TensorDict
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v3_feedback_legacy_env_cfg import AgileKickballV3EnvCfg,AgileKickballV3PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic
from perceptual_ball.rsl_rl_extensions.state_feedback import StateFeedbackActorCritic


def main():
 global env
 torch.set_num_threads(2)
 cfg=AgileKickballV3EnvCfg();cfg.scene.num_envs=16;cfg.sim.device=args.device;cfg.seed=4208
 env=gym.make('Template-Perceptual-Ball-AgileKickball-v3-StateFeedback-20261006',cfg=cfg);base=env.unwrapped;wrapped=RslRlVecEnvWrapper(env)
 acfg=AgileKickballV3PPORunnerCfg();pcfg=acfg.policy.to_dict();pcfg.pop('class_name')
 obs,_=wrapped.reset(); policy=StateFeedbackActorCritic(obs,acfg.obs_groups,29,**pcfg).to(args.device)
 state=torch.load('logs/rsl_rl/agilekickball_v3/2026-10-06_13-17-10_state_feedback_20261006_scratch/model_49999.pt',map_location=args.device,weights_only=False)
 policy.load_state_dict(state['model_state_dict']);policy.eval()
 kb=base._kickball;kb.curriculum_training=False;kb.course_exposure=60000.;kb.serve_speed_override=(.4,2.);kb._sync_course()
 samples=[];seen_kick=torch.zeros(16,dtype=torch.bool,device=args.device);ended_after=0;ended_before=0
 with torch.inference_mode():
  torch.manual_seed(4208);obs,_=wrapped.reset()
  for step in range(160):
   if step%5==0:samples.append(obs.clone())
   seen_kick|=kb.ball_kicked
   obs,_,dones,_=wrapped.step(policy.act_inference(obs))
   ended_after+=int((dones.bool()&seen_kick).sum());ended_before+=int((dones.bool()&~seen_kick).sum());seen_kick[dones.bool()]=False
 batch=torch.cat(samples,dim=0).clone()
 raw=policy.ball_head(PerceptionActorCritic._actor_features(policy,batch))
 mean,logstd=policy.ball_distribution(batch)
 normalized_error=batch['privileged']/policy.ball_state_scale-mean
 terms=.5*(normalized_error*(-logstd).exp()).square()+logstd
 def grad_norm(loss):
  policy.zero_grad(set_to_none=True);loss.backward(retain_graph=True)
  return float(torch.cat([p.grad.flatten() for p in policy.perception_encoder.parameters() if p.grad is not None]).norm())
 nll_norm=grad_norm(terms.mean());mse_norm=grad_norm(.5*normalized_error.square().mean())
 report={'num_states':len(batch),'raw_logstd_below_min_fraction_per_dim':(raw[:,6:]<-4).float().mean(0).tolist(),
         'raw_logstd_above_max_fraction_per_dim':(raw[:,6:]>1).float().mean(0).tolist(),
         'raw_logstd_min_per_dim':raw[:,6:].amin(0).tolist(),'raw_logstd_max_per_dim':raw[:,6:].amax(0).tolist(),
         'nll_mean_per_dim':terms.mean(0).tolist(),'mean_error_weight_per_dim':(-2*logstd).exp().mean(0).tolist(),
         'nll_encoder_gradient_norm':nll_norm,'half_normalized_mse_encoder_gradient_norm':mse_norm,
         'nll_to_half_normalized_mse_encoder_grad_ratio':nll_norm/max(1e-12,mse_norm),
         'termination_after_prior_kick_pulse':ended_after,'termination_without_prior_kick_pulse':ended_before,
         'note':'Actual sampled-state diagnostic. Gradient ratio does not alone establish training causality.'}
 params=list(policy.perception_encoder.parameters())+list(policy.ball_head.parameters())
 original=copy.deepcopy(policy.state_dict())
 with torch.no_grad():old_mu=policy.act_inference(batch).clone();std=policy.std.clone()
 trials=[]
 for lr in (1e-3,1e-4,1e-5):
  policy.load_state_dict(original)
  optimizer=torch.optim.Adam(params,lr=lr);optimizer.load_state_dict(copy.deepcopy(state['ball_aux_optimizer_state_dict']))
  optimizer.param_groups[0]['lr']=lr;optimizer.zero_grad(set_to_none=True)
  (.5*policy.ball_nll(batch)).backward();torch.nn.utils.clip_grad_norm_(params,1.);optimizer.step()
  with torch.no_grad():kl=(.5*((policy.act_inference(batch)-old_mu)/std).square().sum(-1)).mean().item()
  trials.append({'lr':lr,'same_state_action_kl_unbacktracked':kl})
 report['one_aux_step_trials']=trials
 out=Path('docs/agilekickball_v3/stability_fix_20261008')
 (out/'probe.json').write_text(json.dumps(report,indent=2)+'\n');torch.save(batch.cpu(),out/'probe_observations.pt')
 print('NLL_PROBE',json.dumps(report),flush=True)

try:main()
except BaseException:
 import traceback,sys,os
 traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
 if env is not None:env.close()
 app.close(wait_for_replicator=False)
