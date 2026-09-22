"""Small real-IsaacLab check of v0 inheritance, incoming serves, and one PPO update."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
env = None

import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.perceptual_ball_env_cfg import PerceptualBallEnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_env_cfg import AgileKickballEnvCfg, AgileKickballPPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agents.rsl_rl_ppo_cfg import PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic


def main():
    global env
    torch.set_num_threads(2)
    out = Path("docs/agilekickball/validation")
    out.mkdir(parents=True, exist_ok=True)
    result_file = out / "smoke.json"
    result_file.unlink(missing_ok=True)
    cfg, original = AgileKickballEnvCfg(), PerceptualBallEnvCfg()
    # Exact comparison apart from the explicitly requested curriculum/reset changes.
    actual_cfg, v0_cfg = cfg.to_dict(), original.to_dict()
    actual_cfg.pop("curriculum")
    v0_cfg.pop("curriculum")
    actual_cfg["terminations"].pop("recovery_timeout")
    actual_cfg["events"]["setup_kickball_state"] = v0_cfg["events"]["setup_kickball_state"]
    assert actual_cfg["episode_length_s"] == 60.
    actual_cfg["episode_length_s"] = v0_cfg["episode_length_s"]
    assert actual_cfg == v0_cfg
    agent, original_agent = AgileKickballPPORunnerCfg(), PPORunnerCfg()
    actual_agent, v0_agent = agent.to_dict(), original_agent.to_dict()
    actual_agent.pop("experiment_name")
    v0_agent.pop("experiment_name")
    assert actual_agent == v0_agent
    cfg.scene.num_envs = 8
    cfg.sim.device = args.device
    cfg.seed = 42
    env = gym.make("Template-Perceptual-Ball-AgileKickball-v0", cfg=cfg)
    base = env.unwrapped
    wrapper = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    ids = torch.arange(base.num_envs, device=base.device)
    obs, _ = wrapper.reset()
    assert not base.scene.sensors, "AgileKickball must retain v0's sensor-free synthetic depth"
    assert obs["perception"].shape == (8, 8, 27, 48) and "target" not in obs
    assert not base._kickball.ball_active.any()
    zero = torch.zeros(8, 29, device=base.device)
    policy_cfg = agent.policy.to_dict()
    policy_cfg.pop("class_name")
    probe_policy = PerceptionActorCritic(obs, agent.obs_groups, 29, **policy_cfg).to(base.device).eval()
    probe_checkpoint = Path("logs/rsl_rl/g1_soccer_kick/2026-09-18_15-10-38/model_30800.pt")
    probe_policy.load_state_dict(torch.load(probe_checkpoint, map_location=base.device, weights_only=False)["model_state_dict"])

    def standing_action():
        # Existing v0 policy, inference only; this does not warm-start the new training run.
        with torch.inference_mode():
            return probe_policy.act_inference(wrapper.get_observations())

    def wait_for_serves():
        counts = base._kickball.serves.clone()
        speeds = torch.zeros(8, device=base.device)
        seen = torch.zeros(8, dtype=torch.bool, device=base.device)
        for index in range(150):
            data = base.scene["robot"].data
            before = {"height": data.root_pos_w[:, 2].tolist(),
                      "gravity": data.projected_gravity_b.tolist(),
                      "stable_s": base._kickball.stable_elapsed.tolist(),
                      "wait_s": base._kickball.wait_elapsed.tolist()}
            _, _, done, extras = wrapper.step(standing_action())
            assert not done.any(), ("Default stance should recover without an episode reset", index, before,
                                    {k: v for k, v in extras.get("log", {}).items() if "Termination" in k})
            new = (base._kickball.serves > counts) & ~seen
            speeds[new] = base.scene["ball"].data.root_lin_vel_w[new, :2].norm(dim=-1)
            assert not base._kickball.kick_success_flag[new].any(), "Teleport is not a kick"
            seen |= new
            if seen.all():
                return speeds
        raise AssertionError("Default standing recovery gate not reached within 3 seconds")

    measured = {}
    for step, upper in ((0, .8), (120000, 1.4), (240000, 2.)):
        base.common_step_counter = step
        before = base.scene["ball"].data.root_lin_vel_w.clone()
        base.curriculum_manager.compute(ids)
        torch.testing.assert_close(before, base.scene["ball"].data.root_lin_vel_w)
        wrapper.reset()  # Manager curriculum runs before reset's actual ball serve.
        speed = wait_for_serves()
        assert float(speed.min()) >= .4 - 1.e-5 and float(speed.max()) <= upper + 1.e-5
        assert abs(base._kickball.serve_speed_range[1] - upper) < 1.e-6
        measured[str(step)] = speed.tolist()
    assert max(measured["240000"]) > .8, "Final curriculum must actually produce faster balls"
    # End one ball, then require a second serve without resetting the episode/robot.
    before_episode_steps = base.episode_length_buf.clone()
    base.scene["ball"].write_root_velocity_to_sim(torch.zeros(8, 6, device=base.device))
    _, _, done, _ = wrapper.step(standing_action())
    assert not done.any() and not base._kickball.ball_active.any()
    wait_for_serves()
    assert (base.episode_length_buf > before_episode_steps).all()
    base.common_step_counter = 0
    obs, _ = wrapper.reset()
    agent.device = args.device
    agent.num_steps_per_env = 4
    agent.algorithm.num_learning_epochs = 1
    agent.algorithm.num_mini_batches = 1
    runner = BallRegressionOnPolicyRunner(wrapper, agent.to_dict(), log_dir=None, device=args.device)
    with torch.inference_mode():
        for step in range(4):
            if step == 2:
                base.episode_length_buf[0] = base.max_episode_length - 1
            action = runner.alg.act(obs)
            obs, reward, done, extras = wrapper.step(action)
            runner.alg.process_env_step(obs, reward, done, extras)
        runner.alg.compute_returns(obs)
    losses = runner.alg.update()
    assert all(torch.isfinite(torch.tensor(v)) for v in losses.values())
    runner.save(str(out / "smoke_model.pt"))
    with torch.inference_mode():
        runner.load(str(out / "smoke_model.pt"))
    result_file.write_text(json.dumps({"task": "Template-Perceptual-Ball-AgileKickball-v0",
        "num_envs": 8, "device": args.device, "v0_config_preserved_except_reset_curriculum": True,
        "same_episode_second_serve": True, "gate_reachable_with_existing_v0_policy": True,
        "probe_checkpoint": str(probe_checkpoint),
        "measured_serve_speeds_m_s": measured, "update_losses": losses,
        "checkpoint_roundtrip": True, "not_a_performance_evaluation": True}, indent=2) + "\n")


try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    if env is not None:
        env.close()
    app.close(wait_for_replicator=False)
