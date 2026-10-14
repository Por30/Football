"""Bounded CPU physics, new-policy PPO, serve geometry and checkpoint checks."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
env = None

import json
import copy
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
    out = Path('docs/agilekickball_v3/stability_fix_20261008')
    out.mkdir(parents=True, exist_ok=True)
    cfg, agent = AgileKickballV3EnvCfg(), AgileKickballV3PPORunnerCfg()
    old, oldagent = AgileKickballV2EnvCfg(), AgileKickballV2PPORunnerCfg()
    assert old.terminations.walked_away.params['max_dist'] == .6
    assert cfg.terminations.walked_away.params['max_dist'] == .6
    olddict, newdict = old.to_dict(), cfg.to_dict()
    for item in (olddict, newdict):
        item['events'].pop('setup_kickball_state')
    assert olddict == newdict, 'Only the versioned startup event may differ from v2'
    oldrunner, newrunner = oldagent.to_dict(), agent.to_dict()
    oldrunner.pop('experiment_name'); newrunner.pop('experiment_name')
    assert newrunner['policy'].pop('class_name') == 'StateFeedbackActorCritic'
    assert oldrunner['policy'].pop('class_name') == 'PerceptionActorCritic'
    assert newrunner['algorithm'].pop('class_name') == 'StateFeedbackPPO'
    assert oldrunner['algorithm'].pop('class_name') == 'BallRegressionPPO'
    expected_policy = dict(feedback_logstd_min=-2., feedback_logstd_max=1.,
                           feedback_smooth_std=True, feedback_residual_limit=.1)
    for key, value in expected_policy.items():
        assert newrunner['policy'].pop(key) == value
    assert newrunner['algorithm'].pop('ball_aux_update_encoder') is False
    assert newrunner['algorithm'].pop('ball_aux_coef') == .5
    assert newrunner['algorithm'].pop('ball_aux_max_kl') == .001
    assert newrunner['algorithm']['ball_aux_lr'] == .0001
    assert oldrunner['algorithm']['ball_aux_lr'] == .001
    newrunner['algorithm']['ball_aux_lr'] = oldrunner['algorithm']['ball_aux_lr']
    assert newrunner['algorithm']['learning_rate'] == 1.e-5
    assert oldrunner['algorithm']['learning_rate'] == .001
    newrunner['algorithm']['learning_rate'] = oldrunner['algorithm']['learning_rate']
    assert oldrunner == newrunner
    cfg.scene.num_envs = 16
    cfg.sim.device = args.device
    cfg.seed = 42
    agent.num_steps_per_env = 24
    agent.algorithm.num_learning_epochs = 1
    agent.algorithm.num_mini_batches = 1
    env = gym.make('Template-Perceptual-Ball-AgileKickball-v3', cfg=cfg)
    base = env.unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    kb = base._kickball
    runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    with torch.inference_mode():
        obs, _ = wrapped.reset()
        assert kb.ball_active.all() and kb.serve_distance_range == (1.3, 2.)
        assert kb.serve_speed_range == (.4, 1.1)
    baseline_path = 'logs/rsl_rl/agilekickball_v2/2026-09-25_22-18-55_v1_speed_only_20260925_scratch/model_49999.pt'
    runner.warm_start_from_v2(baseline_path)
    from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic
    baseline_cfg = oldagent.policy.to_dict();baseline_cfg.pop('class_name')
    baseline_policy = PerceptionActorCritic(obs, oldagent.obs_groups, 29, **baseline_cfg).to(args.device)
    baseline = torch.load(baseline_path, map_location=args.device, weights_only=False)
    baseline_policy.load_state_dict(baseline['model_state_dict'])
    with torch.no_grad():
        torch.testing.assert_close(runner.alg.policy.act_inference(obs), baseline_policy.act_inference(obs), rtol=0, atol=0)
        torch.testing.assert_close(runner.alg.policy.evaluate(obs), baseline_policy.evaluate(obs), rtol=0, atol=0)
    for key, value in runner.alg.amp.state_dict().items():
        torch.testing.assert_close(value, baseline['amp_state_dict'][key], rtol=0, atol=0)
    assert not runner.alg.optimizer.state and not runner.alg.ball_aux_optimizer.state and not runner.alg.amp_optimizer.state
    recovery_checks = {}
    def check_recovery(label):
        with torch.inference_mode():
            kb.serve_speed_override = (.4, 1.1)
            kb._sync_course()
            torch.manual_seed(4208)
            current, _ = wrapped.reset()
            before = kb.metrics()
            terminations = {key: 0 for key in base.termination_manager.active_terms}
            for _ in range(1000):
                current, _, dones, _ = wrapped.step(runner.alg.policy.act(current))
                for key in terminations:
                    terminations[key] += int((base.termination_manager.get_term(key) & dones.bool()).sum())
            after = kb.metrics()
            recovered = after['AgileKickball/recovered_serves'] - before['AgileKickball/recovered_serves']
            assert recovered > 0, (label, recovered, terminations)
            recovery_checks[label] = dict(num_envs=16, steps=1000, recovered_serves=recovered,
                                          fresh_termination_counts=terminations)
            kb.serve_speed_override = None
            kb._sync_course()
            return wrapped.reset()[0]
    obs = check_recovery('v2_initialized_before_training')
    losses = []
    for _ in range(2):
        with torch.inference_mode():
            for _ in range(agent.num_steps_per_env):
                actions = runner.alg.act(obs)
                obs, rewards, dones, infos = wrapped.step(actions)
                runner.alg.process_env_step(obs, rewards, dones, infos)
            runner.alg.compute_returns(obs)
        result = runner.alg.update()
        assert all(torch.isfinite(torch.tensor(v)) for v in result.values()), result
        assert 'state_feedback/nll' in result
        assert result['aux/predictor_updates'] > 0, result
        assert result['aux/encoder_updates'] == 0, result
        assert result['aux/stage_monitor_kl'] <= runner.alg.ball_aux_max_kl
        losses.append(result)
    assert sum(row['ball/incoming/count'] for row in losses) > 0
    sampling = []
    with torch.inference_mode():
        for exposure, expected_high, expected_width in [(0., .7, .25), (30000., 1.35, .25), (60000., 2., .25)]:
            state = kb.curriculum_state_dict()
            state.update(exposure_steps=exposure, extension_unlocked=False,
                         extension_steps=0., advance_rate=0.)
            kb.load_curriculum_state_dict(state)
            obs, _ = wrapped.reset()
            assert abs(kb.serve_distance_range[1] - expected_high) < 1e-6
            # V2 uses the sampler's fixed default; only legacy v3 has an override.
            assert getattr(kb, 'serve_aim_offset_range', (-.25, .25)) == (-expected_width, expected_width)
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
        saved_optimizer = copy.deepcopy(runner.alg.ball_aux_optimizer.state_dict())
        saved_updates = runner.alg.state_feedback_updates
        saved = kb.curriculum_state_dict()
        runner.load(str(out / 'course.pt'), load_optimizer=False)
        obs, _ = wrapped.reset()
        for _ in range(24):
            obs, _, _, _ = wrapped.step(runner.alg.policy.act_inference(obs))
        assert kb.curriculum_state_dict() == saved
        assert kb.serve_distance_range == (1.3, 2.)
        # Maximum-range, maximum-speed initial balls must survive the first tick.
        kb.serve_speed_override = (6., 6.)
        kb._sync_course()
        obs, _ = wrapped.reset()
        kb.serve_distance_range = (2., 2.)
        kb.reset(torch.arange(16, device=args.device))
        dist = (kb.ball.data.root_pos_w[:, :2] - kb.anchor_xy).norm(dim=-1)
        torch.testing.assert_close(dist, torch.full_like(dist, 2.), atol=2e-5, rtol=0)
        speed = kb.ball.data.root_lin_vel_w[:, :2].norm(dim=-1)
        torch.testing.assert_close(speed, torch.full_like(speed, 6.), atol=1e-5, rtol=0)
        wrapped.step(torch.zeros(16, base.action_manager.total_action_dim, device=args.device))
        assert kb.ball_active.all(), 'A 2m incoming serve must not immediately end'
        kb._sync_course()
        assert kb.curriculum_state_dict() == saved
        # Exercise the actual registered termination with translated root poses.
        obs, _ = wrapped.reset()
        robot = base.scene['robot']
        pose = torch.cat([robot.data.root_pos_w, robot.data.root_quat_w], dim=-1).clone()
        pose[:, :2] = kb.anchor_xy
        pose[:, 0] += torch.tensor([.4, .59, .61, .8] * 4, device=args.device)
        robot.write_root_pose_to_sim(pose)
        term = cfg.terminations.walked_away
        boundary = term.func(base, **term.params)
        assert boundary.tolist() == [False, False, True, True] * 4, boundary
    # A resumed process creates a fresh runner. Reusing the inference runner
    # would retain inference-only normalizer tensors from the play check.
    runner = BallRegressionOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    runner.load(str(out / 'course.pt'), load_optimizer=True)
    assert kb.curriculum_training and kb.curriculum_state_dict() == saved
    assert runner.alg.state_feedback_updates == saved_updates
    loaded_optimizer = runner.alg.ball_aux_optimizer.state_dict()
    assert loaded_optimizer['param_groups'] == saved_optimizer['param_groups']
    for pid, values in saved_optimizer['state'].items():
        for key, value in values.items():
            torch.testing.assert_close(loaded_optimizer['state'][pid][key], value, rtol=0, atol=0)
    # Verify the resumed algorithm can continue actual physics + backpropagation.
    with torch.inference_mode():
        obs, _ = wrapped.reset()
        for _ in range(agent.num_steps_per_env):
            actions = runner.alg.act(obs)
            obs, rewards, dones, infos = wrapped.step(actions)
            runner.alg.process_env_step(obs, rewards, dones, infos)
        runner.alg.compute_returns(obs)
    resumed_losses = runner.alg.update()
    assert all(torch.isfinite(torch.tensor(v)) for v in resumed_losses.values())
    assert resumed_losses['aux/predictor_updates'] > 0
    assert resumed_losses['aux/encoder_updates'] == 0
    assert runner.alg.state_feedback_updates > saved_updates
    assert losses[-1]['state_feedback/residual_abs_mean_raw'] > 0
    check_recovery('after_updates_and_optimizer_resume')
    # Keep the completed old outcome model readable under its archived task.
    from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v3_outcome import AgileKickballV3State as LegacyState
    from perceptual_ball.rsl_rl_extensions.contact_outcome import OutcomeActorCritic
    legacy_path = Path('logs/rsl_rl/agilekickball_v3/2026-10-03_23-56-27_contact_outcome_20261003_scratch/model_49999.pt')
    legacy = torch.load(legacy_path, map_location=args.device, weights_only=False)
    LegacyState(base).validate_curriculum_state_dict(legacy['agile_v3_wide_serve_curriculum'])
    legacy_policy_cfg = oldagent.policy.to_dict()
    legacy_policy_cfg.pop('class_name')
    legacy_policy = OutcomeActorCritic(obs, oldagent.obs_groups, base.action_manager.total_action_dim, **legacy_policy_cfg).to(args.device)
    legacy_policy.load_state_dict(legacy['model_state_dict'])
    with torch.no_grad():
        assert torch.isfinite(legacy_policy.act_inference(obs)).all()
    assert 'agilekickball_v3_outcome_env_cfg' in gym.spec('Template-Perceptual-Ball-AgileKickball-v3-Outcome').kwargs['env_cfg_entry_point']
    from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v3_feedback_legacy_env_cfg import AgileKickballV3PPORunnerCfg as FailedRunnerCfg
    from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.agilekickball_v3_feedback_legacy import AgileKickballV3State as FailedState
    failed = torch.load('logs/rsl_rl/agilekickball_v3/2026-10-06_13-17-10_state_feedback_20261006_scratch/model_49999.pt', map_location=args.device, weights_only=False)
    failed_runner = BallRegressionOnPolicyRunner(wrapped, FailedRunnerCfg().to_dict(), log_dir=None, device=args.device)
    assert failed_runner.alg.state_feedback_config == failed['state_feedback']['config']
    FailedState(base).validate_curriculum_state_dict(failed['agile_v3_state_feedback_curriculum'])
    failed_runner.alg.policy.load_state_dict(failed['model_state_dict'])
    with torch.no_grad():assert torch.isfinite(failed_runner.alg.policy.act_inference(obs)).all()
    assert 'feedback_legacy' in gym.spec('Template-Perceptual-Ball-AgileKickball-v3-StateFeedback-20261006').kwargs['env_cfg_entry_point']
    report = {'revision': REVISION, 'v2_initialized_ppo_updates': 2, 'physical_recovery': recovery_checks, 'losses': losses,
              'resumed_ppo_updates': 1, 'resumed_losses': resumed_losses,
              'constructed_spatial_sampling': sampling, 'checkpoint_play_freeze_and_resume': True,
              'two_metre_six_m_s_incoming_first_step_active': True,
              'registered_travel_boundary_checked': True,
              'v2_physical_task_identical': True,
              'state_feedback_optimizer_restored_exactly': True, 'v2_warm_start_exact_outputs_and_amp': True,
              'legacy_final_checkpoint_loaded': True,
              'does_not_establish_learned_performance': True}
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
