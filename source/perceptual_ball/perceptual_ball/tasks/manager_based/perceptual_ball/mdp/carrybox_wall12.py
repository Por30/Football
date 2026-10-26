"""Wall11 physics with synchronized training-only camera-frame box pose labels."""
import torch
from perceptual_ball.carrybox_wall12 import POSE_CONTRACT
from . import carrybox as base
from . import carrybox_wall11 as wall11


def _capture(env):
    depth = wall11.depth_image(env)
    if not hasattr(env, '_wall12_pose'):
        env._wall12_pose = depth.new_empty((env.num_envs, 12))
        env._wall12_pose_step = torch.full((env.num_envs,), -1, device=env.device, dtype=torch.long)
    ids = (env._wall12_pose_step != env.common_step_counter).nonzero().flatten()
    if len(ids):
        target = torch.cat((base.box_pose_target(env), env.scene['depth_camera'].box_sizes), -1).detach()
        env._wall12_pose[ids] = target[ids]
        env._wall12_pose_step[ids] = env.common_step_counter
    return depth, env._wall12_pose


def depth_image(env):
    return _capture(env)[0]


def box_pose_target(env):
    return _capture(env)[1]


def reset_scene(env, env_ids):
    wall11.reset_scene(env, env_ids)
    if hasattr(env, '_wall12_pose_step'):
        env._wall12_pose_step[env_ids] = -1


class Wall12CarryBoxEnv(wall11.Wall11CarryBoxEnv):
    def terminal_frame(self, group):
        return depth_image(self) if group == 'perception' else super().terminal_frame(group)

    def step(self, action):
        result = super().step(action)
        log = result[-1].get('log', {})
        for key in list(log):
            if key.startswith('Wall11/'):
                log[key.replace('Wall11/', 'Wall12/', 1)] = log.pop(key)
        return result

    def checkpoint_contract(self):
        contract = super().checkpoint_contract()
        contract.update(variant='walled12', migration_revision=1, parent='walled11_revision1',
                        pose_supervision=dict(POSE_CONTRACT))
        return contract
