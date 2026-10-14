"""Compare camera readers on actual rendering, then measure unchanged wall4 rollouts."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument('--num-envs', type=int, required=True)
parser.add_argument('--output', required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import cProfile
import json
import pstats
import time
from pathlib import Path
from types import MethodType
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab.sensors import TiledCamera
from isaaclab.utils.math import quat_apply, quat_mul, quat_conjugate, quat_apply_inverse, matrix_from_quat
from isaaclab.utils.math import convert_camera_frame_orientation_convention as convert
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.carrybox_camera import FabricTiledCamera
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_env_cfg import CarryBoxEnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg, CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox as base
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner


def main():
    torch.set_num_threads(2)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    cfg, agent = CarryBoxWalled4EnvCfg(), CarryBoxWalled4PPORunnerCfg()
    assert cfg.scene.depth_camera.class_type is FabricTiledCamera
    assert CarryBoxEnvCfg().scene.depth_camera.class_type is TiledCamera
    # Begin before the candidate has created any Fabric world attributes.
    cfg.scene.depth_camera.class_type = TiledCamera
    cfg.scene.num_envs, cfg.sim.device, cfg.seed = args.num_envs, args.device, 42
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0', cfg=cfg)
    b = env.unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    cam = b.scene['depth_camera']
    report = dict(num_envs=args.num_envs, max_position_error_m=0., max_rotation_matrix_error=0.)
    ids = torch.arange(args.num_envs, device=args.device)
    actions = torch.zeros((args.num_envs, 29), device=args.device)

    def backend(fast):
        cam._update_poses = MethodType(FabricTiledCamera._update_poses if fast else TiledCamera._update_poses, cam)

    def render():
        b.scene.write_data_to_sim()
        b.sim.forward()
        b.sim.render()
        b.scene.update(.02)
        return base.depth_image(b).clone()

    def check_poses():
        depth = base.depth_image(b).clone()
        TiledCamera._update_poses(cam, ids)
        original_pos = cam._data.pos_w.clone()
        original_q = cam._data.quat_w_world.clone()
        original_label = base.box_pose_target(b).clone()
        FabricTiledCamera._update_poses(cam, ids)
        from pxr import UsdGeom
        transforms = [UsdGeom.Xformable(cam.stage.GetPrimAtPath(path)).GetLocalTransformation() for path in cam._view.prim_paths]
        local_p = torch.tensor([list(t.ExtractTranslation()) for t in transforms], device=args.device)
        local_gl = torch.tensor([[t.ExtractRotationQuat().GetReal(), *t.ExtractRotationQuat().GetImaginary()] for t in transforms], device=args.device)
        torso = task.state(b).torso
        expected_p = b.scene['robot'].data.body_pos_w[:, torso] + quat_apply(b.scene['robot'].data.body_quat_w[:, torso], local_p)
        print('pose_check', dict(original_error=float((original_pos-expected_p).abs().max()), candidate_error=float((cam._data.pos_w-expected_p).abs().max())), flush=True)
        torch.testing.assert_close(cam._data.pos_w, original_pos, atol=2e-4, rtol=0)
        torch.testing.assert_close(matrix_from_quat(cam._data.quat_w_world), matrix_from_quat(original_q), atol=2e-5, rtol=0)
        torch.testing.assert_close(base.box_pose_target(b), original_label, atol=2e-4, rtol=0)
        torch.testing.assert_close(base.depth_image(b), depth, atol=0, rtol=0)
        # Independent reference: actual PhysX parent link and current USD local mount.
        torso = task.state(b).torso
        parent_p = b.scene['robot'].data.body_pos_w[:, torso]
        parent_q = b.scene['robot'].data.body_quat_w[:, torso]
        expected_p = parent_p + quat_apply(parent_q, local_p)
        expected_q = convert(quat_mul(parent_q, local_gl), origin='opengl', target='world')
        pe = float((expected_p - cam._data.pos_w).abs().max())
        re = float((matrix_from_quat(expected_q) - matrix_from_quat(cam._data.quat_w_world)).abs().max())
        report['max_position_error_m'] = max(report['max_position_error_m'], pe)
        report['max_rotation_matrix_error'] = max(report['max_rotation_matrix_error'], re)
        torch.testing.assert_close(cam._data.pos_w, expected_p, atol=2e-4, rtol=0)
        torch.testing.assert_close(matrix_from_quat(cam._data.quat_w_world), matrix_from_quat(expected_q), atol=2e-5, rtol=0)
        assert torch.isfinite(cam._data.pos_w).all()
        torch.testing.assert_close(cam._data.quat_w_world.norm(dim=-1), torch.ones_like(ids, dtype=torch.float), atol=2e-5, rtol=0)

    try:
        with torch.inference_mode():
            wrapped.reset()
            render()
            if args.num_envs == 4:
                # Explicitly check first Fabric read and subsequent moving/reset frames.
                check_poses()
                backend(True)
                initial = cam._data.pos_w.clone()
                for i in range(24):
                    wrapped.step(actions)
                    check_poses()
                    if i == 10:
                        selected = torch.tensor([3, 1], device=args.device)
                        other = cam._data.pos_w[[0, 2]].clone()
                        b._reset_idx(selected)
                        render()
                        check_poses()
                        torch.testing.assert_close(cam._data.pos_w[[0, 2]], other, atol=2e-4, rtol=0)
                        # Reader partial writes must not touch unselected cache rows.
                        cam._data.pos_w[[0, 2]] = 123.
                        cam._update_poses(selected)
                        assert (cam._data.pos_w[[0, 2]] == 123.).all()
                        cam._update_poses(ids)
                assert (cam._data.pos_w - initial).abs().max() > .01
                report['moving_and_partial_reset'] = True
                pair_d, pair_p = task.captured_pair(b)
                torch.testing.assert_close(pair_d, task.depth_image(b), atol=0, rtol=0)
                torch.testing.assert_close(pair_p, task.box_pose_target(b), atol=0, rtol=0)
                report['paired_cache'] = True
            else:
                # No Fabric preparation before timing the original reader.
                for name, fast in [('original', False), ('fabric', True)]:
                    backend(fast)
                    torch.manual_seed(42)
                    wrapped.reset()
                    for _ in range(4):
                        wrapped.step(actions)
                    torch.cuda.synchronize()
                    profile = cProfile.Profile()
                    times = []
                    for _ in range(48):
                        start = time.perf_counter()
                        wrapped.step(actions)
                        torch.cuda.synchronize()
                        times.append(time.perf_counter() - start)
                    profile.enable()
                    for _ in range(4):
                        wrapped.step(actions)
                        torch.cuda.synchronize()
                    profile.disable()
                    profile.dump_stats(str(out / (name + '.prof')))
                    with (out / (name + '_profile.txt')).open('w') as stream:
                        pstats.Stats(profile, stream=stream).sort_stats('cumtime').print_stats(45)
                    report[name] = dict(step_mean_s=sum(times)/len(times), transitions_per_s=args.num_envs*len(times)/sum(times), steps=48)
                    print(name, report[name], flush=True)
                    if fast:
                        check_poses()
                report['speedup'] = report['original']['step_mean_s'] / report['fabric']['step_mean_s']
        if args.num_envs != 4:
            backend(True)
            runner = CarryBoxOnPolicyRunner(wrapped, agent.to_dict(), log_dir=str(out / 'train'), device=args.device)
            old = json.loads(Path('docs/carrybox/performance_20261014/before_launch.json').read_text())
            runner.load(old['checkpoint'])
            runner.learn(2, init_at_random_ep_len=True)
            runner.save(str(out / 'verification_model.pt'))
            runner.load(str(out / 'verification_model.pt'))
            runner.learn(2)
            assert runner.alg.optimizer.state and runner.alg.amp_optimizer.state
            assert all(torch.isfinite(v).all() for v in runner.alg.policy.state_dict().values())
            report['ppo_amp_updates'] = 4
            report['resume'] = True
            report['environment_contract'] = b.checkpoint_contract()
            assert report['speedup'] > 1.05, 'Candidate not measurably faster'
        report['status'] = 'PASS'
        (out / 'benchmark.json').write_text(json.dumps(report, indent=2) + '\n')
        print('CARRYBOX_CAMERA_BENCHMARK_PASS', flush=True)
    except BaseException:
        import traceback
        traceback.print_exc()
        raise
    finally:
        env.close()


try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    app.close(wait_for_replicator=False)
