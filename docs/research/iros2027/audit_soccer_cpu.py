"""Reproduce review findings on CPU; this is not a simulation/performance test.

Extract selected production definitions with AST to avoid launching Isaac Sim.
Assertions document current defects and deliberately fail if those defects change.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace as NS

import torch

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "source/perceptual_ball/perceptual_ball"
MDP = PKG / "tasks/manager_based/perceptual_ball/mdp"
ISAAC = Path("/home/cao/IsaacLab/source")
torch.set_num_threads(1)
torch.manual_seed(42)
sources = {}


def source(path):
    sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return ast.parse(path.read_text())


def load_module(path, name):
    source(path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expression(node, namespace):
    return eval(compile(ast.Expression(node), "source-expression", "eval"), namespace)


def height_probe():
    tree = source(MDP / "amp.py")
    policy = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "amp_features")
    pexpr = next(n.value for n in policy.body if isinstance(n, ast.Assign) and
                 isinstance(n.targets[0], ast.Name) and n.targets[0].id == "base_height")
    lib = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MotionLibrary")
    eexpr = next(n.value for n in ast.walk(lib) if isinstance(n, ast.Assign) and
                 isinstance(n.targets[0], ast.Attribute) and n.targets[0].attr == "base_height")
    result = {}
    for path in sorted((PKG / "assets/motions/kick").glob("*.pt")):
        clip = torch.load(path, map_location="cpu", weights_only=False)
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        z = clip["base_position"]
        links = clip["link_position"]
        p = expression(pexpr, {"asset": NS(data=NS(root_pos_w=z)), "ee_pos_w": links})
        e = expression(eexpr, {"base_position": z, "link_position": links})
        assert p.max() < 0 and e.min() > 0.6
        result[path.name] = {"frames": len(z), "policy_range_m": [p.min().item(), p.max().item()],
                             "expert_range_m": [e.min().item(), e.max().item()]}
    return result


def identity_quat_inverse(q, v):
    # This fixture tests only identity-orientation states; reject other inputs.
    expected = torch.zeros_like(q)
    expected[:, 0] = 1
    assert torch.equal(q, expected)
    return v.clone()


def state_probe():
    tree = source(MDP / "kickball_state.py")
    body = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    body += [n for n in tree.body if isinstance(n, ast.Assign) or
             isinstance(n, (ast.ClassDef, ast.FunctionDef)) and
             n.name in {"KickballState", "_rand_range", "_yaw_from_quat"}]
    namespace = {"torch": torch, "quat_apply_inverse": identity_quat_inverse}
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), "kickball-source", "exec"), namespace)
    cls = namespace["KickballState"]

    def fixture(feet):
        kb = cls.__new__(cls)
        kb.robot = NS(data=NS(root_pos_w=torch.zeros(1, 3), root_quat_w=torch.tensor([[1., 0., 0., 0.]]),
                             body_link_pos_w=torch.tensor([feet], dtype=torch.float32)))
        kb.ball = NS(data=NS(root_pos_w=torch.tensor([[0.6, 0., 0.11]]),
                            root_lin_vel_w=torch.tensor([[1., 0., 0.]])))
        kb.anchor_xy = torch.zeros(1, 2)
        kb.anchor_yaw = torch.zeros(1)
        kb.ball_active = torch.ones(1, dtype=torch.bool)
        kb.ball_kicked = torch.zeros(1, dtype=torch.bool)
        kb.steps_since_ball_ended = torch.zeros(1, dtype=torch.long)
        kb.prev_ball_vel_xy = torch.tensor([[-0.5, 0.]])
        kb.ball_y_ema = torch.zeros(1)
        kb.skill_is_left = torch.zeros(1, dtype=torch.bool)
        kb.foot_body_ids = torch.tensor([0, 1])
        kb.strike_gated_return_speed = True
        kb.require_foot_contact = True
        return kb

    far = fixture([[2., 1., 0.], [2., -1., 0.]])
    far.tick()
    assert not far.kick_success_flag.item() and far.ball_return_speed.item() == 1.
    lifted = fixture([[0.6, 0., 1.], [2., -1., 0.]])
    lifted.tick()
    assert lifted.kick_success_flag.item()
    lifted.ball_y_ema[:] = 0.8
    lifted.skill_is_left[:] = True
    lifted.rsi_probability = 0.
    # Keep serve itself out of this reset-isolation probe.
    lifted._serve = lambda ids: None
    lifted.reset(torch.tensor([0]))
    assert lifted.ball_y_ema.item() > 0.79 and lifted.skill_is_left.item()
    return {"no_foot_nearby": {"success": far.kick_success_flag.item(),
                                "rewarded_return_speed_mps": far.ball_return_speed.item()},
            "foot_0_89m_above_ball": {"success": True, "horizontal_distance_m": 0.},
            "skill_memory_survives_episode_reset": True,
            "scope": "Constructed state tensors; no simulated collision or measured false-positive rate."}


def checkpoint_and_export_probe():
    path = ROOT / "logs/rsl_rl/g1_soccer_v2/2026-09-18_18-50-26/model_2.pt"
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert set(ckpt) == {"model_state_dict", "optimizer_state_dict", "iter", "infos"}
    assert not any("discriminator" in k for k in ckpt["model_state_dict"])
    modules = load_module(PKG / "rsl_rl_extensions/modules.py", "soccer_audit_modules")
    exporter = load_module(ISAAC / "isaaclab_rl/isaaclab_rl/rsl_rl/exporter.py", "soccer_audit_exporter")
    obs = {"proprio_hist": torch.zeros(2, 864), "perception": torch.ones(2, 8, 27, 48),
           "proprio": torch.zeros(2, 108), "robot_vel": torch.zeros(2, 3),
           "privileged": torch.zeros(2, 6), "skill": torch.tensor([[1., 0.], [0., 1.]])}
    with contextlib.redirect_stdout(io.StringIO()):
        policy = modules.PerceptionActorCritic(
            obs, {"policy": ["proprio_hist", "perception"], "critic": ["proprio", "robot_vel", "privileged"]},
            29, num_critics=2, critic_obs_normalization=False, depth_conv_kernels=(5, 3, 3),
            depth_conv_paddings=(2, 1, 1), depth_activation="relu", depth_use_frame_diff=True,
            ball_head_hidden_dim=128)
    policy.load_state_dict(ckpt["model_state_dict"], strict=True)
    wrapper = exporter._TorchPolicyExporter(policy)
    assert not any("perception_encoder" in name for name, _ in wrapper.named_modules())
    with torch.no_grad():
        actions = policy.act_inference(obs)
        latent_input = policy._actor_features(obs)
        assert latent_input.shape == (2, 992)
        assert torch.allclose(actions, wrapper(latent_input))
        raw_input = torch.cat([obs["proprio_hist"], obs["perception"].flatten(1)], dim=-1)
        try:
            wrapper(raw_input)
        except RuntimeError as error:
            raw_error = str(error)
        else:
            raise AssertionError("Expected exporter to lack the perception preprocessing")
    return {"checkpoint_keys": list(ckpt), "strict_model_load": True,
            "amp_and_aux_optimizer_saved": False,
            "export_has_depth_encoder": False, "export_input_dim": 992,
            "raw_observation_dim": raw_input.shape[-1], "raw_input_error": raw_error}


def terminal_probe():
    from rsl_rl.algorithms import PPO
    import inspect
    source(Path(inspect.getfile(PPO)))
    tree = source(PKG / "rsl_rl_extensions/algorithm.py")
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SkillAMPPPO")
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "process_env_step")
    spy = {}

    class BaseSpy:
        @staticmethod
        def process_env_step(self, obs, rewards, dones, extras):
            spy["reward"] = rewards.clone()

    ns = {"PPO": BaseSpy}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "skill-amp-source", "exec"), ns)

    def predict(features, skill):
        spy["amp_input"] = features.clone()
        return features[:, 0]

    instance = NS(amp=NS(predict_reward=predict), amp_obs_group="amp", amp_reward_scale=0.5,
                  amp_coef=0.3, _skill_ids=lambda obs: obs["skill"].argmax(-1))
    reset_obs = {"amp": torch.tensor([[0.8]]), "skill": torch.tensor([[1., 0.]])}
    ns["process_env_step"](instance, reset_obs, torch.zeros(1), torch.ones(1),
                           {"terminal_amp": torch.tensor([[0.2]])})
    assert torch.allclose(spy["reward"], torch.tensor([0.12]))
    env_tree = source(ISAAC / "isaaclab/isaaclab/envs/manager_based_rl_env.py")
    env_step = next(n for c in env_tree.body if isinstance(c, ast.ClassDef) for n in c.body
                    if isinstance(n, ast.FunctionDef) and n.name == "step")
    reset_line = next(n.lineno for n in ast.walk(env_step) if isinstance(n, ast.Call) and
                      isinstance(n.func, ast.Attribute) and n.func.attr == "_reset_idx")
    obs_lines = [n.lineno for n in ast.walk(env_step) if isinstance(n, ast.Call) and
                 isinstance(n.func, ast.Attribute) and n.func.attr == "compute" and
                 any(k.arg == "update_history" for k in n.keywords)]
    assert max(obs_lines) > reset_line
    return {"env_returns_post_reset_observation": True, "done_amp_reward_uses_reset_observation": True,
            "constructed_amp_reward": spy["reward"].item(), "terminal_feature_unused": 0.2}


def main():
    result = {"scope": "CPU source/data probes, not physics or policy-performance evaluation",
              "amp_height": height_probe(), "state_machine": state_probe(),
              "checkpoint_export": checkpoint_and_export_probe(), "terminal_transition": terminal_probe()}
    for path in [PKG / "rsl_rl_extensions/runner.py", PKG / "rsl_rl_extensions/amp.py",
                 PKG / "tasks/manager_based/perceptual_ball/perceptual_ball_env_cfg.py",
                 PKG / "tasks/manager_based/perceptual_ball/soccer_v2_env_cfg.py"]:
        source(path)
    result["source_sha256"] = sources
    output = Path(__file__).with_name("audit_soccer_cpu_results.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "source_sha256"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
