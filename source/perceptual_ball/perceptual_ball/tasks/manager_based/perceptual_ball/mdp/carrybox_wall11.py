"""Wall10 lift-and-stay with noisy depth and randomized physical distractors."""
import torch
from isaaclab.utils.math import quat_from_euler_xyz
from perceptual_ball.carrybox_wall11 import NoisyDepthFrame, obstacle_layout
from . import carrybox_wall10 as base
from .carrybox_walled import write_obstacle_pose


def depth_image(env):
    clean = env.scene['depth_camera'].data.output['distance_to_image_plane'][..., 0]
    if not hasattr(env, '_wall11_depth'):
        env._wall11_depth = NoisyDepthFrame(clean)
    return env._wall11_depth.update(env.common_step_counter, clean, env.cfg.depth_noise)


def reset_scene(env, env_ids):
    base.reset_scene(env, env_ids)
    robot, box = env.scene['robot'].data, env.scene['box'].data
    columns, wall_xy, yaw, _ = obstacle_layout(robot.root_link_pos_w[env_ids, :2],
        robot.body_link_pos_w[env_ids, :, :2], box.root_pos_w[env_ids, :2],
        env.scene['depth_camera'].box_sizes[env_ids])
    ground = env.scene.env_origins[env_ids, 2]
    pose = torch.zeros(len(env_ids), 7, device=env.device)
    pose[:, 3] = 1.
    for i in range(3):
        pose[:, :2] = columns[:, i]
        pose[:, 2] = ground + .9
        write_obstacle_pose(env, f'cylinder{i}', pose, env_ids)
    pose[:, :2] = wall_xy
    pose[:, 2] = ground + 1.5
    zeros = torch.zeros_like(yaw)
    pose[:, 3:7] = quat_from_euler_xyz(zeros, zeros, yaw)
    write_obstacle_pose(env, 'wall', pose, env_ids)
    if hasattr(env, '_wall11_depth'):
        env._wall11_depth.reset(env_ids)


class Wall11CarryBoxEnv(base.Wall10CarryBoxEnv):
    def terminal_frame(self, group):
        return depth_image(self) if group == 'perception' else super().terminal_frame(group)

    def step(self, action):
        result = super().step(action)
        log = result[-1].get('log', {})
        for key in list(log):
            if key.startswith('Wall10/'):
                log[key.replace('Wall10/', 'Wall11/', 1)] = log.pop(key)
        return result

    @property
    def depth_contract(self):
        contract = super().depth_contract
        contract.update(geometry='robot_ground_wall_3cylinders_support_variable_box',
                        noise=dict(self.cfg.depth_noise), capture='once_per_control_step_per_env_reset_invalidated')
        return contract

    def checkpoint_contract(self):
        contract = super().checkpoint_contract()
        contract.update(variant='walled11', migration_revision=1, parent='walled10_revision1',
            obstacles=dict(layout='protected_workspace_ring_v1', cylinder_count=3,
                cylinder_radius_m=.15, cylinder_height_m=1.8, wall_size_m=[.2, 8., 3.],
                robot_link_margin_m=.5, box_support_margin_m=.1, ring_margin_m=.35,
                ring_min_radius_m=1.35, ring_jitter_m=[0., .35], wall_radial_gap_m=[.45, .8],
                physics='six_locked_axes_dynamic_tensor_teleport_zero_velocity',
                resample='every_episode_reset', collision=True, depth_occlusion=True))
        return contract
