"""Actual geometry, physical obstacle and reset/noise acceptance checks."""
import math
import torch
from pxr import Usd, UsdGeom, UsdPhysics
from isaaclab.utils.math import quat_apply, quat_from_euler_xyz
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall11 as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled import write_obstacle_pose


def obstacle_checks(env):
    camera = env.scene['depth_camera']
    assert camera.cfg.object_names == ('Wall', 'Platform', 'Cylinder0', 'Cylinder1', 'Cylinder2')
    # Check the conservative robot margin against the actual collision geometry.
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render', 'proxy', 'guide'], useExtentsHint=False, ignoreVisibility=True)
    bounds = []
    robot = camera.stage.GetPrimAtPath('/World/envs/env_0/Robot')
    for link in Usd.PrimRange(robot):
        if not link.HasAPI(UsdPhysics.RigidBodyAPI):
            continue
        for prim in Usd.PrimRange(link, Usd.TraverseInstanceProxies()):
            if not prim.HasAPI(UsdPhysics.CollisionAPI):
                continue
            if UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get() is False:
                continue
            extent = cache.ComputeRelativeBound(prim, link).ComputeAlignedRange()
            if not extent.IsEmpty():
                bounds.append(max(extent.GetCorner(i).GetLength() for i in range(8)))
    assert bounds and max(bounds) < .5, bounds
    # Verify real reset positions satisfy the protected-region contract.
    data = env.scene['robot'].data
    box = env.scene['box'].data.root_pos_w[:, :2]
    centre = (data.root_link_pos_w[:, :2] + box) / 2
    protected = (data.body_link_pos_w[:, :, :2] - centre[:, None]).norm(dim=-1).amax(-1) + .5
    columns = torch.stack([env.scene[f'cylinder{i}'].data.root_pos_w[:, :2] for i in range(3)], 1)
    assert ((columns - centre[:, None]).norm(dim=-1) - .15 >= protected[:, None] + .1999).all()
    # Teleport each type into the camera's forward half-space. Depth must change.
    ids = torch.arange(env.num_envs, device=env.device)
    hidden = torch.zeros(env.num_envs, 7, device=env.device)
    hidden[:, :3] = env.scene.env_origins
    hidden[:, 2] -= 5
    hidden[:, 3] = 1
    for name in ('wall', 'cylinder0', 'cylinder1', 'cylinder2'):
        write_obstacle_pose(env, name, hidden, ids)
    env.sim.forward()
    camera._update_buffers_impl(ids)
    clean = camera._depth.clone()
    direction = quat_apply(camera._data.quat_w_world, torch.tensor([1., 0., 0.], device=env.device).expand(env.num_envs, -1))
    direction[:, 2] = 0
    direction /= direction.norm(dim=-1, keepdim=True)
    changes = {}
    for name, distance, height in [('cylinder0', .7, .9), ('wall', 1., 1.5)]:
        pose = hidden.clone()
        pose[:, :3] = camera._data.pos_w + direction * distance
        pose[:, 2] = env.scene.env_origins[:, 2] + height
        if name == 'wall':
            yaw = torch.atan2(direction[:, 1], direction[:, 0])
            pose[:, 3:7] = quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)
        write_obstacle_pose(env, name, pose, ids)
        env.sim.forward()
        camera._update_buffers_impl(ids)
        changed = (clean - camera._depth > .05).sum(-1)
        assert (changed > 10).any(), (name, changed)
        changes[name] = changed.tolist()
        torch.testing.assert_close(env.scene[name].root_physx_view.get_transforms()[:, :3], pose[:, :3])
        prim = camera.stage.GetPrimAtPath('/World/envs/env_0/' + ('Wall' if name == 'wall' else 'Cylinder0'))
        from pxr import PhysxSchema
        assert PhysxSchema.PhysxRigidBodyAPI(prim).GetLockedPosAxisAttr().Get() == 7
        assert PhysxSchema.PhysxRigidBodyAPI(prim).GetLockedRotAxisAttr().Get() == 7
        assert any(p.HasAPI(UsdPhysics.CollisionAPI) for p in Usd.PrimRange(prim))
        write_obstacle_pose(env, name, hidden, ids)
        env.sim.forward()
    return dict(robot_collision_count=len(bounds), max_collision_radius_m=max(bounds),
                depth_changed_pixels=changes, reset_clearance=True, physical_locked_colliders=True)


def reset_checks(env):
    depth = task.depth_image(env).clone()
    rng = torch.cuda.get_rng_state(env.device).clone()
    torch.testing.assert_close(task.depth_image(env), depth, atol=0, rtol=0)
    assert torch.equal(torch.cuda.get_rng_state(env.device), rng)
    assert not torch.equal(depth, env.scene['depth_camera'].data.output['distance_to_image_plane'][..., 0])
    ids = torch.tensor([env.num_envs - 1, 0], device=env.device)
    keep = torch.arange(1, env.num_envs - 1, device=env.device)
    poses = {name: env.scene[name].data.root_state_w.clone() for name in ('wall', 'cylinder0', 'cylinder1', 'cylinder2')}
    old_history = env.observation_manager.compute_group('perception').clone()
    env._reset_idx(ids)
    assert (env._wall11_depth.last_step[ids] == -1).all()
    for name in poses:
        torch.testing.assert_close(env.scene[name].data.root_state_w[keep], poses[name][keep], atol=1.e-6, rtol=0)
    new_depth = task.depth_image(env)
    torch.testing.assert_close(new_depth[keep], depth[keep], atol=0, rtol=0)
    history = env.observation_manager.compute_group('perception', update_history=True)
    torch.testing.assert_close(history[ids], new_depth[ids, None].expand(-1, 4, -1, -1), atol=0, rtol=0)
    torch.testing.assert_close(history[keep], old_history[keep], atol=0, rtol=0)

    # Observe the actual pre-reset terminal callback, compared later by smoke.py.
    original = env.terminal_frame
    def capture(group):
        frame = original(group)
        if group == 'perception':
            env._wall11_terminal_probe = frame.clone()
        return frame
    env.terminal_frame = capture
