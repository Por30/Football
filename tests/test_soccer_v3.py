"""CPU regressions using production math/algorithms and explicit simulator-boundary doubles."""
import copy
import importlib.util
import io
import contextlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import torch
from tensordict import TensorDict

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "source/perceptual_ball/perceptual_ball"
TASK = PKG / "tasks/manager_based/perceptual_ball"
torch.set_num_threads(1)


def package(name, path=None):
    module = types.ModuleType(name)
    module.__path__ = [str(path)] if path else []
    sys.modules[name] = module
    return module


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


# Only Isaac Sim boundary classes are doubled; math and all project logic are actual modules.
package("omni")
sys.modules["omni.log"] = types.ModuleType("omni.log")
package("isaaclab")
package("isaaclab.utils")
math = module("isaaclab.utils.math", Path("/home/cao/IsaacLab/source/isaaclab/isaaclab/utils/math.py"))
assets = package("isaaclab.assets")
assets.Articulation = assets.RigidObject = object
managers = package("isaaclab.managers")


class Entity:
    def __init__(self, name, body_names=None, **kwargs):
        self.name, self.body_names = name, body_names
        self.body_ids = list(range(5))

    def resolve(self, scene):
        self.body_ids = [0 if "left" in self.body_names[0] else 1]


class Term:
    def __init__(self, cfg, env):
        self._env = env


managers.SceneEntityCfg, managers.ManagerTermBase = Entity, Term
envs = package("isaaclab.envs")
envs.ManagerBasedRLEnv = type("ManagerBasedRLEnv", (), {"_reset_idx": lambda self, ids: None})
package("perceptual_ball", PKG)
package("perceptual_ball.rsl_rl_extensions", PKG / "rsl_rl_extensions")
package("perceptual_ball.tasks", PKG / "tasks")
package("perceptual_ball.tasks.manager_based", PKG / "tasks/manager_based")
TNAME = "perceptual_ball.tasks.manager_based.perceptual_ball"
package(TNAME, TASK)
package(TNAME + ".mdp", TASK / "mdp")
from perceptual_ball.amp_features import pack_amp_frame
from perceptual_ball.rsl_rl_extensions.modules import PerceptionActorCritic
from perceptual_ball.rsl_rl_extensions.algorithm import SkillAMPPPO
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.amp import MotionLibrary, KICK_MOTION_CLIP_PATHS, amp_features
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.soccer_v3 import SoccerV3State, PREPARE, RECOVER
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.depth_v3 import TimedDepth
from perceptual_ball.tasks.manager_based.perceptual_ball.soccer_env import SoccerEnv


def observations(n=4):
    return TensorDict({"proprio_hist": torch.randn(n, 864) * .05,
                       "perception": torch.rand(n, 8, 27, 48), "proprio": torch.randn(n, 108) * .05,
                       "robot_vel": torch.zeros(n, 3), "privileged": torch.randn(n, 6) * .1,
                       "amp": torch.randn(n, 600) * .1, "target": torch.tensor([[1., 0.]]).repeat(n, 1),
                       "timing": torch.tensor([[.04, 1.]]).repeat(n, 1),
                       "skill": torch.eye(2).repeat((n + 1) // 2, 1)[:n]}, batch_size=[n])


def make_algorithm(n=4):
    obs = observations(n)
    with contextlib.redirect_stdout(io.StringIO()):
        policy = PerceptionActorCritic(obs, {
            "policy": ["proprio_hist", "perception", "target", "timing"],
            "critic": ["proprio", "robot_vel", "target", "privileged"]}, 29,
            actor_hidden_dims=(32,), critic_hidden_dims=(32,), num_critics=2,
            critic_obs_normalization=False, depth_use_frame_diff=True, ball_aux_fuse_proprio=True,
            ball_head_hidden_dim=16)
    lib = MotionLibrary(KICK_MOTION_CLIP_PATHS, "cpu")
    alg = SkillAMPPPO(policy, motion_library=lib, device="cpu", num_learning_epochs=1,
                      num_mini_batches=1, ball_aux_coef=1., amp_coef=.3)
    alg.init_storage("rl", n, 2, obs, [29])
    return alg, obs


class Sensor:
    def __init__(self, n):
        self.data = NS(force_matrix_w_history=torch.zeros(n, 4, 1, 1, 3),
                       force_matrix_w=torch.zeros(n, 1, 1, 3),
                       net_forces_w=torch.tensor([[[0., 0., 100.]]]).repeat(n, 1, 1))

    def reset(self, ids):
        self.data.force_matrix_w_history[ids] = 0
        self.data.force_matrix_w[ids] = 0


def state_fixture(n=2):
    clip = torch.load(KICK_MOTION_CLIP_PATHS[0], weights_only=False)
    robot = NS(joint_names=clip["joint_names"], data=NS(
        root_pos_w=torch.tensor([[0., 0., .8]]).repeat(n, 1),
        root_quat_w=torch.tensor([[1., 0., 0., 0.]]).repeat(n, 1),
        root_lin_vel_w=torch.zeros(n, 3), root_ang_vel_b=torch.zeros(n, 3),
        projected_gravity_b=torch.tensor([[0., 0., -1.]]).repeat(n, 1),
        joint_vel=torch.zeros(n, 29), body_link_pos_w=torch.zeros(n, 2, 3)))
    ball = NS(data=NS(root_pos_w=torch.zeros(n, 3), root_lin_vel_w=torch.zeros(n, 3)))
    ball.write_root_pose_to_sim = lambda p, ids: ball.data.root_pos_w.__setitem__(ids, p[:, :3])
    ball.write_root_velocity_to_sim = lambda v, ids: ball.data.root_lin_vel_w.__setitem__(ids, v[:, :3])

    class Scene(dict):
        env_origins = torch.zeros(n, 3)

    scene = Scene(robot=robot, ball=ball, left_ball_contact=Sensor(n), right_ball_contact=Sensor(n), ball_robot_contact=Sensor(n))
    env = NS(scene=scene, num_envs=n, device="cpu", step_dt=.02, common_step_counter=0,
             cfg=NS(decimation=4), reset_buf=torch.zeros(n, dtype=torch.bool))
    state = SoccerV3State(env, Entity("robot"), Entity("ball"))
    env._kickball = state
    state.reset(torch.arange(n))
    state.target_direction[:] = torch.tensor([1., 0.])
    return env, state


class SoccerTests(unittest.TestCase):
    def test_all_motion_feature_dimensions_match(self):
        lib = MotionLibrary(KICK_MOTION_CLIP_PATHS, "cpu")
        clips = [torch.load(p, weights_only=False) for p in KICK_MOTION_CLIP_PATHS]
        ee = torch.cat([c["link_position"] for c in clips])
        robot = NS(data=NS(root_pos_w=lib.base_position, root_quat_w=lib.base_quat,
                          body_link_pos_w=ee, joint_pos=lib.joint_position,
                          root_lin_vel_b=lib.base_lin_vel_b, root_ang_vel_b=lib.base_ang_vel_b))
        env = NS(scene={"robot": robot}, num_envs=len(ee), device="cpu")
        actual = amp_features(env, Entity("robot"), Entity("robot"), Entity("ball"))
        expected = pack_amp_frame(lib.base_height, lib.joint_position, lib.ee_pos_b,
                                  lib.base_lin_vel_b, lib.base_ang_vel_b, lib.root_rot_6d)
        torch.testing.assert_close(actual, expected)
        self.assertEqual(actual.shape[1], 60)
        self.assertGreater(actual[:, 0].min().item(), .6)
        torch.testing.assert_close(math.quat_apply_inverse(lib.base_quat, lib.base_ang_vel_w), lib.base_ang_vel_b)

    def test_state_contact_target_recovery_and_denominator(self):
        env, state = state_fixture()
        # First physical foot contact is at substep 3, not only the final substep.
        env.scene["left_ball_contact"].data.force_matrix_w_history[0, 2, 0, 0, 0] = 10
        env.scene["ball_robot_contact"].data.force_matrix_w_history[0, 2, 0, 0, 0] = -10
        env.scene["ball"].data.root_pos_w[0] = torch.tensor([.3, 0., .11])
        env.scene["ball"].data.root_lin_vel_w[0] = torch.tensor([2., 0., 0.])
        state.tick()
        self.assertEqual(state.phase[0], RECOVER)
        self.assertTrue(state.kick_success_flag[0])
        self.assertEqual(state.counts["contact"], 1)
        state.tick()
        self.assertEqual(state.counts["contact"], 1)  # double read same tick
        for sensor in state.foot_sensors + [state.ball_sensor]:
            sensor.reset(torch.tensor([0]))
        for _ in range(20):
            env.common_step_counter += 1
            env.scene["ball"].data.root_pos_w[0, 0] += .1
            state.tick()
        self.assertEqual(state.counts["success"], 1)
        self.assertEqual(state.counts["served"], 2)
        state.reset(torch.tensor([1]))
        self.assertEqual(state.counts["terminated"], 1)
        self.assertEqual(state.counts["served"], state.counts["settled"] + int(state.open_serve.sum()))

    def test_body_rebound_high_foot_and_fall_fail(self):
        env, state = state_fixture()
        env.scene["robot"].data.body_link_pos_w[:, :, 2] = 1.
        env.scene["ball"].data.root_lin_vel_w[:] = torch.tensor([1., 0., 0.])
        env.scene["ball_robot_contact"].data.force_matrix_w_history[0, 0, 0, 0, 0] = 10.
        state.tick()
        self.assertEqual(state.counts["nonfoot"], 1)
        self.assertFalse(state.kick_success_flag.any())
        self.assertEqual(float(state.ball_return_speed.max()), 0.)
        env.reset_buf[1] = True
        env.common_step_counter += 1
        state.tick()
        state.reset(torch.tensor([1]))
        self.assertEqual(state.counts["terminated"], 1)
        self.assertEqual(state.counts["success"], 0)

    def test_terminal_reward_timeout_and_action_skill(self):
        alg, obs = make_algorithm()
        alg.act(obs)
        captured = {}
        def reward(x, skills):
            captured["x"], captured["skills"] = x.clone(), skills.clone()
            return x[:, 0]
        alg.amp.predict_reward = reward
        returned = obs.clone()
        returned["amp"][:] = .9
        returned["skill"][:] = torch.flip(obs["skill"], [-1])
        terminal = {g: v[[0, 1]].clone() for g, v in obs.items()}
        terminal["amp"][:] = .2
        alg.policy.evaluate = lambda x: torch.full((len(x["proprio"]), 1), 5.)
        alg.process_env_step(returned, torch.zeros(4), torch.tensor([1, 1, 0, 0]), {
            "terminal_observations": {"env_ids": torch.tensor([0, 1]), "obs": terminal},
            "time_outs": torch.tensor([1, 0, 0, 0])})
        torch.testing.assert_close(captured["x"][:, 0], torch.tensor([.2, .2, .9, .9]))
        torch.testing.assert_close(captured["skills"], obs["skill"].argmax(-1))
        torch.testing.assert_close(alg.storage.rewards[0, :, 0], torch.tensor([.03 + .99 * 5, .03, .135, .135]))

    def test_repeated_contact_timeout_and_missed_target(self):
        env, state = state_fixture(3)
        ids = torch.arange(3)
        env.scene["left_ball_contact"].data.force_matrix_w_history[:, 0, 0, 0, 0] = 10
        env.scene["ball_robot_contact"].data.force_matrix_w_history[:, 0, 0, 0, 0] = -10
        env.scene["ball"].data.root_pos_w[:] = torch.tensor([.3, 0., .11])
        env.scene["ball"].data.root_lin_vel_w[:] = torch.tensor([2., 0., 0.])
        state.tick()
        for sensor in state.foot_sensors + [state.ball_sensor]:
            sensor.reset(ids)
        env.common_step_counter += 1
        state.tick()
        env.scene["left_ball_contact"].data.force_matrix_w_history[0, 0, 0, 0, 0] = 10
        env.scene["ball_robot_contact"].data.force_matrix_w_history[0, 0, 0, 0, 0] = -10
        state.elapsed[1] = state.recovery_timeout
        env.scene["ball"].data.root_pos_w[2] = torch.tensor([2.1, 2., .11])
        env.common_step_counter += 1
        state.tick()
        self.assertEqual([state.counts[k] for k in ("multi_touch", "recovery_timeout", "bad_return")], [1, 1, 1])
        self.assertEqual(state.counts["success"], 0)
        self.assertEqual(state.counts["settled"], 3)
        self.assertTrue(state.round_failure.all())

    def test_contact_and_fall_same_tick_is_failure(self):
        env, state = state_fixture()
        env.reset_buf[0] = True
        env.scene["left_ball_contact"].data.force_matrix_w_history[0, 0, 0, 0, 0] = 10
        env.scene["ball_robot_contact"].data.force_matrix_w_history[0, 0, 0, 0, 0] = -10
        state.tick()
        self.assertEqual(state.counts["terminated"], 1)
        self.assertEqual(state.counts["contact"], 0)
        self.assertFalse(state.kick_success_flag.any())

    def test_terminal_history_snapshot_does_not_advance(self):
        env = SoccerEnv.__new__(SoccerEnv)
        env._inside_step = True
        history = torch.arange(1200.).reshape(2, 600)
        frame = torch.full((2, 60), -7.)
        term = NS(func=lambda env, **kwargs: frame, params={})
        def group(name):
            return history.clone() if name == "amp" else torch.zeros(2, 3)
        env.observation_manager = NS(compute_group=group, active_terms={}, _group_obs_term_cfgs={"amp": [term]})
        env._reset_idx(torch.tensor([0]))
        terminal = env._terminal_snapshot["obs"]["amp"]
        torch.testing.assert_close(terminal[:, -60:], frame[:1])
        torch.testing.assert_close(terminal[:, :-60], history[:1, 60:])
        torch.testing.assert_close(history, torch.arange(1200.).reshape(2, 600))

    def test_update_checkpoint_and_full_export(self):
        alg, obs = make_algorithm()
        for _ in range(2):
            alg.act(obs)
            alg.process_env_step(obs, torch.zeros(4), torch.zeros(4), {})
        alg.compute_returns(obs)
        losses = alg.update()
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in losses.values()))
        def runner(algorithm):
            value = BallRegressionOnPolicyRunner.__new__(BallRegressionOnPolicyRunner)
            value.alg, value.device, value.current_learning_iteration = algorithm, "cpu", 7
            value.logger_type, value.disable_logs = "tensorboard", True
            return value
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "model.pt"
            runner(alg).save(str(p))
            restored, _ = make_algorithm()
            runner(restored).load(str(p))
            for a, b in zip(alg.amp.state_dict().values(), restored.amp.state_dict().values()):
                torch.testing.assert_close(a, b)
            self.assertEqual(len(restored.amp_optimizer.state), len(alg.amp_optimizer.state))
            self.assertEqual(len(restored.ball_aux_optimizer.state), len(alg.ball_aux_optimizer.state))
            torch.testing.assert_close(alg.policy.act_inference(obs), restored.policy.act_inference(obs))
            wrapper = export_depth_policy(alg.policy, obs, d)
            import onnxruntime as ort
            session = ort.InferenceSession(str(Path(d) / "policy.onnx"), providers=["CPUExecutionProvider"])
            jit = torch.jit.load(str(Path(d) / "policy.pt"))
            for n in (1, 4):
                inputs = obs[:n]
                flat = torch.cat([inputs[g] for g in ("proprio_hist", "target", "timing")], -1)
                depth = inputs["perception"]
                expected = alg.policy.act_inference(inputs)
                torch.testing.assert_close(jit(flat, depth), expected)
                actual = torch.tensor(session.run(None, {"flat": flat.numpy(), "depth": depth.numpy()})[0])
                torch.testing.assert_close(actual, expected, atol=1.e-5, rtol=1.e-4)
            saved = torch.load(p, weights_only=False)
            saved.pop("soccer_schema_version")
            torch.save(saved, p)
            with self.assertRaises(ValueError):
                runner(restored).load(str(p))

    def test_auxiliary_kl_guard_rolls_back(self):
        alg, obs = make_algorithm()
        for _ in range(2):
            alg.act(obs)
            alg.process_env_step(obs, torch.zeros(4), torch.zeros(4), {})
        alg.ball_aux_max_kl = 0.
        before = copy.deepcopy(alg.policy.state_dict())
        alg._update_ball_head()
        for name, value in alg.policy.state_dict().items():
            torch.testing.assert_close(value, before[name])

    def test_depth_delay_repeated_read_and_reset(self):
        # Isolate transport: source image = control step, no geometry/noise.
        depth = TimedDepth.__new__(TimedDepth)
        n = 2
        env = NS(num_envs=n, device="cpu", step_dt=.02, common_step_counter=0)
        depth.env, depth.period, depth.max_delay, depth.dropout, depth.far = env, 1, 2, 0., 3.
        depth.queue = torch.full((n, 3, 1, 1), 3.)
        depth.timestamps = torch.full((n, 3), -1.)
        depth.latest = torch.full((n, 1, 1), 3.)
        depth.latest_time = torch.full((n,), -1.)
        depth.delivered = depth.latest.clone()
        depth.age_valid = torch.zeros(n, 2)
        depth.delay = torch.tensor([0, 2])
        depth.done_step = torch.full((n,), -1)
        from unittest.mock import patch
        from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.perception import synthetic_ball_depth_image
        with patch.object(synthetic_ball_depth_image, "__call__", lambda self, env, *args, **kw: torch.full((n, 1, 1), float(env.common_step_counter))):
            for step in range(4):
                env.common_step_counter = step
                value = depth(env).clone()
                torch.testing.assert_close(depth(env), value)
                self.assertEqual(value[0].item(), step)
                if step >= 2:
                    self.assertEqual(value[1].item(), step - 2)
                    self.assertAlmostEqual(depth.age_valid[1, 0].item(), .04)
                else:
                    self.assertEqual(depth.age_valid[1, 1].item(), 0.)
            depth.reset(torch.tensor([1]))
            depth.delay[1] = 2
            depth(env)
            self.assertEqual(depth.age_valid[1, 1].item(), 0.)
            self.assertEqual(depth.delivered[1].item(), 3.)


if __name__ == "__main__":
    unittest.main()
