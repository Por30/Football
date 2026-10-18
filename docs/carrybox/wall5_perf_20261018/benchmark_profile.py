"""Full production-config profiling; checkpoints in docs are validation-only."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['baseline','candidate'],required=True)
parser.add_argument('--rsi-only',action='store_true')
AppLauncher.add_app_launcher_args(parser);args=parser.parse_args();app=AppLauncher(args).app
import cProfile,json,time,pstats,torch,gymnasium as gym, types
from pathlib import Path
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
OUT=Path(__file__).resolve().parent
CKPT=OUT.parents[2]/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_12-27-37_wall5_v13_hold_rsi/model_0.pt'
torch.backends.cuda.matmul.allow_tf32=True;torch.backends.cudnn.allow_tf32=True
torch.backends.cudnn.deterministic=False;torch.backends.cudnn.benchmark=False
cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
cfg.scene.num_envs=64 if args.rsi_only else 4096;cfg.seed=42;cfg.sim.device=args.device
if args.rsi_only:
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
assert cfg.reset_skill_probabilities==(.8,0.,.2)
assert agent.num_steps_per_env==24 and agent.algorithm.num_learning_epochs==5 and agent.algorithm.num_mini_batches==4
stage={'instrument':False};timings={};rows=[];prof=cProfile.Profile()
def wrap(obj,name,label):
    original=getattr(obj,name)
    def call(*a,**k):
        if not stage['instrument']:return original(*a,**k)
        torch.cuda.synchronize();start=time.perf_counter()
        try:return original(*a,**k)
        finally:
            torch.cuda.synchronize();s=timings.setdefault(label,{'seconds':0.,'calls':0});s['seconds']+=time.perf_counter()-start;s['calls']+=1
    setattr(obj,name,call)
env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
try:
    b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
    if args.rsi_only:
        from rsi_equivalence import check
        with torch.inference_mode():
            w.reset()
            w.step(torch.zeros(b.num_envs,29,device=b.device))
        print('RSI_ONLY_PASS',check(b,task),flush=True)
        raise SystemExit(0)
    runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/(args.phase+'_run')),device=args.device)
    runner.load(str(CKPT));runner.alg._ensure_motion_library()
    wrap(task,'initialize_reference','RSI_initialize');wrap(b,'_reset_idx','reset_total')
    wrap(b.sim,'step','physics_step');wrap(b.sim,'forward','sim_forward')
    wrap(b.scene['depth_camera'],'_update_buffers_impl','camera_update')
    wrap(b,'step','env_step');wrap(runner.alg,'act','policy_act')
    wrap(runner.alg,'process_env_step','process_env_step');wrap(runner.alg,'update','learning_update')
    wrap(runner.alg,'_update_amp','AMP_update');wrap(runner.alg.motion_library,'windows','AMP_expert_windows')
    wrap(runner.alg.policy.perception_encoder,'forward','CNN_forward')
    original_log=runner.log
    def log(locs,*a,**k):
        row={key:locs[key] for key in ('it','collection_time','learn_time')}
        row['instrumented']=stage['instrument'];rows.append(row);original_log(locs,*a,**k)
        if locs['it']==5:stage['instrument']=True;prof.enable()
    runner.log=log
    runner.learn(num_learning_iterations=8,init_at_random_ep_len=True)
    prof.disable();prof.dump_stats(str(OUT/(args.phase+'.prof')))
    with (OUT/(args.phase+'_profile.txt')).open('w') as f:pstats.Stats(prof,stream=f).sort_stats('cumulative').print_stats(100)
    stage['instrument']=False
    rsi_result=None
    if args.phase=='candidate':
        from rsi_equivalence import check
        rsi_result=check(b,task)
    # Full strict load of the validation checkpoint exercises optimizer/AMP/RNG restore.
    final=OUT/(args.phase+'_run')/'model_7.pt';runner.load(str(final))
    result=dict(phase=args.phase,threads=torch.get_num_threads(),checkpoint=str(CKPT),num_envs=4096,iterations=rows,synchronized_nested_timings=timings,strict_restore=True,rsi_equivalence=rsi_result)
    (OUT/(args.phase+'.json')).write_text(json.dumps(result,indent=2))
    print('PERF_PROFILE_PASS',json.dumps(result),flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    raise
finally:
    env.close();app.close()
