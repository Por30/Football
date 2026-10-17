"""Four bounded inference-only conditions; production training is untouched."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
import json, statistics as st
from pathlib import Path
import torch, gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat, wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg, CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task, carrybox as base
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
CHECKPOINT = ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a/model_7200.pt'
N, STEPS = 16, 1200

def main():
    torch.set_num_threads(2)
    cfg = CarryBoxWalled5EnvCfg()
    cfg.scene.num_envs=N; cfg.seed=42; cfg.sim.device=args.device
    for key in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,key,262144)
    agent = CarryBoxWalled5PPORunnerCfg()
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped; w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=args.device)
        runner.load(str(CHECKPOINT),load_optimizer=False)
        runner.alg.policy.eval(); runner.alg.amp.eval()
        before={k:v.clone() for k,v in runner.alg.policy.state_dict().items()}
        b.set_training_iteration(0); b.set_training_iteration(7200)
        s=task.state(b); robot=b.scene['robot']; box=b.scene['box']
        assert abs(s.curriculum.degrees-7.2)<1.e-9 and s.curriculum.iteration-s.curriculum.anchor>=5000
        active=None; original_reset=b._reset_idx
        ages=torch.zeros(N,dtype=torch.long,device=b.device)
        last_push=torch.full_like(ages,-1); push_counts=torch.zeros_like(ages)
        metric_names=['style','near_box','both_contact','box_high','hand_error','distance_xy','root_z','raw_action_clip','physical_target_clip']
        sums=torch.zeros(3,len(metric_names),device=b.device); counts=torch.zeros(3,device=b.device)

        def snapshot(i):
            roll,pitch,_=euler_xyz_from_quat(robot.data.root_quat_w[i:i+1])
            root_z=float(robot.data.root_pos_w[i,2]-b.scene.env_origins[i,2])
            head_z=float(task.head_height(b)[i])
            return dict(skill=int(s.skills[i]),steps=int(ages[i]),actual_steps=int(s.actual_episode_steps[i]),
                root_z=root_z,head_z=head_z,roll=float(wrap_to_pi(roll)[0]),pitch=float(wrap_to_pi(pitch)[0]),
                tipped=bool(task.tipped(b)[i]),fell=bool(task.fallen(b)[i]),
                timeout=bool(b.termination_manager.time_outs[i]),success=bool(s.achieved[i]),
                box_z=float(box.data.root_pos_w[i,2]-b.scene.env_origins[i,2]),
                distance_xy=float((box.data.root_pos_w[i,:2]-robot.data.root_pos_w[i,:2]).norm()),
                root_vel=robot.data.root_vel_w[i].tolist(),push_count=int(push_counts[i]),
                steps_since_push=None if int(last_push[i])<0 else int(ages[i]-last_push[i]))

        def reset_capture(ids):
            if active is not None and getattr(b,'_carrybox_in_step',False):
                ended=[snapshot(i) for i in ids.tolist()]
                assert all(e['steps']==e['actual_steps'] and e['steps']>0 for e in ended)
                active['episodes'].extend(ended)
            original_reset(ids)
            ages[ids]=0; last_push[ids]=-1; push_counts[ids]=0
            if active is not None:
                active['resets'].extend(snapshot(i) for i in ids.tolist())
        b._reset_idx=reset_capture
        event=b.event_manager.get_term_cfg('push_robot')
        original_push=event.func
        disable_push=False
        def push_capture(env,ids,**kw):
            if disable_push:
                return
            old=robot.data.root_vel_w[ids].clone()
            original_push(env,ids,**kw)
            last_push[ids]=ages[ids];push_counts[ids]+=1
            if active is not None:
                for j,i in enumerate(ids.tolist()):
                    active['pushes'].append(dict(env=i,skill=int(s.skills[i]),age=int(ages[i]),before=old[j].tolist(),after=robot.data.root_vel_w[i].tolist()))
        event.func=push_capture
        b.event_manager.set_term_cfg('push_robot',event)
        result=dict(status='RUNNING',checkpoint=str(CHECKPOINT),num_envs=N,steps_per_case=STEPS,
            training_updates=0,curriculum_iteration=7200,yaw_deg=7.2,
            cases={},joint_names=robot.joint_names,action_std=runner.alg.policy.log_std.exp().tolist(),
            caveats=['Same seed is not paired episodes after RNG/reset divergence','Censored episodes remain separate; completed means are length-biased','Depth noise and other randomization retained in all four cases','Small-scene inference does not establish formal task success or training causality'])
        with torch.inference_mode():
            for name,sample,no_push in [('sample_push',True,False),('sample_no_push',True,True),('mean_push',False,False),('mean_no_push',False,True)]:
                active=None;disable_push=no_push;torch.manual_seed(42)
                obs,_=w.reset();ages.zero_();last_push.fill_(-1);push_counts.zero_();sums.zero_();counts.zero_()
                active=dict(episodes=[],resets=[],pushes=[],initial=[snapshot(i) for i in range(N)])
                done_count=0
                for step in range(STEPS):
                    action=runner.alg.policy.act(obs) if sample else runner.alg.policy.act_inference(obs)
                    assert torch.isfinite(action).all() and all(torch.isfinite(v).all() for v in obs.values())
                    skill=s.skills.clone()
                    distance=(box.data.root_pos_w[:,:2]-robot.data.root_pos_w[:,:2]).norm(dim=-1)
                    hands=robot.data.body_pos_w[:,s.hands].mean(1)
                    data=torch.stack((runner.alg.amp.predict_reward(obs['amp']).flatten(),(distance<.7).float(),
                        base.hand_contacts(b).all(-1).float(),(box.data.root_pos_w[:,2]-b.scene.env_origins[:,2]>.6).float(),
                        (hands-box.data.root_pos_w).norm(dim=-1),distance,
                        robot.data.root_pos_w[:,2]-b.scene.env_origins[:,2],(action.abs()>9).float().mean(-1)),dim=-1)
                    ages+=1
                    obs,reward,done,_=w.step(action)
                    assert torch.isfinite(reward).all()
                    physical=b.action_manager.get_term('joint_pos').target_saturation.float().mean(-1)
                    data=torch.cat((data,physical[:,None]),dim=-1)
                    sums.index_add_(0,skill,data);counts.index_add_(0,skill,torch.ones(N,device=b.device))
                    done_count+=int(done.sum())
                    if (step+1)%400==0:print('REPLAY_PROGRESS',name,step+1,'done',done_count,flush=True)
                censored=[snapshot(i) for i in range(N)]
                assert done_count==len(active['episodes'])
                assert sum(e['steps'] for e in active['episodes'])+sum(e['steps'] for e in censored)==N*STEPS
                by_skill={}
                for skill,label in enumerate(('loco','pickup','hold')):
                    es=[e for e in active['episodes'] if e['skill']==skill]
                    by_skill[label]=dict(completed=len(es),mean_completed_steps=st.mean(e['steps'] for e in es) if es else None,
                        median_completed_steps=st.median(e['steps'] for e in es) if es else None,
                        ends_before_first_push=sum(e['push_count']==0 for e in es),
                        ended_within_10_steps=sum(e['steps']<=10 for e in es),
                        tipped=sum(e['tipped'] for e in es),fell=sum(e['fell'] for e in es),timeouts=sum(e['timeout'] for e in es),
                        successes=sum(e['success'] for e in es),
                        censored_ages=[e['steps'] for e in censored if e['skill']==skill],
                        state_samples=int(counts[skill]),
                        state_means={k:float(sums[skill,j]/counts[skill]) for j,k in enumerate(metric_names)} if counts[skill] else {})
                active.update(by_skill=by_skill,censored=censored,done_count=done_count,
                    mean_completed_steps=st.mean(e['steps'] for e in active['episodes']),
                    action_mode='sample' if sample else 'mean',push_enabled=not no_push)
                result['cases'][name]=active
                print('CASE_SUMMARY',name,json.dumps(by_skill),flush=True)
                (OUT/'replay_result.json').write_text(json.dumps(result,indent=2)+'\n')
                active=None
        assert all(torch.equal(v,before[k]) for k,v in runner.alg.policy.state_dict().items())
        result['status']='PASS';result['parameters_unchanged']=True
        (OUT/'replay_result.json').write_text(json.dumps(result,indent=2)+'\n')
        print('WALL5_REPLAY_PASS',flush=True)
    finally:
        env.close()
try:
    main()
finally:
    app.close(wait_for_replicator=False)
