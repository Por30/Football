"""Shared AMP conventions for reference clips and live robot state."""
import torch


def relative_base_height(root_pos, end_effector_pos):
    return root_pos[..., 2:3] - end_effector_pos[..., 2].amin(dim=-1, keepdim=True)


def pack_amp_frame(height, joints, ee_local, linear_velocity, angular_velocity, rotation_6d):
    """Object features are zero on both sides because the mocap has no ball trajectory."""
    return torch.cat((height, joints, ee_local, linear_velocity, angular_velocity,
                      rotation_6d, torch.zeros_like(linear_velocity)), dim=-1)
