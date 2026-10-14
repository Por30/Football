"""Separate geometry audit and fresh continuous PPO/AMP acceptance processes."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument('--variant', type=int, choices=(3, 4), required=True)
parser.add_argument('--num-envs', type=int, default=4)
parser.add_argument('--scale-preflight', action='store_true')
parser.add_argument('--geometry-only', action='store_true')
parser.add_argument('--iterations', type=int, default=20)
parser.add_argument('--output', required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
import copy
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_walled_env_cfg as config
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox as base_task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner


def geometry(b, wrapped, cfg, report):
    with torch.inference_mode():
        for skill in range(3):
            cfg.reset_skill_probabilities = tuple(float(i == skill) for i in range(3))
            cfg.search_prob = 1. if args.variant == 4 else 0.
            obs, _ = wrapped.reset()
            assert (task.state(b).skills == skill).all()
            camera = b.scene['depth_camera']
            if cfg.depth_backend == 'warp':
                mount = camera._offset_pos
            else:
                mount, _ = camera._view.get_local_poses()
            nominal = torch.tensor(cfg.scene.depth_camera.offset.pos, device=args.device)
            assert ((mount - nominal).abs() <= cfg.camera_position_error_m + 1e-5).all()
            assert obs['perception'].shape == (args.num_envs, 4, 27, 48)
            assert obs['proprio'].shape == (args.num_envs, 372)
            assert obs['amp'].shape == (args.num_envs, 640)
            assert obs['box_pose_target'].shape == (args.num_envs, 9)
            assert all(torch.isfinite(v).all() for v in obs.values())
            torch.testing.assert_close(obs['perception'][:, -1], task.depth_image(b))
            torch.testing.assert_close(obs['box_pose_target'], task.box_pose_target(b))
            root = b.scene['robot'].data.root_pos_w
            box = b.scene['box'].data.root_pos_w
            assert (base_task.lift_geometry(b)[0] > -.002).all()
            if args.variant == 4:
                assert (task.state(b).search == (skill == 0)).all()
                if skill == 0:
                    delta = box - root
                    angle = torch.atan2(delta[:, 1], delta[:, 0]).abs()
                    assert (angle >= torch.pi / 3 - 1e-4).all()
                    assert (delta[:, :2].norm(dim=-1) >= .9).all()
            torch.testing.assert_close(task.obstacle_pose(b, 'platform')[:, :2], box[:, :2])
            hand_distance = (b.scene['robot'].data.body_pos_w[:, task.state(b).hands].mean(1) - box).norm(dim=-1)
            if skill == 2:
                assert (hand_distance < .6).all(), hand_distance
            report['rsi'][str(skill)] = {'root_height': root[:, 2].tolist(), 'hand_center_distance': hand_distance.tolist()}
            for name, low, high in [('wall', 3., 4.)] + [(f'cylinder{i}', 2.2, 3.2) for i in range(3)]:
                p = task.obstacle_pose(b, name)
                r = (p[:, :2] - root[:, :2]).norm(dim=-1)
                assert (r >= low - 1e-4).all() and (r <= high + 1e-4).all()
                prim = b.sim.get_initial_stage().GetPrimAtPath('/World/envs/env_0/' + name.capitalize())
                assert prim.HasAPI(UsdPhysics.RigidBodyAPI)
                assert not UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get()
                assert PhysxSchema.PhysxRigidBodyAPI(prim).GetLockedPosAxisAttr().Get() == 7
                assert PhysxSchema.PhysxRigidBodyAPI(prim).GetLockedRotAxisAttr().Get() == 7
                colliders = [p for p in Usd.PrimRange(prim) if p.HasAPI(UsdPhysics.CollisionAPI)]
                assert colliders and all(UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() for p in colliders)
        # Collision instance conversion must preserve all four shoulders and visual instances.
        robot_prim = b.sim.get_initial_stage().GetPrimAtPath('/World/envs/env_0/Robot')
        cylinders = [p for p in Usd.PrimRange(robot_prim, Usd.TraverseInstanceProxies())
                     if p.GetName() == 'cylinder' and '/collisions/' in str(p.GetPath())]
        assert len(cylinders) == 4
        assert all(p.IsA(UsdGeom.Mesh) and UsdPhysics.MeshCollisionAPI(p).GetApproximationAttr().Get() == 'convexHull' for p in cylinders)
        # Reset only env 0: cloned locked geometry must not change in other environments.
        other = task.obstacle_pose(b, 'wall').clone()
        b._reset_idx(torch.tensor([0], device=args.device))
        torch.testing.assert_close(task.obstacle_pose(b, 'wall')[1:], other[1:])
        cfg.reference_init = False
        cfg.search_prob = 0.
        wrapped.reset()
        origin = b.scene.env_origins
        q = torch.tensor([1., 0., 0., 0.], device=args.device).expand(args.num_envs, 4)
        def put(name, xyz):
            pose = torch.cat((origin + torch.tensor(xyz, device=args.device), q), -1)
            if name == 'box':
                b.scene[name].write_root_state_to_sim(torch.cat((pose, torch.zeros(args.num_envs, 6, device=args.device)), -1))
            else:
                task.write_obstacle_pose(b, name, pose)
        for name in ['platform', 'wall', 'cylinder0', 'cylinder1', 'cylinder2']:
            put(name, [10., 0., -5.])
        camera = b.scene['depth_camera']
        camera.set_world_poses(origin + torch.tensor([0., 0., 1.], device=args.device), q, convention='world')
        def render():
            b.scene.write_data_to_sim()
            b.sim.forward()
            b.sim.render()
            b.scene.update(.02)
            return base_task.depth_image(b).clone()
        put('box', [2.2, 0., 1.])
        box_visible = render()
        for name, z in [('wall', 1.5), ('cylinder0', .9)]:
            put(name, [1.5, 0., z])
            blocked = render()
            center = blocked[:, 13, 24] * 3.
            assert ((center > 1.2) & (center < 1.6)).all(), (name, center)
            assert ((box_visible[:, 13, 24] - blocked[:, 13, 24]) > .1).all()
            put('box', [2.7, 0., 1.])
            moved_hidden_box = render()
            torch.testing.assert_close(blocked[:, 13, 24], moved_hidden_box[:, 13, 24], atol=1e-4, rtol=0)
            report['depth_changes'][name] = {'nearest_depth_m': center.tolist(), 'hidden_box_invariant': True}
            put(name, [10., 0., -5.])
            put('box', [2.2, 0., 1.])
            render()
        # Static-pose changes must update PhysX too. Shoot a box at each obstacle
        # after moving it from its parked location; an absent collider lets it pass.
        report['collision_checks'] = {}
        for name, z in [('wall', 1.5), ('cylinder0', .9)]:
            put(name, [1.5, 0., z])
            put('box', [.65, 0., 1.4])
            velocity = torch.zeros(args.num_envs, 6, device=args.device)
            velocity[:, 0] = 3.
            b.scene['box'].write_root_velocity_to_sim(velocity)
            b.scene.write_data_to_sim()
            b.sim.forward()
            for _ in range(60):
                b.sim.step(render=False)
                b.scene.update(b.physics_dt)
            torch.testing.assert_close(task.obstacle_pose(b, name)[:, :3], origin + torch.tensor([1.5, 0., z], device=args.device), atol=1e-5, rtol=0)
            torch.testing.assert_close(b.scene[name].data.root_vel_w, torch.zeros_like(b.scene[name].data.root_vel_w), atol=1e-5, rtol=0)
            x = b.scene['box'].data.root_pos_w[:, 0] - origin[:, 0]
            assert (x < 1.3).all(), (name, x)
            assert (x > .7).all(), (name, x)
            report['collision_checks'][name] = x.tolist()
            put(name, [10., 0., -5.])
        # A relocated platform supports a falling box above ground.
        put('platform', [2., 0., .6])
        put('box', [2., 0., 1.4])
        b.scene.write_data_to_sim()
        b.sim.forward()
        for _ in range(100):
            b.sim.step(render=False)
            b.scene.update(b.physics_dt)
        z = b.scene['box'].data.root_pos_w[:, 2] - origin[:, 2]
        assert ((z > 1.10) & (z < 1.16)).all(), z
        report['collision_checks']['platform_support_z'] = z.tolist()


def train(b, wrapped, cfg, agent, out, report):
    runner = CarryBoxOnPolicyRunner(wrapped, agent.to_dict(), log_dir=str(out / 'train'), device=args.device)
    before = copy.deepcopy(runner.alg.amp.state_dict())
    step = wrapped.step
    resets = 0
    max_speed = 0.
    def checked_step(action):
        nonlocal resets, max_speed
        obs, reward, done, info = step(action)
        torch.cuda.synchronize()
        assert all(torch.isfinite(v).all() for v in obs.values())
        assert torch.isfinite(reward).all()
        speed = float(b.scene['box'].data.root_lin_vel_w.norm(dim=-1).max())
        max_speed = max(max_speed, speed)
        assert speed < 50., ('Box reset impulse', speed)
        resets += int(done.sum())
        return obs, reward, done, info
    wrapped.step = checked_step
    runner.learn(args.iterations, init_at_random_ep_len=args.scale_preflight)
    assert task.state(b).curriculum.iteration == args.iterations
    assert task.state(b).curriculum.anchor == 0
    assert not torch.equal(before['amp_linear.weight'], runner.alg.amp.amp_linear.weight)
    assert runner.alg.optimizer.state and runner.alg.amp_optimizer.state
    path = out / 'smoke_model.pt'
    runner.save(str(path))
    runner.load(str(path))
    # Resume must actually collect another rollout and update, not merely parse tensors.
    runner.learn(2)
    assert resets > 0
    assert all(torch.isfinite(v).all() for v in runner.alg.policy.state_dict().values())
    assert all(torch.isfinite(v).all() for v in runner.alg.amp.state_dict().values())
    changed = cfg.walled_variant
    cfg.walled_variant = 'walled4' if changed == 'walled3' else 'walled3'
    try:
        runner.load(str(path))
    except ValueError:
        pass
    else:
        raise AssertionError('Cross-variant checkpoint was accepted')
    transfer = CarryBoxOnPolicyRunner(wrapped, agent.to_dict(), log_dir=None, device=args.device)
    transfer.warm_start(str(path))
    assert not transfer.alg.optimizer.state and not transfer.alg.amp_statistics_initialized
    cfg.walled_variant = changed
    report.update(iterations=args.iterations, resumed_iterations=2, resets=resets,
                  max_box_speed_m_s=max_speed, checkpoint=True, environment_contract=b.checkpoint_contract())


def main():
    torch.set_num_threads(2)
    cfg = getattr(config, f'CarryBoxWalled{args.variant}EnvCfg')()
    agent = getattr(config, f'CarryBoxWalled{args.variant}PPORunnerCfg')()
    cfg.scene.num_envs = args.num_envs
    cfg.sim.device = args.device
    cfg.seed = 42
    if not args.scale_preflight:
        cfg.episode_length_s = .4
        agent.algorithm.num_learning_epochs = 1
        agent.algorithm.num_mini_batches = 1
    assert cfg.scene.depth_camera.height == 27 and cfg.terminations.success is None
    assert 'held_hand_speed' in vars(cfg.rewards) and not hasattr(cfg.rewards, 'torque_limits')
    assert 'agilekickball_v4_env_cfg' in gym.spec('Template-Perceptual-Ball-AgileKickball-v4').kwargs['env_cfg_entry_point']
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    env = gym.make(f'Template-Perceptual-Ball-CarryBox-Walled{args.variant}-v0', cfg=cfg)
    try:
        b = env.unwrapped
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        report = dict(variant=args.variant, rsi={}, depth_changes={}, num_envs=args.num_envs,
                      scale_preflight=args.scale_preflight, geometry_only=args.geometry_only,
                      trained_success_rate='not_evaluated')
        if args.geometry_only:
            geometry(b, wrapped, cfg, report)
        else:
            train(b, wrapped, cfg, agent, out, report)
        report['status'] = 'PASS'
        (out / ('geometry.json' if args.geometry_only else 'smoke.json')).write_text(json.dumps(report, indent=2) + '\n')
        print('CARRYBOX_WALLED_SMOKE_PASS', flush=True)
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
