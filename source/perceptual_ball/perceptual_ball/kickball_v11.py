"""Kickball v11 motion data, supervision and return curriculum contracts."""
import hashlib
from pathlib import Path
import torch
from .amp_features import pack_amp_frame
from .carrybox_wall10 import Wall10MotionLibrary
from .tasks.manager_based.perceptual_ball.mdp.amp import MotionLibrary, KICK_MOTION_CLIP_PATHS
from .tasks.manager_based.perceptual_ball.mdp.agilekickball_v4 import AgileKickballV4State

REVISION = 'wall11_return5_aux_standing_v1'
FEATURE_SCHEMA = 'kick_height1_joints29_wrist_anklepitch_head15_lin3_ang3_rot6_zeroobject3_v1'
MOTION_DIR = str(Path(KICK_MOTION_CLIP_PATHS[0]).resolve().parent)
CRITIC_DIM = 124


class KickMotionLibrary(MotionLibrary):
    """Original football feature semantics, sampled through wall11's batched API."""
    window_length = 10
    windows = Wall10MotionLibrary.windows
    sample_window_parameters = Wall10MotionLibrary.sample_window_parameters
    sample_expert_amp_obs = Wall10MotionLibrary.sample_expert_amp_obs

    def __init__(self, root=MOTION_DIR, device='cpu', env_fps=50.):
        paths = [Path(root) / f'kick_{side}.pt' for side in ('left', 'right')]
        super().__init__([str(p) for p in paths], device, env_fps, (.95, 1.05))
        self.frames = pack_amp_frame(self.base_height, self.joint_position, self.ee_pos_b,
                                    self.base_lin_vel_b, self.base_ang_vel_b, self.root_rot_6d)
        if not torch.isfinite(self.frames).all() or (self.lengths < 32).any():
            raise ValueError('Invalid kick reference frames/window length')
        self.offsets = self.starts
        self.weights = torch.full((2,), .5, device=device)
        self.metadata = dict(schema=1, feature_schema=FEATURE_SCHEMA, frame_dim=60,
            fps=self.fps, lengths=self.lengths.tolist(), joint_names=self.joint_names,
            files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            clip_weights=[.5, .5], time_jitter=[.95, 1.05], window_length=10,
            interpolation='native_features', normalization='none', object_features='zero_both_sides')


def ball_state_loss(prediction, target):
    """Root-frame metres and relative inertial velocity m/s; all paired frames."""
    if prediction.shape != target.shape or prediction.shape[-1] != 6:
        raise ValueError('Ball supervision requires paired xyz/velocity six-vectors')
    target = target.detach()
    position = (prediction[..., :3] - target[..., :3]).square().mean()
    velocity = ((prediction[..., 3:] - target[..., 3:]) / 5.).square().mean()
    return position, velocity


class KickballV11State(AgileKickballV4State):
    curriculum_checkpoint_key = 'kickball_v11_curriculum'

    def __init__(self, env):
        super().__init__(env, initial_exposure_steps=60000.)
        self.course_config.update(revision=REVISION, speed_bounds=[.4, 1.1, 2., 5.],
                                  distance_range=[1.3, 2.], reset='standing_only')
        self._sync_course()

    def _sync_course(self):
        super()._sync_course()
        progress = self.extension_steps / self.course_config['extension_steps']
        self.course_upper = (self.extension_start_upper + (5. - self.extension_start_upper) * progress
                             if self.extension_unlocked else self._bootstrap_upper())
        self.serve_speed_range = self.serve_speed_override or (.4, self.course_upper)
        self.serve_distance_range = (1.3, 2.)
        self._validate_speed()

    def _validate_speed(self):
        lo, hi = self.serve_speed_override or self.serve_speed_range
        if not (.4 <= lo <= hi <= 5.):
            raise ValueError('kickballv11 incoming speed must remain within 0.4--5 m/s')

    def _sample_serve_speed(self, env_ids):
        self._validate_speed()
        return super()._sample_serve_speed(env_ids)

    def _serve(self, env_ids):
        before = self.serves[env_ids].clone()
        super()._serve(env_ids)
        ids = env_ids[self.serves[env_ids] != before]
        # A re-serve teleports the ball within the same control step. Invalidate
        # only affected captures; the next observation reads the new live pose.
        if len(ids) and 'depth_camera' in getattr(self.env.scene, 'sensors', {}):
            self.env.scene['depth_camera'].reset(ids)
            if hasattr(self.env, '_wall11_depth'):
                self.env._wall11_depth.reset(ids)

    def metrics(self):
        return {k.replace('AgileV4/', 'KickballV11/').replace('AgileKickball/', 'KickballV11/'):
                v for k, v in super().metrics().items()}
