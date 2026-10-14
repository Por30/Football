"""Bounded CPU physics, new-policy PPO, serve geometry and checkpoint checks."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
env = None

import json
from pathlib import Path
import gymnasium as gym
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v2_env_cfg import (
    AgileKickballV2EnvCfg, AgileKickballV2PPORunnerCfg)
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v3_env_cfg import (
    AgileKickballV3EnvCfg, AgileKickballV3PPORunnerCfg)
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v3 import REVISION


def main():
    global env
    torch.set_num_threads(2)
    out = Path('docs/agilekickball_v3/validation')
    out.mkdir(parents=True, exist_ok=True)
    cfg, agent = AgileKickballV3EnvCfg(), AgileKickballV3PPORunnerCfg()
    old, oldagent = AgileKickballV2EnvCfg(), AgileKickballV2PPORunnerCfg()
    assert old.terminations.walked_away.params['max_dist'] == .6
    assert cfg.terminations.walked_away.params['max_dist'] == 1.2
    olddict, newdict = old.to_dict(), cfg.to_dict()
    for item in (olddict, newdict):
        item['events'].pop('setup_kickball_state')
        item['terminations'].pop('walked_away')
    assert olddict == newdict, 'Only v3 startup and travel limit may differ'
    oldrunner, newrunner = oldagent.to_dict(), agent.to_dict()
    oldrunner.pop('experiment_name'); newrunner.pop('experiment_name')
    assert oldrunner == newrunner
    cfg.scene.num_envs = 16
    cfg.sim.device = args.device
    cfg.seed = 42
    agent.num_steps_per_env = 8
    agent.algorithm.num_learning_epochs = 1
    agent.algorithm.num_mini_batches = 1
    env = gym.make('Template-Perceptual-Ball-AgileKickball-v3', cfg=cfg)
    base = env.unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    kb = base._kickball
    runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    with torch.inference_mode():
        obs, _ = wrapped.reset()
        assert kb.ball_active.all() and kb.serve_distance_range == (.5, .7)
    losses = []
    for _ in range(2):
        with torch.inference_mode():
            for _ in range(8):
                actions = runner.alg.act(obs)
                obs, rewards, dones, infos = wrapped.step(actions)
                runner.alg.process_env_step(obs, rewards, dones, infos)
            runner.alg.compute_returns(obs)
        result = runner.alg.update()
        assert all(torch.isfinite(torch.tensor(v)) for v in result.values()), result
        losses.append(result)
    assert sum(row['ball/incoming/count'] for row in losses) > 0
    sampling = []
    with torch.inference_mode():
        for exposure, expected_high, expected_width in [(0., .7, .25), (30000., 1.85, .3), (60000., 3., .35)]:
            state = kb.curriculum_state_dict()
            state.update(exposure_steps=exposure, extension_unlocked=False,
                         extension_steps=0., advance_rate=0.)
            kb.load_curriculum_state_dict(state)
            obs, _ = wrapped.reset()
            assert abs(kb.serve_distance_range[1] - expected_high) < 1e-6
            assert kb.serve_aim_offset_range == (-expected_width, expected_width)
            pos = kb.ball.data.root_pos_w[:, :2] - kb.anchor_xy
            vel = kb.ball.data.root_lin_vel_w[:, :2]
            dist = pos.norm(dim=-1)
            radial = pos / dist[:, None]
            t = -dist / (radial * vel).sum(-1)
            target = pos + vel * t[:, None]
            assert ((dist >= kb.serve_distance_range[0] - 1e-5) & (dist <= expected_high + 1e-5)).all()
            assert (target.norm(dim=-1) <= expected_width + 1e-5).all()
            sampling.append({'exposure': exposure, 'distance_min_m': dist.min().item(),
                             'distance_max_m': dist.max().item(), 'aim_max_m': target.norm(dim=-1).max().item()})
        # Construct the final speed stage to test persistence, not to claim learning.
        state = kb.curriculum_state_dict()
        state.update(extension_unlocked=True, extension_start_upper=1.1, extension_steps=288000.)
        kb.load_curriculum_state_dict(state)
        runner.current_learning_iteration = 2
        runner.save(str(out / 'course.pt'))
        saved = kb.curriculum_state_dict()
        runner.load(str(out / 'course.pt'), load_optimizer=False)
        obs, _ = wrapped.reset()
        for _ in range(24):
            obs, _, _, _ = wrapped.step(runner.alg.policy.act_inference(obs))
        assert kb.curriculum_state_dict() == saved
        assert kb.serve_distance_range == (1.3, 3.)
        # Maximum-range, maximum-speed initial balls must survive the first tick.
        kb.serve_speed_override = (6., 6.)
        kb._sync_course()
        obs, _ = wrapped.reset()
        kb.serve_distance_range = (3., 3.)
        kb.reset(torch.arange(16, device=args.device))
        dist = (kb.ball.data.root_pos_w[:, :2] - kb.anchor_xy).norm(dim=-1)
        torch.testing.assert_close(dist, torch.full_like(dist, 3.), atol=2e-5, rtol=0)
        speed = kb.ball.data.root_lin_vel_w[:, :2].norm(dim=-1)
        torch.testing.assert_close(speed, torch.full_like(speed, 6.), atol=1e-5, rtol=0)
        wrapped.step(torch.zeros(16, base.action_manager.total_action_dim, device=args.device))
        assert kb.ball_active.all(), 'A 3m incoming serve must not immediately end'
        kb._sync_course()
        assert kb.curriculum_state_dict() == saved
        # Exercise the actual registered termination with translated root poses.
        obs, _ = wrapped.reset()
        robot = base.scene['robot']
        pose = torch.cat([robot.data.root_pos_w, robot.data.root_quat_w], dim=-1).clone()
        pose[:, :2] = kb.anchor_xy
        pose[:, 0] += torch.tensor([.8, 1.19, 1.21, 1.3] * 4, device=args.device)
        robot.write_root_pose_to_sim(pose)
        term = cfg.terminations.walked_away
        boundary = term.func(base, **term.params)
        assert boundary.tolist() == [False, False, True, True] * 4, boundary
    # A resumed process creates a fresh runner. Reusing the inference runner
    # would retain inference-only normalizer tensors from the play check.
    runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    runner.load(str(out / 'course.pt'), load_optimizer=True)
    assert kb.curriculum_training and kb.curriculum_state_dict() == saved
    report = {'revision': REVISION, 'scratch_ppo_updates': 2, 'losses': losses,
              'constructed_spatial_sampling': sampling, 'checkpoint_play_freeze_and_resume': True,
              'three_metre_six_m_s_incoming_first_step_active': True,
              'registered_travel_boundary_checked': True,
              'v2_env_and_runner_unchanged_except_startup_travel_and_log_name': True,
              'does_not_establish_learned_wide_interception': True}
    (out / 'smoke.json').write_text(json.dumps(report, indent=2) + '\n')
    print('V3_SMOKE_PASS', json.dumps(report), flush=True)


try:
    main()
except BaseException:
    import traceback, sys, os
    traceback.print_exc(); sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
finally:
    if env is not None:
        env.close()
    app.close(wait_for_replicator=False)
