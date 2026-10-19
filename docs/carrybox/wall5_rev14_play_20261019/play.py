"""GUI/finite headless playback for archived Wall5 rev14, without training/export writes."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'docs/carrybox/wall5_push_20261019/before/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball'


def main():
    from isaaclab.app import AppLauncher
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--num_envs', type=int, choices=range(1, 5), default=4)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--steps', type=int, default=0, help='0: run until window closes; positive: finite diagnostic')
    parser.add_argument('--real-time', action='store_true')
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if not args.checkpoint.is_file() or args.steps < 0:
        parser.error('checkpoint must exist and steps must be nonnegative')
    app = AppLauncher(args).app
    env = None
    try:
        import importlib.util
        import sys
        import time
        import torch
        import perceptual_ball.tasks
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic
        from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled import state

        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module

        torch.set_num_threads(2)
        device = args.device or 'cuda:0'
        checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
        if checkpoint.get('carrybox_schema') != 2 or checkpoint.get('environment_contract', {}).get('migration_revision') != 14:
            raise ValueError('This playback entry accepts only schema2 / Wall5 revision14 checkpoints')
        package = 'perceptual_ball.tasks.manager_based.perceptual_ball'
        config = load(package + '.rev14_gui_cfg', ARCHIVE / 'carrybox_wall5_env_cfg.py')
        task = load(package + '.mdp.rev14_gui_mdp', ARCHIVE / 'mdp/carrybox_wall5.py')
        cfg = config.CarryBoxWalled5EnvCfg()
        agent = config.CarryBoxWalled5PPORunnerCfg()
        cfg.scene.num_envs, cfg.seed, cfg.sim.device = args.num_envs, args.seed, device
        cfg.viewer.origin_type, cfg.viewer.env_index = 'env', 0
        cfg.viewer.eye, cfg.viewer.lookat = (2.8, -3.2, 2.1), (.65, 0., .65)
        for name in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity', 'gpu_total_aggregate_pairs_capacity'):
            setattr(cfg.sim.physx, name, 262144)
        env = task.Wall5CarryBoxEnv(cfg=cfg)
        if env.checkpoint_contract() != checkpoint['environment_contract']:
            raise ValueError('Archived environment differs from checkpoint contract')
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = wrapped.reset()
        policy_cfg = agent.policy.to_dict()
        if policy_cfg.pop('class_name') != 'CarryBoxWall5ActorCritic':
            raise ValueError('Unexpected archived policy class')
        policy = CarryBoxWall5ActorCritic(obs, agent.obs_groups, 29, **policy_cfg).to(device)
        policy.load_state_dict(checkpoint['model_state_dict'], strict=True)
        policy.eval()
        # This historical run started fresh at zero; reconstruct its course,
        # instead of restarting the warm-start course at the checkpoint iteration.
        env.set_training_iteration(0)
        env.set_training_iteration(int(checkpoint['iter']))
        with torch.inference_mode():
            obs, _ = wrapped.reset()
            print(f"REV14_PLAY_READY checkpoint={args.checkpoint} iteration={checkpoint['iter']} "
                  f"envs={args.num_envs} yaw_deg={state(env).curriculum.degrees:.2f} "
                  "actions=mean original_set_push=true friction=0.5/average", flush=True)
            steps = 0
            while app.is_running() and (args.steps == 0 or steps < args.steps):
                started = time.monotonic()
                action = policy.act_inference(obs)
                if not torch.isfinite(action).all():
                    raise FloatingPointError('Non-finite policy action')
                obs, _, _, _ = wrapped.step(action)
                steps += 1
                if args.real_time:
                    time.sleep(max(0., env.step_dt - (time.monotonic() - started)))
            print(f'REV14_PLAY_DONE steps={steps}', flush=True)
    finally:
        if env is not None:
            env.close()
        app.close(wait_for_replicator=False)


if __name__ == '__main__':
    main()
