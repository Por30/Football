"""512-env/200-iteration fresh learning check; not a formal success evaluation."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
from pathlib import Path
import json, statistics
import torch, gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg, CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled import state
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
OUT=Path(__file__).resolve().parent

def main():
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32=True;torch.backends.cudnn.allow_tf32=True
    cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    cfg.scene.num_envs=512;cfg.seed=42;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'pilot_run'),device=args.device)
        assert not runner.alg.optimizer.state and not runner.alg.amp_optimizer.state
        rows=[];s=state(b);expected=torch.bincount(s.skills,minlength=3).tolist()
        assert expected==[410,0,102]
        before={k:v.clone() for k,v in runner.alg.policy.state_dict().items()}
        projection=runner.alg._project_policy_parameters;minibatches=0
        def checked_projection():
            nonlocal minibatches
            projection();minibatches+=1
            assert torch.isfinite(runner.alg.policy.log_std).all() and runner.alg.policy.log_std.exp().max() <= 1.
        runner.alg._project_policy_parameters=checked_projection
        original=runner.log
        def log(locs,*a,**kw):
            assert torch.bincount(s.skills,minlength=3).tolist()==expected
            assert all(torch.isfinite(torch.tensor(v)) for v in locs['loss_dict'].values())
            logs=locs['ep_infos'];selected={}
            keys=[k for k in logs[-1] if k.startswith(('Sampling/','Reward/loco_','Reward/hold_','Motion/','Control/'))]
            for key in keys:
                values=[float(x[key]) for x in logs if key in x]
                assert all(torch.isfinite(torch.tensor(v)) for v in values)
                selected[key]=statistics.mean(values)
            assert abs(selected['Sampling/loco_transition_fraction']-410/512)<1e-7
            assert abs(selected['Sampling/hold_transition_fraction']-102/512)<1e-7
            row=dict(iteration=locs['it'],seconds=locs['collection_time']+locs['learn_time'],
                episode_counts=s.episode_counts.tolist(),episode_steps=s.episode_steps.tolist(),
                tipped=s.tipped_counts.tolist(),fell=s.fell_counts.tolist(),loss=locs['loss_dict'],metrics=selected)
            rows.append(row);original(locs,*a,**kw)
            (OUT/'pilot_progress.json').write_text(json.dumps(row,indent=2))
        runner.log=log
        runner.learn(200,init_at_random_ep_len=True)
        assert len(rows)==200 and minibatches==4000
        assert all(torch.isfinite(v).all() for v in runner.alg.policy.state_dict().values())
        for prefix in ('actor.','critic.','perception_encoder.','pose_head.'):
            assert any(not torch.equal(before[k],v) for k,v in runner.alg.policy.state_dict().items() if k.startswith(prefix)),prefix
        assert runner.alg.motion_metadata['clip_count']==13
        for opt in (runner.alg.optimizer,runner.alg.amp_optimizer):
            assert all(float(x['step'])==4000 for x in opt.state.values())
        def window(lo,hi):
            a=rows[lo-1] if lo else dict(episode_counts=[0]*3,episode_steps=[0]*3,tipped=[0]*3,fell=[0]*3)
            z=rows[hi-1];result={}
            for i,name in enumerate(('loco','pickup','hold')):
                count=z['episode_counts'][i]-a['episode_counts'][i]
                result[name]=dict(completed=count,mean_steps=(z['episode_steps'][i]-a['episode_steps'][i])/count if count else None,
                    tipped=(z['tipped'][i]-a['tipped'][i])/count if count else None,
                    fell=(z['fell'][i]-a['fell'][i])/count if count else None)
            result['seconds_per_iteration']=statistics.mean(r['seconds'] for r in rows[lo:hi])
            result['metrics']={k:statistics.mean(r['metrics'][k] for r in rows[lo:hi]) for k in rows[lo]['metrics']}
            return result
        result=dict(status='PASS',initialization='fresh',num_envs=512,iterations=200,minibatch_checks=minibatches,
            contract=b.checkpoint_contract(),first_25=window(0,25),last_25=window(175,200),rows=rows,
            conclusion='Engineering learning check only; walking/lifting success not established')
        (OUT/'pilot.json').write_text(json.dumps(result,indent=2))
        print('PILOT_PASS',json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
    finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
