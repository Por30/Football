"""Same-checkpoint full wall10 timing; validation artifacts stay under docs."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument('--phase', required=True)
parser.add_argument('--steps', type=int, default=100)
parser.add_argument('--iterations', type=int, default=4)
parser.add_argument('--profile', action='store_true')
parser.add_argument('--also24', action='store_true')
parser.add_argument('--envs', type=int, default=4096)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
import cProfile
import json
import pstats
import time
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall10_env_cfg import CarryBoxWalled10EnvCfg, CarryBoxWalled10PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import CarryBoxWall10OnPolicyRunner

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parents[2] / 'logs/rsl_rl/g1_carrybox_depth/walled10/2026-10-23_23-25-30_wall10_physhsi_lift_hold_v1/model_0.pt'
torch.set_num_threads(24)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = False
cfg, agent = CarryBoxWalled10EnvCfg(), CarryBoxWalled10PPORunnerCfg()
cfg.seed = 42
cfg.sim.device = args.device
cfg.scene.num_envs = args.envs
agent.num_steps_per_env = args.steps
started = time.perf_counter()
env = gym.make('Template-Perceptual-Ball-CarryBox-Walled10-v0', cfg=cfg)
try:
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    runner = CarryBoxWall10OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    if args.steps == 100:
        runner.load(str(SOURCE))
    else:
        # Timing-only alternate workload; do not claim strict 100->24 resume.
        saved = torch.load(SOURCE, map_location=args.device, weights_only=False)
        runner.alg.policy.load_state_dict(saved['model_state_dict'])
        runner.alg.amp.load_state_dict(saved['amp']['model'])
        runner.alg.optimizer.load_state_dict(saved['optimizer_state_dict'])
        runner.alg.learning_rate = runner.alg.optimizer.param_groups[0]['lr']
        torch.set_rng_state(saved['torch_rng_state'].cpu())
        torch.cuda.set_rng_state_all([x.cpu() for x in saved['cuda_rng_state']])
    runner.alg._ensure_motion_library()
    creation_seconds = time.perf_counter() - started
    with torch.inference_mode():
        obs, _ = wrapped.reset()
    env.unwrapped.episode_length_buf.random_(0, env.unwrapped.max_episode_length)
    rows = []
    profile = cProfile.Profile()
    for iteration in range(args.iterations):
        if args.profile and iteration == args.iterations - 1:
            profile.enable()
        torch.cuda.synchronize()
        start = time.perf_counter()
        with torch.inference_mode():
            for _ in range(args.steps):
                obs, reward, done, extras = wrapped.step(runner.alg.act(obs))
                runner.alg.process_env_step(obs, reward, done, extras)
            runner.alg.compute_returns(obs)
        torch.cuda.synchronize()
        collected = time.perf_counter()
        losses = runner.alg.update()
        torch.cuda.synchronize()
        finished = time.perf_counter()
        assert all(torch.isfinite(torch.tensor(value)) for value in losses.values())
        row = dict(iteration=iteration, collection=collected-start, learning=finished-collected,
                   total=finished-start, peak_allocated_gb=torch.cuda.max_memory_allocated()/1e9)
        rows.append(row)
        print('WALL10_TIMING', json.dumps(row), flush=True)
    profile.disable()
    if args.profile:
        with (OUT / (args.phase + '_profile.txt')).open('w') as stream:
            pstats.Stats(profile, stream=stream).sort_stats('cumulative').print_stats(100)
    runner.save(OUT / (args.phase + '_model.pt'))
    runner.load(OUT / (args.phase + '_model.pt'))
    assert runner.alg.optimizer is runner.alg.amp_optimizer
    result = dict(phase=args.phase, num_envs=args.envs, rollout_steps=args.steps, epochs=5, minibatches=4,
                  source=str(SOURCE), creation_seconds=creation_seconds, iterations=rows,
                  strict_same_task_restore=True, loss=losses, formal_training=False)
    (OUT / (args.phase + '.json')).write_text(json.dumps(result, indent=2)+'\n')
    if args.also24:
        # A separate workload measurement, not a default training-config change.
        import gc
        del runner
        gc.collect()
        torch.cuda.empty_cache()
        agent.num_steps_per_env = 24
        runner = CarryBoxWall10OnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        saved = torch.load(SOURCE, map_location=args.device, weights_only=False)
        runner.alg.policy.load_state_dict(saved['model_state_dict'])
        runner.alg.amp.load_state_dict(saved['amp']['model'])
        runner.alg.optimizer.load_state_dict(saved['optimizer_state_dict'])
        runner.alg.learning_rate = runner.alg.optimizer.param_groups[0]['lr']
        torch.set_rng_state(saved['torch_rng_state'].cpu())
        torch.cuda.set_rng_state_all([x.cpu() for x in saved['cuda_rng_state']])
        del saved
        runner.alg._ensure_motion_library()
        # Rollouts create inference tensors in task state; resetting that same
        # live environment must use the runner's inference-mode context too.
        with torch.inference_mode():
            obs, _ = wrapped.reset()
        env.unwrapped.episode_length_buf.random_(0, env.unwrapped.max_episode_length)
        rows24 = []
        for iteration in range(4):
            torch.cuda.synchronize()
            start = time.perf_counter()
            with torch.inference_mode():
                for _ in range(24):
                    obs, reward, done, extras = wrapped.step(runner.alg.act(obs))
                    runner.alg.process_env_step(obs, reward, done, extras)
                runner.alg.compute_returns(obs)
            torch.cuda.synchronize()
            collected = time.perf_counter()
            losses = runner.alg.update()
            torch.cuda.synchronize()
            finished = time.perf_counter()
            assert all(torch.isfinite(torch.tensor(value)) for value in losses.values())
            row = dict(iteration=iteration, collection=collected-start, learning=finished-collected,
                       total=finished-start)
            rows24.append(row)
            print('WALL10_TIMING24', json.dumps(row), flush=True)
        (OUT/('candidate24.json' if args.envs == 4096 else 'debug24.json')).write_text(json.dumps(dict(num_envs=args.envs,rollout_steps=24,
            epochs=5,minibatches=4,iterations=rows24,default_changed=False),indent=2)+'\n')
    print('WALL10_PERF_PASS', flush=True)
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    env.close()
    app.close(wait_for_replicator=False)
