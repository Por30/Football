"""G1 wall variants. Truth is used only by reset, rewards and paired supervision."""
import math
from types import SimpleNamespace
import torch
from isaaclab.utils.math import (quat_apply, quat_apply_inverse, quat_mul, quat_conjugate,
    quat_from_euler_xyz, matrix_from_quat, yaw_quat, euler_xyz_from_quat, wrap_to_pi)
from perceptual_ball.carrybox_amp import FindBoxMotionLibrary, joint_mapping, resolve_dataset_path
from perceptual_ball.carrybox_walled import YawCurriculum, PairedDepthBuffer, search_reward
from . import carrybox as base


def state(env):
    if not hasattr(env, '_walled'):
        robot = env.scene['robot']
        env._walled = SimpleNamespace(
            curriculum=YawCurriculum(env.cfg.walled_variant), paired=None, library=None, references=None,
            skills=torch.zeros(env.num_envs, device=env.device, dtype=torch.long),
            search=torch.zeros(env.num_envs, device=env.device, dtype=torch.bool),
            achieved=torch.zeros(env.num_envs, device=env.device, dtype=torch.bool),
            arm_ids=robot.find_joints(['.*shoulder.*', '.*elbow.*', '.*wrist.*'])[0],
            waist_id=robot.find_joints('waist_yaw_joint')[0][0],
            hands=robot.find_bodies(['left_rubber_hand', 'right_rubber_hand'], preserve_order=True)[0],
            torso=robot.find_bodies('torso_link')[0][0],
            head=robot.find_bodies('head_link')[0][0])
    return env._walled


def captured_pair(env):
    s = state(env)
    depth = base.depth_image(env)
    pose = base.box_pose_target(env)
    if s.paired is None:
        s.paired = PairedDepthBuffer(depth, pose, env.cfg.depth_max_delay_steps)
    if (s.paired.last_step == env.common_step_counter).all():
        return s.paired.output_depth, s.paired.output_pose
    depth = (depth + torch.randn_like(depth)*env.cfg.depth_noise_std_m/3.).clamp(.1/3., 1.)
    delays = torch.randint(env.cfg.depth_max_delay_steps+1, (env.num_envs,), device=env.device)
    freezes = torch.randint(1, env.cfg.depth_freeze_max_steps+1, (env.num_envs,), device=env.device)
    freezes *= torch.rand(env.num_envs, device=env.device) < env.cfg.depth_freeze_probability
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
    if s.library is None:
        s.library = FindBoxMotionLibrary('findbox', device=env.device)
        s.references = []
        for name in s.library.clip_names:
            data = torch.load(resolve_dataset_path()/name, map_location=env.device, weights_only=True)
            data = {k: v.float() if isinstance(v, torch.Tensor) and v.is_floating_point() else v for k,v in data.items()}
            for key, shape in [('base_position',(len(data['joint_position']),3)),
                               ('base_height',(len(data['joint_position']),)),
                               ('box_pos_local',(len(data['joint_position']),3))]:
                if data[key].shape != shape or not torch.isfinite(data[key]).all():
                    raise ValueError(f'Invalid RSI {name}: {key}')
            s.references.append(data)
    inverse = torch.argsort(torch.tensor(joint_mapping(robot.joint_names), device=env.device))
    box_positions = torch.zeros((len(ids),3), device=env.device)
    support_tops = torch.zeros(len(ids), device=env.device)
    for skill, group in enumerate(('loco_direction','pickUp','carryWith')):
        rows = (s.skills[ids] == skill).nonzero().flatten()
        clips = [i for i,g in enumerate(s.library.clip_groups) if g == group]
        selection = torch.randint(len(clips), (len(rows),), device=env.device)
        for slot, clip in enumerate(clips):
            selected = rows[selection == slot]
            if not len(selected):
                continue
            env_ids = ids[selected]
            data = s.references[clip]
            joints, velocity, quaternion, angular = s.library.clips[clip]
            frames = torch.randint(len(joints)-1, (len(selected),), device=env.device)
            q = quaternion[frames]
            undo_yaw = quat_conjugate(yaw_quat(q))
            root = robot.data.default_root_state[env_ids].clone()
            root[:, :3] = env.scene.env_origins[env_ids]
            root[:, 2] += data['base_height'][frames] + .05
            root[:, 3:7] = quat_mul(undo_yaw,q)
            linear = (data['base_position'][frames+1]-data['base_position'][frames])*60.
            linear[:,2] = (data['base_height'][frames+1]-data['base_height'][frames])*60.
            root[:,7:10] = quat_apply(undo_yaw, linear)
            root[:,10:13] = quat_apply(root[:,3:7], angular[frames])
            robot.write_root_state_to_sim(root, env_ids=env_ids)
            robot.write_joint_state_to_sim(joints[frames][:,inverse], velocity[frames][:,inverse], env_ids=env_ids)
            box_positions[selected] = root[:,:3]+quat_apply(undo_yaw,data['box_pos_local'][frames])
            if group == 'pickUp':
                contact = int(data['contact_index'])
                # Proxy support: source provides no platform geometry or box orientation.
                top = data['base_height'][contact]+.05+data['box_pos_local'][contact,2]-base.BOX_SIZE[2]/2
                support_tops[selected] = top.clamp_min(0.)
    return box_positions, support_tops


def obstacle_pose(env, name):
    """Actual tensor pose of a locked rigid collider, for reset/audit only."""
    return env.scene[name].data.root_state_w[:, :7]


def write_obstacle_pose(env, name, pose, env_ids=None):
    """Instant tensor teleport; six locked axes keep the obstacle stationary."""
    velocity = torch.zeros((len(pose), 6), device=pose.device, dtype=pose.dtype)
    env.scene[name].write_root_state_to_sim(torch.cat((pose, velocity), -1), env_ids=env_ids)


def reset_scene(env, env_ids):
    s = state(env)
    n, device = len(env_ids), env.device
    probs = torch.tensor(env.cfg.reset_skill_probabilities, device=device)
    if probs.shape != (3,) or (probs < 0).any() or abs(float(probs.sum())-1.) > 1e-6:
        raise ValueError('RSI probabilities must sum to one (loco,pickUp,carryWith)')
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
    write_obstacle_pose(env, 'platform', platform_state, env_ids)
    # Parent robot/box/platform first; wall then independently sampled columns.
    for name, low, high, z in [('wall',3.,4.,1.5)]+[(f'cylinder{i}',2.2,3.2,.9) for i in range(3)]:
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
    position += torch.empty_like(position).uniform_(-env.cfg.camera_position_error_m,env.cfg.camera_position_error_m)
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
    return search_reward(state(env).search,angle,delta[:,:2].norm(dim=-1),robot.root_ang_vel_b[:,2])


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
    # Literal source criterion: positive roll > .5; symmetric pitch threshold.
    return (wrap_to_pi(roll)>.5) | (wrap_to_pi(pitch).abs()>1.1)


def fallen(env):
    robot = env.scene['robot'].data
    s = state(env)
    head = robot.body_pos_w[:,s.head]
    z = env.scene.env_origins[:,2]
    return (robot.root_pos_w[:,2]-z<.2) | (head[:,2]-z<.4)


class WalledCarryBoxEnv(base.CarryBoxEnv):
    def terminal_frame(self, group):
        return {'proprio':base.proprioception,'perception':depth_image,'amp':base.amp_frame}[group](self)

    def set_training_iteration(self, iteration):
        state(self).curriculum.set_iteration(iteration)

    def checkpoint_contract(self):
        return dict(variant=self.cfg.walled_variant, migration_revision=5, depth_backend=self.cfg.depth_backend,
                    depth_geometry='all_visible_link_meshes_ground2000_v1', depth_clip='optical_near_plane_pixel_centers_v1',
                    failure_reward="current_transition", obstacle_backend="locked_rigid_6dof", shoulder_colliders="convex_hull_32", depth_shape=[4,27,48],
                    reference_init=self.cfg.reference_init, reset_probs=list(self.cfg.reset_skill_probabilities),
                    search_prob=self.cfg.search_prob, noise=self.cfg.depth_noise_std_m,
                    delay=self.cfg.depth_max_delay_steps, freeze=self.cfg.depth_freeze_probability,
                    freeze_steps=self.cfg.depth_freeze_max_steps,
                    mount_pos=self.cfg.camera_position_error_m,mount_rot=self.cfg.camera_rotation_error_deg,
                    curriculum='process_anchor', reward_parent='g1_carrybox_v0')

    def _reset_idx(self, env_ids):
        success = state(self).achieved[env_ids].float().mean() if len(env_ids) else 0.
        super()._reset_idx(env_ids)
        if self.cfg.depth_backend == 'warp':
            # RTX used render()->forward() here. Pure Warp needs the same
            # articulation kinematics refresh before reading reset link poses.
            self.sim.forward()
        self.extras.setdefault('log',{})['Curriculum/box_yaw_range_deg'] = state(self).curriculum.degrees
        self.extras['log']['Metrics/episode_lift_success'] = success
