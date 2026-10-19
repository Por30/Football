"""Bounded 4096-env full-recipe pilot; never used to seed the formal run."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import json,traceback
from pathlib import Path
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5 import Wall5CarryBoxEnv
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled import state
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
DOC=Path(__file__).resolve().parent

def main():
    torch.set_num_threads(2);cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    cfg.scene.num_envs=4096;cfg.seed=42;cfg.sim.device=args.device
    env=Wall5CarryBoxEnv(cfg=cfg)
    try:
        w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=str(DOC/'pilot'),device=args.device)
        original_log=runner.log;rows=[]
        def recorded_log(locs,*a,**kw):
            p=runner.alg.policy
            for group in (p.state_dict(),runner.alg.amp.state_dict()):assert all(torch.isfinite(v).all() for v in group.values())
            assert p.log_std.exp().max()<=1.
            counts=state(env).transition_counts
            torch.testing.assert_close(counts,counts.new_tensor([3277,0,819])*(locs['it']+1)*agent.num_steps_per_env,rtol=0,atol=0)
            row=dict(iteration=locs['it'],seconds=locs['collection_time']+locs['learn_time'],
                     losses=locs['loss_dict'],transition_counts=counts.tolist(),
                     skill_completed_counts=state(env).episode_counts.tolist(),skill_completed_steps=state(env).episode_steps.tolist())
            assert all(torch.isfinite(torch.tensor(v)) for v in row['losses'].values())
            rows.append(row);original_log(locs,*a,**kw)
        runner.log=recorded_log;runner.learn(16,init_at_random_ep_len=True)
        warm=[r['seconds'] for r in rows[-10:]]
        result=dict(status='RUNNING',num_envs=4096,iterations=16,rows=rows,
                    mean_warm_seconds=sum(warm)/len(warm),max_warm_seconds=max(warm),
                    physical_config=env.checkpoint_contract(),train_configuration=agent.to_dict(),
                    policy_parameters_finite=True,optimizer_steps=sorted({int(v['step']) for v in runner.alg.optimizer.state.values()}),
                    amp_optimizer_steps=sorted({int(v['step']) for v in runner.alg.amp_optimizer.state.values()}),
                    initialized_from='fresh',formal_training=False,used_for_formal_initialization=False)
        (DOC/'pilot.json').write_text(json.dumps(result,indent=2)+'\n')
        assert max(warm)<=6.,warm
        assert result['optimizer_steps']==[320] and result['amp_optimizer_steps']==[320]
        assert runner.alg.motion_metadata['clip_count']==13 and runner.alg.amp.running_count>0
        # Honest early-learning observation, not a learned-walking acceptance gate.
        with torch.inference_mode():
            obs,_=w.reset();first_end=torch.full((4096,),101,device=env.device,dtype=torch.long)
            for step in range(100):
                obs,reward,done,extra=w.step(runner.alg.policy.act_inference(obs))
                first_end[(first_end==101)&done.bool()]=step+1
            ids=state(env).skills==0;ends=first_end[ids];completed=ends[ends<=100]
            result['early_loco_mean_action_evaluation']=dict(horizon_steps=100,count=int(ids.sum()),
                completed=int(len(completed)),survived_100=int((ends>100).sum()),
                mean_completed_steps=float(completed.float().mean()) if len(completed) else None,
                failed_by_20=int((ends<=20).sum()),convergence_claim=False)
        result['status']='PASS';(DOC/'pilot.json').write_text(json.dumps(result,indent=2)+'\n')
        print('LOCO_PILOT_PASS',flush=True)
    finally:env.close()
try:main()
except BaseException:
    traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
