"""Small real-IsaacLab regression: FK provenance, contact filtering, reset, PPO, resume."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
app = launcher.app
test_env = None

import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import quat_apply
from perceptual_ball.tasks.manager_based.perceptual_ball.soccer_v3_env_cfg import SoccerV3EnvCfg, ROBOT_CONTACT_LINKS
from perceptual_ball.tasks.manager_based.perceptual_ball.agents.rsl_rl_ppo_cfg import SoccerV3PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.amp import KICK_MOTION_CLIP_PATHS, END_EFFECTOR_BODY_NAMES
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy


def main():
    global test_env
    torch.set_num_threads(2)
    out = Path("docs/research/iros2027/validation")
    (out / "smoke_v3.json").unlink(missing_ok=True)
    cfg = SoccerV3EnvCfg()
    cfg.scene.num_envs = 2
    cfg.sim.device = args.device
    cfg.seed = 42
    env = gym.make("Template-Perceptual-Ball-Soccer-v3", cfg=cfg)
    test_env = env
    base = env.unwrapped
    wrapper = RslRlVecEnvWrapper(env, clip_actions=10.)
    robot = base.scene["robot"]
    body_ids, body_names = robot.find_bodies(END_EFFECTOR_BODY_NAMES, preserve_order=True)
    assert body_names == END_EFFECTOR_BODY_NAMES
    obs, _ = wrapper.reset()
    assert obs["amp"].shape == (2, 600) and obs["perception"].shape == (2, 8, 27, 48)
    assert obs["target"].shape == (2, 2) and obs["timing"].shape == (2, 2)
    term = base.action_manager.get_term("joint_pos")
    torch.testing.assert_close(term._offset, robot.data.default_joint_pos[:, term._joint_ids])
    fk_errors = {}
    for path in KICK_MOTION_CLIP_PATHS:
        clip = torch.load(path, weights_only=False, map_location=base.device)
        assert clip["joint_names"] == robot.joint_names
        frame = min(100, len(clip["base_position"]) - 1)
        pos = clip["base_position"][frame].repeat(2, 1) + base.scene.env_origins
        quat = clip["base_quat"][frame].repeat(2, 1)
        robot.write_root_pose_to_sim(torch.cat((pos, quat), -1))
        robot.write_root_velocity_to_sim(torch.zeros(2, 6, device=base.device))
        q = clip["joint_position"][frame].repeat(2, 1)
        robot.write_joint_state_to_sim(q, torch.zeros_like(q))
        base.scene.write_data_to_sim()
        base.sim.forward()
        base.scene.update(base.physics_dt)
        expected = clip["link_position"][frame][None] + base.scene.env_origins[:, None]
        error = (robot.data.body_link_pos_w[:, body_ids] - expected).abs().max().item()
        fk_errors[Path(path).name] = error
        assert error < 0.003, f"AMP end-effector order/FK mismatch: {path}: {error}"
    wrapper.reset()
    # Reset writes root/joints; refresh FK before choosing a world-space contact fixture.
    base.sim.forward()
    base.scene.update(base.physics_dt)
    zero = torch.zeros(2, 29, device=base.device)
    # Place a ball at the toe surface for a genuine filtered contact.
    ball = base.scene["ball"]
    foot_id = base._kickball.foot_body_ids[0]
    foot = robot.data.body_link_pos_w[:, foot_id].clone()
    pose = torch.zeros(2, 7, device=base.device)
    # Actual collision mesh: toe x <= .1424 m, upper toe z ~= -.0077 m.
    # Touch the toe, away from ankle/shin and the opposite foot.
    pose[:, :3] = foot + quat_apply(robot.data.body_link_quat_w[:, foot_id],
                                    torch.tensor([[.20, 0., .065]], device=base.device).repeat(2, 1))
    pose[:, 3] = 1.
    ball.write_root_pose_to_sim(pose)
    drop_velocity = torch.zeros(2, 6, device=base.device)
    drop_velocity[:, 0] = 0.3  # Keep the served ball live until it reaches the foot.
    ball.write_root_velocity_to_sim(drop_velocity)
    base._kickball.previous_ball_xy.copy_(pose[:, :2])
    peak_contact = 0.
    contacts_before = base._kickball.counts["contact"]
    import omni.usd
    from pxr import UsdPhysics
    collision_links = {str(p.GetPath()).split("/")[5] for p in omni.usd.get_context().get_stage().Traverse()
                       if str(p.GetPath()).startswith("/World/envs/env_0/Robot/") and p.HasAPI(UsdPhysics.CollisionAPI)}
    assert collision_links == set(ROBOT_CONTACT_LINKS), "Update explicit filters after a G1 asset change"
    for step in range(15):
        obs, reward, done, extras = wrapper.step(zero)
        force = base.scene["left_ball_contact"].data.force_matrix_w_history
        assert force.shape == (2, 4, 1, 1, 3), force.shape
        assert base.scene["ball_robot_contact"].data.force_matrix_w_history.shape == (2, 4, 1, len(ROBOT_CONTACT_LINKS), 3)
        peak_contact = max(peak_contact, force.norm(dim=-1).max().item())
        if step == 0:
            columns = base.scene["ball_robot_contact"].data.force_matrix_w_history[:, :, 0]
            print("contact_columns", [(name, columns[:, :, j].norm(dim=-1).max().item())
                  for j, name in enumerate(ROBOT_CONTACT_LINKS)], flush=True)
        print("contact_probe", step, "phase", base._kickball.phase.tolist(),
              "force", force.norm(dim=-1).amax(dim=(1, 2, 3)).tolist(),
              "ball_speed", ball.data.root_lin_vel_w[:, :2].norm(dim=-1).tolist(),
              "done", done.tolist(), "counts", base._kickball.counts, flush=True)
    assert peak_contact > .5, "Real foot-ball contact filter returned no contact"
    assert base._kickball.counts["contact"] > contacts_before, "Physical foot contact did not enter RECOVER"

    agent = SoccerV3PPORunnerCfg()
    agent.device = args.device
    agent.num_steps_per_env = 4
    agent.algorithm.num_learning_epochs = 1
    agent.algorithm.num_mini_batches = 1
    runner = BallRegressionOnPolicyRunner(wrapper, agent.to_dict(), log_dir=None, device=args.device)
    obs = wrapper.get_observations()
    terminal_seen = False
    for i in range(4):
        if i == 2:
            base.episode_length_buf[0] = base.max_episode_length - 1
        with torch.inference_mode():
            actions = runner.alg.act(obs)
            obs, reward, done, extras = wrapper.step(actions)
            if done.any():
                terminal = extras["terminal_observations"]
                assert terminal["obs"]["amp"].shape[1] == 600
                assert torch.isfinite(terminal["obs"]["amp"]).all()
                terminal_seen = True
            runner.alg.process_env_step(obs, reward, done, extras)
    assert terminal_seen
    with torch.inference_mode():
        runner.alg.compute_returns(obs)
    losses = runner.alg.update()
    assert all(torch.isfinite(torch.tensor(value)) for value in losses.values())
    runner.save(str(out / "smoke_model.pt"))
    with torch.inference_mode():
        amp_before = runner.alg.amp.predict_reward(obs["amp"], obs["skill"].argmax(-1)).clone()
        runner.load(str(out / "smoke_model.pt"))
        torch.testing.assert_close(amp_before, runner.alg.amp.predict_reward(obs["amp"], obs["skill"].argmax(-1)))
    export_depth_policy(runner.alg.policy, obs, out / "exported", {"joint_names": robot.joint_names})
    result = {"task": "Template-Perceptual-Ball-Soccer-v3", "device": args.device,
              "num_envs": 2, "fk_max_errors_m": fk_errors, "peak_foot_ball_force_N": peak_contact,
              "valid_contact_routed": True,
              "terminal_snapshot_seen": terminal_seen, "update_losses": losses,
              "checkpoint_roundtrip": True, "complete_depth_export": True,
              "joint_effort_limits": robot.data.joint_effort_limits[0].cpu().tolist(),
              "joint_velocity_limits": robot.data.joint_vel_limits[0].cpu().tolist(),
              "metrics": base._kickball.metrics(), "not_a_performance_evaluation": True}
    (out / "smoke_v3.json").write_text(json.dumps(result, indent=2) + "\n")
    env.close()


try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    if test_env is not None:
        test_env.close()
    app.close(wait_for_replicator=False)
