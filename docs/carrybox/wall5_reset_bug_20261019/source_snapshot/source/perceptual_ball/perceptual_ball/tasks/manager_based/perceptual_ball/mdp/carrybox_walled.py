"""G1 wall variants. Truth is used only by reset, rewards and paired supervision."""
import math
from types import SimpleNamespace
import torch
from isaaclab.utils.math import (quat_apply, quat_apply_inverse, quat_mul, quat_conjugate,
    quat_from_euler_xyz, matrix_from_quat, yaw_quat, euler_xyz_from_quat, wrap_to_pi)
from perceptual_ball.carrybox_amp import FindBoxMotionLibrary, joint_mapping
from perceptual_ball.carrybox_walled import YawCurriculum, PairedDepthBuffer, search_reward, corrupt_depth_m
from . import carrybox as base


def state(env):
    if not hasattr(env, '_walled'):
        robot = env.scene['robot']
        env._walled = SimpleNamespace(
            curriculum=YawCurriculum(env.cfg.walled_variant), paired=None, library=None, references=None,
            skills=torch.zeros(env.num_envs, device=env.device, dtype=torch.long),
            search=torch.zeros(env.num_envs, device=env.device, dtype=torch.bool),
            achieved=torch.zeros(env.num_envs, device=env.device, dtype=torch.bool),
            episode_counts=torch.zeros(3, device=env.device, dtype=torch.long),
            success_counts=torch.zeros(3, device=env.device, dtype=torch.long),
            episode_steps=torch.zeros(3, device=env.device, dtype=torch.long),
            valid_amp_steps=torch.zeros(3, device=env.device, dtype=torch.long),
            tipped_counts=torch.zeros(3, device=env.device, dtype=torch.long),
            fell_counts=torch.zeros(3, device=env.device, dtype=torch.long),
            actual_episode_steps=torch.zeros(env.num_envs, device=env.device, dtype=torch.long),
            arm_ids=robot.find_joints(['.*shoulder.*', '.*elbow.*', '.*wrist.*'])[0],
            waist_id=robot.find_joints('waist_yaw_joint')[0][0],
            knees=robot.find_joints(['left_knee_joint', 'right_knee_joint'], preserve_order=True)[0],
            hands=robot.find_bodies(['left_rubber_hand', 'right_rubber_hand'], preserve_order=True)[0],
            torso=robot.find_bodies('torso_link')[0][0],
            head=robot.find_bodies('head_link')[0][0])
    return env._walled


def captured_pair(env):
    s = state(env)
    if s.paired is not None and (s.paired.last_step == env.common_step_counter).all():
        return s.paired.output_depth, s.paired.output_pose
    depth = base.depth_image(env)
    pose = base.box_pose_target(env)
    depth = corrupt_depth_m(depth*3., gaussian_std=env.cfg.depth_noise_std_m,
        edge_threshold=env.cfg.depth_edge_threshold_m, edge_probability=env.cfg.depth_edge_probability,
        hole_probability=env.cfg.depth_hole_probability,
        stereo_near=env.cfg.depth_stereo_near_m, stereo_far=env.cfg.depth_stereo_far_m) / 3.
    if getattr(env.cfg, 'pose_visibility_supervision', False):
        from .carrybox_wall5 import pose_visible
        pose = torch.cat((pose, pose_visible(env, depth, pose)[:, None].float()), -1)
    if s.paired is None:
        s.paired = PairedDepthBuffer(depth, pose, env.cfg.depth_max_delay_steps)
    delays = (torch.rand(env.num_envs, device=env.device) < env.cfg.depth_delay_probability).long()
    # Count the onset image as frame 1, then hold it for fourteen more frames.
    freezes = (torch.rand(env.num_envs, device=env.device) < env.cfg.depth_freeze_probability).long()
    freezes *= env.cfg.depth_freeze_max_steps - 1
    return s.paired.update(env.common_step_counter, depth, pose, delays, freezes)


def depth_image(env):
    return captured_pair(env)[0]


def box_pose_target(env):
    return captured_pair(env)[1]


def heading(quat):
    return euler_xyz_from_quat(quat)[2]


def initialize_reference(env, ids):
    """RSI root/joints use verified G1 data; box orientation is unavailable in source."""
    s, robot = state(env), env.scene['robot']
    ground_only = getattr(getattr(env, 'cfg', None), 'ground_box_reset', False)
    link_velocity = getattr(getattr(env, 'cfg', None), 'reference_link_velocity', False)
    held_reference = getattr(getattr(env, 'cfg', None), 'held_box_reference_reset', False)
    if ground_only and not held_reference and (s.skills[ids] == 2).any():
        raise ValueError('Ground-box reset does not support held-box RSI')
    if s.library is None:
        s.library = FindBoxMotionLibrary(
            getattr(getattr(env, 'cfg', None), 'reference_motion_dataset', None), device=env.device)
        s.references = []
        for name in s.library.clip_names:
            data = torch.load(s.library.root/name, map_location=env.device, weights_only=True)
            data = {k: v.float() if isinstance(v, torch.Tensor) and v.is_floating_point() else v for k,v in data.items()}
            for key, shape in [('base_position',(len(data['joint_position']),3)),
                               ('base_height',(len(data['joint_position']),)),
                               ('box_pos_local',(len(data['joint_position']),3))]:
                if data[key].shape != shape or not torch.isfinite(data[key]).all():
                    raise ValueError(f'Invalid RSI {name}: {key}')
            s.references.append(data)
        if ground_only:
            from perceptual_ball.carrybox_wall5 import ground_pickup_frame_ids
            start, end = env.cfg.ground_pickup_reset_frame_range
            if start < 0 or end <= start:
                raise ValueError('Invalid collision-checked ground-pickup frame range')
            s.ground_reference_frames = [ground_pickup_frame_ids(data) if group == 'pickUp' else None
                for data, group in zip(s.references, s.library.clip_groups)]
            s.ground_reference_frames = [frames[(frames >= start) & (frames < end)] if frames is not None else None
                for frames in s.ground_reference_frames]
    inverse = torch.argsort(torch.tensor(joint_mapping(robot.joint_names), device=env.device))
    box_positions = torch.zeros((len(ids),3), device=env.device)
    support_tops = torch.zeros(len(ids), device=env.device)
    if link_velocity:
        root_batch = torch.empty((len(ids), 13), device=env.device)
        joint_batch = torch.empty((len(ids), len(inverse)), device=env.device)
        velocity_batch = torch.empty_like(joint_batch)
    for skill, group in enumerate(('loco_direction','pickUp','carryWith')):
        rows = (s.skills[ids] == skill).nonzero().flatten()
        if not len(rows):
            continue
        clips = [i for i,g in enumerate(s.library.clip_groups) if g == group]
        if ground_only and group == 'pickUp':
            clips = [i for i in clips if len(s.ground_reference_frames[i])]
            if not clips:
                raise ValueError('No ground-pickup frames available for RSI')
        selection = torch.randint(len(clips), (len(rows),), device=env.device)
        for slot, clip in enumerate(clips):
            selected = rows[selection == slot]
            if not len(selected):
                continue
            env_ids = ids[selected]
            data = s.references[clip]
            joints, velocity, quaternion, angular = s.library.clips[clip]
            if ground_only and group == 'pickUp':
                pool = s.ground_reference_frames[clip]
                frames = pool[torch.randint(len(pool), (len(selected),), device=env.device)]
            else:
                frames = torch.randint(len(joints)-1, (len(selected),), device=env.device)
            q = quaternion[frames]
            undo_yaw = quat_conjugate(yaw_quat(q))
            root = robot.data.default_root_state[env_ids].clone()
            root[:, :3] = env.scene.env_origins[env_ids]
            root[:, 2] += data['base_height'][frames] + .05
            root[:, 3:7] = quat_mul(undo_yaw,q)
            linear = (data['base_position'][frames+1]-data['base_position'][frames])*60.
            if not link_velocity:
                linear[:,2] = (data['base_height'][frames+1]-data['base_height'][frames])*60.
            root[:,7:10] = quat_apply(undo_yaw, linear)
            root[:,10:13] = quat_apply(root[:,3:7], angular[frames])
            # Wall5 task AMP compares pelvis-link velocity, not root COM velocity.
            if link_velocity:
                # Keep native sampling/RNG order; submit one PhysX write after all
                # clips, avoiding repeated whole-articulation buffer refreshes.
                root_batch[selected] = root
                joint_batch[selected] = joints[frames][:, inverse]
                velocity_batch[selected] = velocity[frames][:, inverse]
            else:
                robot.write_root_state_to_sim(root, env_ids=env_ids)
                robot.write_joint_state_to_sim(joints[frames][:,inverse], velocity[frames][:,inverse], env_ids=env_ids)
            box_positions[selected] = root[:,:3]+quat_apply(undo_yaw,data['box_pos_local'][frames])
            if group == 'pickUp' and not ground_only:
                contact = int(data['contact_index'])
                # Proxy support: source provides no platform geometry or box orientation.
                top = data['base_height'][contact]+.05+data['box_pos_local'][contact,2]-base.BOX_SIZE[2]/2
                support_tops[selected] = top.clamp_min(0.)
    if link_velocity:
        robot.write_root_link_state_to_sim(root_batch, env_ids=ids)
        robot.write_joint_state_to_sim(joint_batch, velocity_batch, env_ids=ids)
    # base_height is a reference-frame height, not the bottom of the G1 foot
    # collider. Refresh the written articulation before resolving penetration.
    env.sim.forward()
    correction = reference_ground_correction(env, ids)
    root = robot.data.root_state_w[ids].clone()
    root[:, 2] += correction
    robot.write_root_state_to_sim(root, env_ids=ids)
    box_positions[:, 2] += correction
    support_tops += correction
    return box_positions, support_tops


def reference_ground_correction(env, ids):
    """Lift penetrating RSI feet to 5 mm clearance using the G1 collision hulls."""
    s, robot = state(env), env.scene['robot']
    if not hasattr(s, 'foot_support_points'):
        import numpy as np
        import trimesh
        from pxr import Usd, UsdGeom, UsdPhysics
        stage = env.sim.get_initial_stage()
        cache = UsdGeom.XformCache()
        names = ['left_ankle_roll_link', 'right_ankle_roll_link']
        s.feet = robot.find_bodies(names, preserve_order=True)[0]
        s.foot_support_points = []
        for name in names:
            link = stage.GetPrimAtPath('/World/envs/env_0/Robot/' + name)
            inverse = cache.GetLocalToWorldTransform(link).GetInverse()
            points = []
            # The URDF converter applies a merged convex collider to this
            # parent Xform, rather than CollisionAPI to each descendant mesh.
            collider = stage.GetPrimAtPath(str(link.GetPath()) + '/collisions')
            if (not collider.HasAPI(UsdPhysics.CollisionAPI)
                    or UsdPhysics.MeshCollisionAPI(collider).GetApproximationAttr().Get() != 'convexHull'):
                raise RuntimeError(f'Unexpected G1 foot collision approximation: {name}')
            for prim in Usd.PrimRange(collider, Usd.TraverseInstanceProxies()):
                if prim.IsA(UsdGeom.Mesh):
                    vertices = np.asarray(UsdGeom.Mesh(prim).GetPointsAttr().Get())
                    transform = np.asarray(cache.GetLocalToWorldTransform(prim) * inverse)
                    points.append((np.c_[vertices, np.ones(len(vertices))] @ transform)[:, :3])
            if not points:
                raise RuntimeError(f'Missing G1 foot collision mesh: {name}')
            # Linear support extrema are unchanged by convex-hull reduction.
            vertices = np.concatenate(points)
            if not np.isfinite(vertices).all():
                raise RuntimeError(f'Non-finite G1 foot collision geometry: {name}')
            hull = trimesh.convex.convex_hull(vertices)
            s.foot_support_points.append(torch.tensor(np.asarray(hull.vertices).copy(), device=env.device, dtype=torch.float32))
    lowest = []
    for foot, points in zip(s.feet, s.foot_support_points):
        q = robot.data.body_link_quat_w[ids, foot, None].expand(-1, len(points), -1)
        world = quat_apply(q.reshape(-1, 4), points[None].expand(len(ids), -1, -1).reshape(-1, 3)).reshape(len(ids), -1, 3)
        lowest.append(world[:, :, 2].amin(-1) + robot.data.body_link_pos_w[ids, foot, 2])
    return (env.scene.env_origins[ids, 2] + .005 - torch.stack(lowest, -1).amin(-1)).clamp_min(0.)


def obstacle_pose(env, name):
    """Actual tensor pose of a locked rigid collider, for reset/audit only."""
    return env.scene[name].data.root_state_w[:, :7]


def write_obstacle_pose(env, name, pose, env_ids=None):
    """Instant tensor teleport; six locked axes keep the obstacle stationary."""
    velocity = torch.zeros((len(pose), 6), device=pose.device, dtype=pose.dtype)
    env.scene[name].write_root_state_to_sim(torch.cat((pose, velocity), -1), env_ids=env_ids)


def reset_scene(env, env_ids, skill_ids=None):
    s = state(env)
    s.reward_step = None
    n, device = len(env_ids), env.device
    probs = torch.tensor(env.cfg.reset_skill_probabilities, device=device)
    if probs.shape != (3,) or (probs < 0).any() or abs(float(probs.sum())-1.) > 1e-6:
        raise ValueError('RSI probabilities must sum to one (loco,pickUp,carryWith)')
    ground_only = getattr(env.cfg, 'ground_box_reset', False)
    held_reference = getattr(env.cfg, 'held_box_reference_reset', False)
    if ground_only and not held_reference and probs[2] != 0:
        raise ValueError('Ground-box reset requires zero held-box RSI probability')
    if skill_ids is not None:
        if skill_ids.shape != (n,) or skill_ids.dtype != torch.long or ((skill_ids < 0) | (skill_ids > 2)).any():
            raise ValueError('Explicit RSI skills must be one valid integer per reset environment')
        s.skills[env_ids] = skill_ids if env.cfg.reference_init else 0
    else:
        s.skills[env_ids] = torch.multinomial(probs, n, replacement=True) if env.cfg.reference_init else 0
    reference_box = support = None
    if env.cfg.reference_init:
        reference_box, support = initialize_reference(env,env_ids)
    base.reset_box(env,env_ids)  # initialize/reset success cache, after the final robot reset
    s.achieved[env_ids] = False
    s.search[env_ids] = False
    robot = env.scene['robot'].data
    box = env.scene['box']
    pose = box.data.root_state_w[env_ids].clone()
    zeros = torch.zeros(n,device=device)
    angle = torch.empty(n,device=device).uniform_(-math.pi/4,math.pi/4)
    radius = torch.empty(n,device=device).uniform_(.7,2.)
    loco = s.skills[env_ids] == 0
    search = loco & (torch.rand(n,device=device)<env.cfg.search_prob)
    s.search[env_ids] = search
    angle[search] = torch.empty(int(search.sum()),device=device).uniform_(math.pi/3,math.pi) * (
        torch.randint(2,(int(search.sum()),),device=device)*2-1)
    radius[search] = torch.empty(int(search.sum()),device=device).uniform_(.9,2.)
    yaw_robot = heading(robot.root_quat_w[env_ids])
    bearing = angle+yaw_robot
    pose[:,:2] = robot.root_pos_w[env_ids,:2]+radius[:,None]*torch.stack((bearing.cos(),bearing.sin()),-1)
    tilt = torch.empty((n,2),device=device).uniform_(-math.pi/6,math.pi/6)
    yaw_range = math.radians(s.curriculum.degrees)
    yaw = torch.empty(n,device=device).uniform_(-yaw_range,yaw_range)+yaw_robot
    pose[:,3:7] = quat_from_euler_xyz(tilt[:,0],tilt[:,1],yaw)
    # Preserve reference hand/box alignment for non-loco RSI. No box quaternion is recorded.
    reference = ~loco
    if reference_box is not None:
        pose[reference,:3] = reference_box[reference]
        pose[reference,3:7] = quat_from_euler_xyz(zeros[reference],zeros[reference],yaw_robot[reference])
    extent = (matrix_from_quat(pose[:,3:7])[:,2].abs()*torch.tensor(base.BOX_SIZE,device=device)/2).sum(-1)
    ground_z = env.scene.env_origins[env_ids,2]
    if ground_only:
        on_ground = (s.skills[env_ids] != 2) if held_reference else torch.ones_like(loco)
        pose[on_ground,2] = (ground_z+extent+.005)[on_ground]
        # Hold RSI retains the paired reference box pose; never place it below ground.
        pose[:,2] = torch.maximum(pose[:,2],ground_z+extent+.005)
    else:
        pose[loco,2] = ground_z[loco]+extent[loco]+.005
        pose[:,2] = torch.maximum(pose[:,2],ground_z+extent+.005)
    pose[:,7:] = 0.
    box.write_root_state_to_sim(pose, env_ids=env_ids)
    platform_state = torch.zeros((n,7),device=device)
    platform_state[:,:2] = pose[:,:2]
    top = zeros.clone()
    if support is not None:
        pickup = s.skills[env_ids] == 1
        # Keep support below the actual sampled box, including early pre-contact frames.
        top[pickup] = torch.minimum(support[pickup],pose[pickup,2]-ground_z[pickup]-extent[pickup]-.005).clamp_min(0.)
    platform_state[:,2] = ground_z+top-.4
    platform_state[:,3:7] = torch.tensor([1.,0.,0.,0.],device=device)
    if not ground_only:
        write_obstacle_pose(env, 'platform', platform_state, env_ids)
    # Parent robot/box/platform first; wall then independently sampled columns.
    for name, low, high, z in [('wall',3.,4.,1.5)]+[(f'cylinder{i}',2.2,3.2,.9) for i in range(env.cfg.obstacle_cylinder_count)]:
        p = torch.zeros((n,7),device=device)
        a = torch.rand(n,device=device)*2*math.pi
        r = torch.empty(n,device=device).uniform_(low,high)
        p[:,:2] = robot.root_pos_w[env_ids,:2]+r[:,None]*torch.stack((a.cos(),a.sin()),-1)
        p[:,2] = ground_z+z
        p[:,3:7] = quat_from_euler_xyz(zeros,zeros,a if name == 'wall' else zeros)
        write_obstacle_pose(env, name, p, env_ids)
    if s.paired is not None:
        s.paired.reset(env_ids)
    reset_camera(env, env_ids)
    # Manager reset populates extras['log'] later; env subclass appends this key afterwards.


def reset_camera(env, ids):
    s = state(env)
    cfg = env.cfg.scene.depth_camera.offset
    position = torch.tensor(cfg.pos,device=env.device).expand(len(ids),3).clone()
    direction = torch.randn_like(position)
    position += direction / direction.norm(dim=-1, keepdim=True).clamp_min(1.e-9) * env.cfg.camera_position_error_m
    delta = torch.empty_like(position).uniform_(-math.radians(env.cfg.camera_rotation_error_deg),math.radians(env.cfg.camera_rotation_error_deg))
    q = quat_mul(torch.tensor(cfg.rot,device=env.device).expand(len(ids),4),quat_from_euler_xyz(*delta.unbind(-1)))
    # Set the mount in its parent torso frame. World setters invert USD parent
    # transforms, which can lag PhysX/Fabric after an articulation reset.
    from isaaclab.utils.math import convert_camera_frame_orientation_convention
    optical = convert_camera_frame_orientation_convention(q, origin='world', target='opengl')
    camera = env.scene['depth_camera']
    if hasattr(camera, 'set_mount_poses'):
        camera.set_mount_poses(position, optical, ids)
    else:
        camera._view.set_local_poses(position, optical, indices=ids)


def held_joint_excess(env, acceleration=False, threshold=1.):
    s, robot, box = state(env),env.scene['robot'].data,env.scene['box'].data
    hands = robot.body_pos_w[:,s.hands].mean(1)
    held = ((box.root_pos_w[:,2]-env.scene.env_origins[:,2])>.55) & ((hands-box.root_pos_w).norm(dim=-1)<.15)
    value = robot.joint_acc if acceleration else robot.joint_vel
    return (value[:,s.arm_ids].abs()-threshold).clamp_min(0).square().mean(-1)*held


def waist_yaw(env):
    robot = env.scene['robot'].data
    i = state(env).waist_id
    return (robot.joint_pos[:,i]-robot.default_joint_pos[:,i]).abs()


def search_turn(env):
    robot, box = env.scene['robot'].data,env.scene['box'].data
    delta = box.root_pos_w-robot.root_pos_w
    angle = wrap_to_pi(torch.atan2(delta[:,1],delta[:,0])-heading(robot.root_quat_w))
    torso = state(env).torso
    angular = quat_apply_inverse(robot.body_quat_w[:,torso], robot.body_ang_vel_w[:,torso])
    return search_reward(state(env).search,angle,delta[:,:2].norm(dim=-1),angular[:,2])


def success_pulse(env):
    s = state(env)
    success = base.lift_success(env)
    new = success & ~s.achieved
    s.achieved |= success
    return new.float()


def failure_event(env, term_keys=('fell', 'tipped')):
    """One failure penalty on the current transition, never a previous episode.

    This Isaac Lab version retains get_term() flags for episode statistics after
    reset. Gate those named flags with the current aggregate termination signal.
    """
    manager = env.termination_manager
    named = torch.zeros_like(manager.terminated)
    for key in term_keys:
        named |= manager.get_term(key)
    return (named & manager.terminated & ~manager.time_outs).float()


def tipped(env):
    roll,pitch,_ = euler_xyz_from_quat(env.scene['robot'].data.root_quat_w)
    return (wrap_to_pi(roll).abs()>.5) | (wrap_to_pi(pitch).abs()>1.1)


def randomize_default_joint_pos(env, env_ids, magnitude=.01):
    """Startup only; keep action offsets and observed defaults in the same frame."""
    robot = env.scene['robot']
    if env_ids is None:
        env_ids = torch.arange(env.num_envs, device=env.device)
    default = robot.data.default_joint_pos
    default[env_ids] += torch.empty_like(default[env_ids]).uniform_(-magnitude, magnitude)
    action = env.action_manager.get_term('joint_pos')
    action._offset[env_ids] = default[env_ids][:, action._joint_ids]


def push_velocity(env, env_ids, velocity_range):
    """Set a bounded root velocity, not an accumulating velocity increment."""
    ranges = torch.tensor([velocity_range[k] for k in ('x','y','z','roll','pitch','yaw')], device=env.device)
    velocity = ranges[:,0] + torch.rand((len(env_ids),6), device=env.device) * (ranges[:,1]-ranges[:,0])
    if hasattr(getattr(env, 'cfg', None), 'push_warmup_iterations'):
        curriculum = state(env).curriculum
        effective = 0 if curriculum.anchor is None else max(0, curriculum.iteration-curriculum.anchor)
        scale = max(0., min(1., (effective-env.cfg.push_warmup_iterations)/env.cfg.push_ramp_iterations))
        if scale == 0.:
            return  # Do not set velocity to zero: that would itself perturb locomotion.
        current = env.scene['robot'].data.root_vel_w[env_ids]
        velocity = current + scale*(velocity-current)
    env.scene['robot'].write_root_velocity_to_sim(velocity, env_ids=env_ids)


def head_height(env):
    """Physical head COM, not the G1 head-link frame near the waist."""
    return env.scene['robot'].data.body_com_pos_w[:, state(env).head, 2] - env.scene.env_origins[:, 2]


def reference_joint_pos_limits(env):
    """Retain soft limits except knee extension, where valid expert poses use the hard lower bound."""
    robot = env.scene['robot'].data
    low = robot.soft_joint_pos_limits[..., 0].clone()
    low[:, state(env).knees] = robot.joint_pos_limits[:, state(env).knees, 0]
    return ((low-robot.joint_pos).clamp_min(0)
            + (robot.joint_pos-robot.soft_joint_pos_limits[..., 1]).clamp_min(0)).sum(-1)


def fallen(env):
    robot = env.scene['robot'].data
    z = env.scene.env_origins[:,2]
    return (robot.root_pos_w[:,2]-z<.2) | (head_height(env)<.4)


def record_episode_metrics(env, env_ids):
    """Count executed transitions, independent of runner-randomized timeout ages."""
    s = state(env)
    if getattr(env, '_carrybox_in_step', False):
        for skill in range(3):
            ids = env_ids[s.skills[env_ids] == skill]
            s.episode_counts[skill] += len(ids)
            s.success_counts[skill] += s.achieved[ids].sum()
            lengths = s.actual_episode_steps[ids]
            s.episode_steps[skill] += lengths.sum()
            s.valid_amp_steps[skill] += (lengths-getattr(env, 'amp_warmup_steps', 8)).clamp_min(0).sum()
            s.tipped_counts[skill] += env.termination_manager.get_term('tipped')[ids].sum()
            s.fell_counts[skill] += env.termination_manager.get_term('fell')[ids].sum()
    s.actual_episode_steps[env_ids] = 0


class WalledCarryBoxEnv(base.CarryBoxEnv):
    def step(self, action):
        state(self).actual_episode_steps += 1
        result = super().step(action)
        term = self.action_manager.get_term('joint_pos')
        self.extras.setdefault('log', {})['Control/physical_target_clipped_fraction'] = term.target_saturation.float().mean()
        return result

    def terminal_frame(self, group):
        return {'proprio':base.proprioception,'perception':depth_image,'amp':base.amp_frame}[group](self)

    def set_training_iteration(self, iteration):
        state(self).curriculum.set_iteration(iteration)

    def checkpoint_contract(self):
        return dict(variant=self.cfg.walled_variant, migration_revision=8, depth_backend=self.cfg.depth_backend,
                    reference_ground_clearance='G1_collision_hull_min_5mm_upward_only',
                    obstacle_cylinders=self.cfg.obstacle_cylinder_count,
                    head_reference='head_link_COM', knee_lower_penalty='hard_limit_other_limits_soft',
                    action_targets='clamp_to_physical_joint_limits',
                    push_curriculum=[self.cfg.push_warmup_iterations,self.cfg.push_ramp_iterations],
                    depth_geometry='all_visible_link_meshes_ground2000_v1', depth_clip='optical_near_plane_pixel_centers_v1',
                    failure_reward="none_x2_recipe", obstacle_backend="locked_rigid_6dof", shoulder_colliders="convex_hull_32", depth_shape=[4,27,48],
                    reference_init=self.cfg.reference_init, reset_probs=list(self.cfg.reset_skill_probabilities),
                    search_prob=self.cfg.search_prob, noise=self.cfg.depth_noise_std_m,
                    depth_edge=[self.cfg.depth_edge_threshold_m,self.cfg.depth_edge_probability],
                    depth_holes=self.cfg.depth_hole_probability,
                    depth_stereo=[self.cfg.depth_stereo_near_m,self.cfg.depth_stereo_far_m],
                    latency_probability=self.cfg.depth_delay_probability,
                    depth_noise_contract='metres_miss_preserved_near_clamp_15_including_onset',
                    delay=self.cfg.depth_max_delay_steps, freeze=self.cfg.depth_freeze_probability,
                    freeze_steps=self.cfg.depth_freeze_max_steps,
                    mount_pos=self.cfg.camera_position_error_m,mount_rot=self.cfg.camera_rotation_error_deg,
                    curriculum='shared_piecewise_process_anchor', reward_parent='g1_corrected_common_v2',
                    reward_weights={name:term.weight for name,term in vars(self.cfg.rewards).items()
                                    if term is not None and hasattr(term,'weight')},
                    roll_termination='abs_roll_gt_0.5', action_scale=self.cfg.actions.joint_pos.scale, action_clip=9.,
                    randomization={name:{k:v for k,v in getattr(self.cfg.events,name).params.items() if k!='asset_cfg'}
                                   for name in ('box_material','box_mass','default_joint_pos','torso_com','push_robot')},
                    box_mass_kg=self.cfg.scene.box.spawn.mass_props.mass,
                    com_body='torso_link', push_interval=list(self.cfg.events.push_robot.interval_range_s),
                    hand_forces='g1_rubber_hands_box_filtered', standup_success='instant_x2',
                    strict_success_metric='g1_contact_clearance_hold0.5s')

    def _reset_idx(self, env_ids):
        s = state(self)
        success = s.achieved[env_ids].float().mean() if len(env_ids) else 0.
        record_episode_metrics(self, env_ids)
        super()._reset_idx(env_ids)
        if self.cfg.depth_backend == 'warp':
            # RTX used render()->forward() here. Pure Warp needs the same
            # articulation kinematics refresh before reading reset link poses.
            self.sim.forward()
        self.extras.setdefault('log',{})['Curriculum/box_yaw_range_deg'] = state(self).curriculum.degrees
        self.extras['log']['Metrics/episode_lift_success'] = success
        for skill, name in enumerate(('loco','pickup','hold')):
            count = s.episode_counts[skill].clamp_min(1)
            self.extras['log'][f'Skill/{name}_episodes'] = s.episode_counts[skill].float()
            self.extras['log'][f'Skill/{name}_success_fraction'] = s.success_counts[skill]/count
            self.extras['log'][f'Skill/{name}_successes'] = s.success_counts[skill].float()
            self.extras['log'][f'Skill/{name}_tipped_fraction'] = s.tipped_counts[skill]/count
            self.extras['log'][f'Skill/{name}_fell_fraction'] = s.fell_counts[skill]/count
            self.extras['log'][f'Skill/{name}_mean_steps'] = s.episode_steps[skill]/count
            self.extras['log'][f'Skill/{name}_valid_amp_steps'] = s.valid_amp_steps[skill].float()
