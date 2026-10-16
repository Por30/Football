"""Wall5 AMP projection; original FindBox files and RSI states stay unchanged."""
import torch
from .carrybox_amp import AMP_WINDOW, AMP_FRAME_DIM, FindBoxMotionLibrary

WALL5_FRAME_DIM = 35
WALL5_FEATURE_SCHEMA = 'joint_pos29_gravity3_angvel3_raw_v1'


def project_frame(frame):
    """Source named joint order, radians, unit gravity, root-frame rad/s."""
    if frame.shape[-1] != AMP_FRAME_DIM:
        raise ValueError('Wall5 projection requires the original 64-component frame')
    return torch.cat((frame[..., :29], frame[..., 58:]), dim=-1)


class Wall5MotionLibrary(FindBoxMotionLibrary):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata.update(feature_schema=WALL5_FEATURE_SCHEMA, frame_dim=WALL5_FRAME_DIM)

    def windows(self, clip_ids, native_starts):
        original = super().windows(clip_ids, native_starts)
        return project_frame(original.reshape(-1, self.window_length, AMP_FRAME_DIM)).flatten(1)
