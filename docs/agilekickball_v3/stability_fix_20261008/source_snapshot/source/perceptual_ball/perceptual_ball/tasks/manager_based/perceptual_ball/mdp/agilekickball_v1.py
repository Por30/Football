"""v0 bootstrap and ball rounds, with a gradual incoming-speed extension to 5 m/s."""
import copy
import math
from .agilekickball import AgileKickballState


class AgileKickballV1State(AgileKickballState):
    curriculum_checkpoint_key = 'agile_speed_curriculum'

    def __init__(self, env, extension_ramp_steps=240_000):
        if type(extension_ramp_steps) is not int or extension_ramp_steps <= 0:
            raise ValueError('extension_ramp_steps must be a positive integer')
        super().__init__(env)
        self.course_config = dict(v0_ramp_steps=240_000, extension_ramp_steps=extension_ramp_steps,
                                  distance_ramp_steps=60_000, speed_bounds=[.4, .8, 2., 5.])
        self.curriculum_training = True
        self.course_exposure = 0.
        self._sync_course()

    def balanced(self):
        # Keep v0 body/stance bounds. Instantaneous all-joint speed also measures
        # PPO exploration noise and must not indefinitely block an upright robot.
        data = self.robot.data
        height = data.root_pos_w[:, 2] - self.env_origins[:, 2]
        feet_z = data.body_link_pos_w[:, self.foot_body_ids, 2] - self.env_origins[:, 2, None]
        return ((data.projected_gravity_b[:, :2].norm(dim=-1) < .15)
                & (data.projected_gravity_b[:, 2] < -.98)
                & (data.root_lin_vel_w.norm(dim=-1) < .25)
                & (data.root_ang_vel_b.norm(dim=-1) < .5)
                & (height > .7) & (height < .9)
                & data.joint_vel.isfinite().all(-1)
                & (feet_z < .12).all(-1) & (feet_z > -.03).all(-1))

    @staticmethod
    def _validate_exposure(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('Incoming exposure must be finite and nonnegative')
        return float(value)

    def _sync_course(self):
        if self.curriculum_training:
            self.course_exposure = self._validate_exposure(self.exposure_steps)
        e, c = self.course_exposure, self.course_config
        if e <= c['v0_ramp_steps']:
            upper = .8 + 1.2 * e / c['v0_ramp_steps']
        else:
            upper = 2. + 3. * min((e - c['v0_ramp_steps']) / c['extension_ramp_steps'], 1.)
        self.serve_speed_range = self.serve_speed_override or (.4, upper)
        p = min(e / c['distance_ramp_steps'], 1.)
        self.serve_distance_range = (.5 + .8 * p, .7 + 1.3 * p)

    def curriculum_state_dict(self):
        self._sync_course()
        return dict(schema=2, config=copy.deepcopy(self.course_config), exposure_steps=self.course_exposure)

    def load_curriculum_state_dict(self, data):
        if data is None:
            data = dict(schema=2, config=self.course_config, exposure_steps=0.)
        if not isinstance(data, dict) or data.get('schema') != 2 or data.get('config') != self.course_config:
            raise ValueError('Incompatible v1 speed curriculum schema/config; old strict-success v1 '
                             'checkpoints cannot resume this task. Start a fresh training run.')
        exposure = self._validate_exposure(data.get('exposure_steps'))
        self.course_exposure = self.exposure_offset = exposure
        self.incoming_steps.zero_()  # saved mean is independent of the new parallel environment count
        self._sync_course()

    def metrics(self):
        result = super().metrics()
        result.update({'AgileV1/speed_upper_m_s': self.serve_speed_range[1],
                       'AgileV1/course_incoming_steps_per_env': self.course_exposure,
                       'AgileV1/speed_progress': min(self.course_exposure /
                           (self.course_config['v0_ramp_steps'] + self.course_config['extension_ramp_steps']), 1.),
                       'AgileV1/distance_min_m': self.serve_distance_range[0],
                       'AgileV1/distance_max_m': self.serve_distance_range[1],
                       'AgileV1/updates_enabled': int(self.curriculum_training)})
        return result


def setup_agilekickball_v1(env, env_ids, extension_ramp_steps=240_000):
    env._kickball = AgileKickballV1State(env, extension_ramp_steps)


def incoming_speed_curriculum(env, env_ids):
    """Same reset-time update as v0; only future serves use the new range."""
    env._kickball._sync_course()
    return env._kickball.serve_speed_range[1]
