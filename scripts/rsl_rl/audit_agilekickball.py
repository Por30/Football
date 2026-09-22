"""Read-only checkpoint diagnosis, no gradient updates or policy changes."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
app=AppLauncher(args).app
env=None
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_env_cfg import AgileKickballEnvCfg, AgileKickballPPORunnerCfg
from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic


def main():
    global env
    torch.set_num_threads(2)
    out=Path('docs/agilekickball/training_audit_20260921')
    ckpt=Path('logs/rsl_rl/agilekickball_v0/2026-09-20_18-02-42_learning_fix/model_25200.pt')
    saved=torch.load(ckpt,map_location=args.device,weights_only=False)
    cfg,agent=AgileKickballEnvCfg(),AgileKickballPPORunnerCfg()
    cfg.scene.num_envs=16; cfg.sim.device=args.device; cfg.seed=921
    env=gym.make('Template-Perceptual-Ball-AgileKickball-v0',cfg=cfg)
    base=env.unwrapped; wrapper=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
    obs,_=wrapper.reset()
    pc=agent.policy.to_dict(); pc.pop('class_name')
    policy=PerceptionActorCritic(obs,agent.obs_groups,29,**pc).to(args.device).eval()
    policy.load_state_dict(saved['model_state_dict'])
    kb=base._kickball; robot=base.scene['robot']
    output={'checkpoint':str(ckpt),'checkpoint_exposure':saved['agile_incoming_exposure_steps'],'num_envs':16,'steps_per_condition':1000,'conditions':{}}
    with torch.inference_mode():
        for mode,offset in [('training_course',saved['agile_incoming_exposure_steps']),('default_play_course',0.)]:
            torch.manual_seed(921)
            kb.exposure_offset=offset; kb.incoming_steps.zero_()
            obs,_=wrapper.reset()
            start_counters=kb.metrics(); rows=[]; events=[]; reward=[]; done_count=0
            for step in range(1000):
                action=policy.act_inference(obs)
                prediction=policy.predict_ball_state(obs)
                shuffled=obs.clone(); shuffled['perception']=obs['perception'].roll(1,0)
                shuffled_prediction=policy.predict_ball_state(shuffled)
                shuffled_action=policy.act_inference(shuffled)
                depth=obs['perception']
                rows.append({'target':obs['privileged'].clone(),'prediction':prediction.clone(),
                    'shuffled_prediction':shuffled_prediction.clone(),'status':obs['ball_status'].clone(),
                    'visible':(depth[:,-1].flatten(1).amin(-1)<2.99999),
                    'history_visible':(depth.flatten(1).amin(-1)<2.99999),
                    'action_depth_delta_rad':((shuffled_action-action)*.25).square().mean(-1).sqrt(),
                    'foot_speed':robot.data.body_link_lin_vel_w[:,kb.foot_body_ids].norm(dim=-1).amax(-1).clone(),
                    'joint_vel_rms':robot.data.joint_vel.square().mean(-1).sqrt().clone(),
                    'root_speed':robot.data.root_lin_vel_w.norm(dim=-1).clone()})
                obs,_,done,_=wrapper.step(action)
                done_count+=int(done.sum()); reward.append(base.reward_manager._step_reward.clone())
                ids=kb.kick_success_flag.nonzero().flatten()
                for idx in ids.tolist():
                    near=kb.foot_ball_dist[idx].argmin()
                    events.append({'step':step,'env':idx,'foot_distance':kb.foot_ball_dist[idx,near].item(),
                        'foot_speed':robot.data.body_link_lin_vel_w[idx,kb.foot_body_ids[near]].norm().item(),
                        'return_speed':kb.ball_return_speed[idx].item()})
            data={k:torch.cat([r[k] for r in rows]) for k in rows[0]}
            assert torch.isfinite(data['prediction']).all() and torch.isfinite(data['target']).all()
            groups={'all':torch.ones(16000,dtype=torch.bool,device=args.device),
                    'active_visible':data['status'][:,0].bool()&data['visible'],
                    'incoming':data['status'][:,1].bool(),'near_foot':data['status'][:,2].bool(),
                    'near_foot_visible':data['status'][:,2].bool()&data['visible'],
                    'near_foot_no_history':data['status'][:,2].bool()&~data['history_visible']}
            stats={}
            for name,mask in groups.items():
                r={'count':int(mask.sum()),'fraction':mask.float().mean().item()};stats[name]=r
                if not mask.any(): continue
                target,pred,shuf=[data[k][mask] for k in ['target','prediction','shuffled_prediction']]
                epos=(pred[:,:3]-target[:,:3]).norm(dim=-1)*100
                evel=(pred[:,3:]-target[:,3:]).norm(dim=-1)
                speed_error=(pred[:,3:].norm(dim=-1)-target[:,3:].norm(dim=-1)).abs()
                r.update(position_rmse_cm=epos.square().mean().sqrt().item(),velocity_rmse=evel.square().mean().sqrt().item(),
                    velocity_p95=torch.quantile(evel,.95).item(),speed_mae=speed_error.mean().item(),
                    speed_rmse=speed_error.square().mean().sqrt().item(),true_speed_mean=target[:,3:].norm(dim=-1).mean().item(),
                    predicted_speed_mean=pred[:,3:].norm(dim=-1).mean().item(),
                    shuffled_velocity_rmse=(shuf[:,3:]-target[:,3:]).square().sum(-1).mean().sqrt().item(),
                    current_visible_fraction=data['visible'][mask].float().mean().item(),
                    history_visible_fraction=data['history_visible'][mask].float().mean().item(),
                    foot_speed_mean=data['foot_speed'][mask].mean().item(),foot_speed_p95=torch.quantile(data['foot_speed'][mask],.95).item(),
                    joint_velocity_rms_mean=data['joint_vel_rms'][mask].mean().item(),
                    root_speed_mean=data['root_speed'][mask].mean().item(),
                    depth_action_delta_rad_mean=data['action_depth_delta_rad'][mask].mean().item())
            end=kb.metrics()
            counters={k:end[k]-start_counters[k] for k in end if k!='AgileKickball/waiting_fraction'}
            event_speeds=torch.tensor([e['foot_speed'] for e in events])
            result={'serve_speed_range':kb.serve_speed_range,'serve_distance_range':kb.serve_distance_range,
                    'metrics':stats,'delta_counters_excluding_initial16':counters,'episode_resets':done_count,
                    'reward_weighted_per_second':dict(zip(base.reward_manager.active_terms,torch.cat(reward).mean(0).tolist())),
                    'kick_proxy_events':len(events),'proxy_foot_speed_mean':event_speeds.mean().item() if len(events) else None,
                    'proxy_fraction_foot_below_0p2_m_s':(event_speeds<.2).float().mean().item() if len(events) else None,
                    'event_examples':events[:40]}
            output['conditions'][mode]=result
            torch.save(data,out/(mode+'_samples.pt'))
            print(mode,json.dumps(result),flush=True)
    # Exercise the actual production runner inference-load path and play's first reset.
    from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
    runner=BallRegressionOnPolicyRunner(wrapper,agent.to_dict(),log_dir=None,device=args.device)
    with torch.inference_mode():
        runner.load(str(ckpt),load_optimizer=False)
        assert abs(kb.exposure_steps-saved['agile_incoming_exposure_steps'])<1.e-4
        obs,_=wrapper.reset()
        distance=(base.scene['ball'].data.root_pos_w[:,:2]-kb.anchor_xy).norm(dim=-1)
        assert ((distance>=1.3-1.e-5)&(distance<=2.+1.e-5)).all()
        torch.testing.assert_close(policy.act_inference(obs),runner.alg.policy.act_inference(obs))
        output['corrected_play_load']={'exposure':kb.exposure_steps,'first_ball_distance_min_m':distance.min().item(),
            'first_ball_distance_max_m':distance.max().item(),'serve_speed_range':kb.serve_speed_range,
            'production_runner_load_optimizer_false':True,'policy_unchanged':True}
    (out/'replay.json').write_text(json.dumps(output,indent=2)+'\n')

try:
    main()
except BaseException:
    import traceback,sys,os
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
    if env is not None: env.close()
    app.close(wait_for_replicator=False)
