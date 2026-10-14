"""Return to the actual sender; privileged geometry is used only for reward/metrics."""
import copy
import math
import torch

from .agilekickball_v2 import AgileKickballV2State
from .agilekickball_v3 import AgileKickballV3State
from .kickball_state import KICK_FOOT_CONTACT_MAX_DIST, KICK_STRIKE_IMPULSE_THRESHOLD

REVISION = 'return_to_sender_20261012'
RETURN_CONFIG = dict(initial_half_width_m=.6, final_half_width_m=.2,
                     ramp_steps=120000, window_steps=6000, min_completed=128,
                     advance_hit_rate=.6, advance_recovery=.8,
                     min_forward_speed_m_s=.4, max_height_m=.35,
                     shaping_duration_s=.5)


def return_quality(xy, velocity, source, normal, half_width):
    """Bounded positive velocity and predicted lateral miss at the sender's plane."""
    offset = source - xy
    along = (velocity * normal).sum(-1)
    remaining = (offset * normal).sum(-1)
    time = remaining / along.clamp(min=1.e-6)
    crossing = xy + velocity * time[:, None]
    tangent = torch.stack((-normal[:, 1], normal[:, 0]), -1)
    error = ((crossing - source) * tangent).sum(-1).abs()
    cosine = (offset * velocity).sum(-1) / (
        offset.norm(dim=-1) * velocity.norm(dim=-1)).clamp(min=1.e-6)
    quality = torch.exp(-.5 * (error / half_width.clamp(min=1.e-6)).square()) * cosine.clamp(0., 1.)
    valid = ((along > RETURN_CONFIG['min_forward_speed_m_s']) & (remaining > 0)
             & torch.isfinite(quality) & torch.isfinite(error) & torch.isfinite(along))
    return torch.where(valid, quality, 0.), torch.where(valid, along.clamp(0., 3.), 0.), error


def source_gate_crossing(previous, current, source, normal, half_width):
    """Interpolate a one-way XY gate crossing, including the ball height in metres."""
    before = ((previous[:, :2] - source) * normal).sum(-1)
    after = ((current[:, :2] - source) * normal).sum(-1)
    fraction = (-before / (after - before).clamp(min=1.e-6)).clamp(0., 1.)
    crossing = previous + fraction[:, None] * (current - previous)
    tangent = torch.stack((-normal[:, 1], normal[:, 0]), -1)
    error = ((crossing[:, :2] - source) * tangent).sum(-1).abs()
    crossed = ((before < 0.) & (after >= 0.) & (after - before > 1.e-6)
               & torch.isfinite(crossing).all(-1) & torch.isfinite(error))
    low = (crossing[:, 2] >= 0.) & (crossing[:, 2] <= RETURN_CONFIG['max_height_m'])
    return crossed & low & (error <= half_width), crossed, error


class AgileKickballV4State(AgileKickballV3State):
    curriculum_checkpoint_key = 'agile_v4_return_curriculum'

    def __init__(self, env, initial_exposure_steps=60000.):
        super().__init__(env, initial_exposure_steps)
        self.course_config['revision'] = REVISION
        self.course_config['return_to_sender'] = copy.deepcopy(RETURN_CONFIG)
        # Keep the original radial kick proxy for the inherited speed course.
        # V4 rewards and return success use a separate foot-qualified signal.
        self.source_xy = torch.zeros(env.num_envs, 2, device=env.device)
        self.return_normal = torch.zeros_like(self.source_xy)
        self.previous_ball_xyz = torch.zeros(env.num_envs, 3, device=env.device)
        self.round_half_width = torch.full_like(self.wait_elapsed, .6)
        for name in ('round_open', 'return_has_strike', 'return_hit', 'strict_return_hit', 'return_gate_passed'):
            setattr(self, name, torch.zeros_like(self.ball_active))
        for name in ('return_age', 'return_dense', 'return_kick_quality', 'return_target_pulse', 'return_miss_pulse'):
            setattr(self, name, torch.zeros_like(self.wait_elapsed))
        for name in ('completed_rounds', 'completed_target_hits', 'completed_strict_hits',
                     'completed_foot_strikes', 'foot_strike_rounds', 'target_hits', 'strict_hits'):
            setattr(self, name, torch.zeros_like(self.serves))
        self.direction_steps = 0.
        self.direction_advance_rate = 0.
        self.recent_target_hit_rate = 0.
        self.recent_completed_rounds = 0
        self._direction_window_start = self.course_steps
        self._direction_window_counts = self._return_counts()
        self._sync_course()

    @property
    def target_half_width(self):
        c = RETURN_CONFIG
        return c['initial_half_width_m'] + (c['final_half_width_m'] - c['initial_half_width_m']) * (
            self.direction_steps / c['ramp_steps'])

    def _return_counts(self):
        return tuple(int(x.sum().item()) for x in (self.completed_rounds, self.completed_target_hits))

    def _finish_rounds(self, ids):
        ids = ids[self.round_open[ids]]
        self.completed_rounds[ids] += 1
        self.completed_target_hits[ids] += self.return_hit[ids].long()
        self.completed_strict_hits[ids] += self.strict_return_hit[ids].long()
        self.completed_foot_strikes[ids] += self.return_has_strike[ids].long()
        self.round_open[ids] = False

    def reset(self, env_ids):
        self._finish_rounds(env_ids)
        super().reset(env_ids)

    def _serve(self, env_ids):
        before = self.serves[env_ids].clone()
        super()._serve(env_ids)
        ids = env_ids[self.serves[env_ids] != before]
        self.source_xy[ids] = self.ball.data.root_pos_w[ids, :2]
        velocity = self.ball.data.root_lin_vel_w[ids, :2]
        self.return_normal[ids] = -velocity / velocity.norm(dim=-1, keepdim=True).clamp(min=1.e-6)
        self.previous_ball_xyz[ids] = self.ball.data.root_pos_w[ids]
        self.round_half_width[ids] = self.target_half_width
        self.round_open[ids] = True
        for name in ('return_has_strike', 'return_hit', 'strict_return_hit', 'return_gate_passed', 'return_age',
                     'return_dense', 'return_kick_quality', 'return_target_pulse', 'return_miss_pulse'):
            getattr(self, name)[ids] = 0

    def tick(self):
        if self.last_tick == self.env.common_step_counter:
            return
        active = self.ball_active.clone()
        served = self.serves.clone()
        xyz = self.ball.data.root_pos_w.clone()
        velocity = self.ball.data.root_lin_vel_w[:, :2].clone()
        alive = ~self.env.reset_buf.bool()
        foot_distance = (self.robot.data.body_link_pos_w[:, self.foot_body_ids] - xyz[:, None]).norm(dim=-1).amin(-1)
        strike = (active & alive & (foot_distance < KICK_FOOT_CONTACT_MAX_DIST)
                  & ((velocity - self.prev_ball_vel_xy).norm(dim=-1) > KICK_STRIKE_IMPULSE_THRESHOLD))
        super().tick()
        same_round = self.serves == served
        eligible = active & same_round & alive & torch.isfinite(xyz).all(-1) & torch.isfinite(velocity).all(-1)
        first_strike = strike & same_round & ~self.return_has_strike
        self.foot_strike_rounds += first_strike.long()
        self.return_has_strike |= strike & same_round
        self.return_age = torch.where(first_strike, 0., self.return_age + self.env.step_dt)
        passed_before = self.return_gate_passed.clone()
        quality, speed, _ = return_quality(xyz[:, :2], velocity, self.source_xy, self.return_normal, self.round_half_width)
        qualified = eligible & self.return_has_strike
        self.return_kick_quality = self.kick_success_flag.float() * (.2 + .8 * quality) * qualified
        self.return_dense = (quality * speed / 3. * qualified * ~passed_before
                             * (self.return_age < RETURN_CONFIG['shaping_duration_s']))
        hit, crossed, _ = source_gate_crossing(self.previous_ball_xyz, xyz, self.source_xy,
                                        self.return_normal, self.round_half_width)
        strict, _, _ = source_gate_crossing(self.previous_ball_xyz, xyz, self.source_xy,
                                           self.return_normal, torch.full_like(self.round_half_width, .2))
        forward = (velocity * self.return_normal).sum(-1) > RETURN_CONFIG['min_forward_speed_m_s']
        new_hit = hit & qualified & forward & ~passed_before
        new_strict = strict & qualified & forward & ~passed_before
        self.return_gate_passed |= crossed & qualified
        self.return_hit |= new_hit
        self.strict_return_hit |= new_strict
        self.target_hits += new_hit.long()
        self.strict_hits += new_strict.long()
        self.return_target_pulse = new_hit.float()
        ended = active & same_round & ~self.ball_active
        self.return_miss_pulse = (ended & ~self.return_hit & alive).float()
        self._finish_rounds(ended.nonzero(as_tuple=False).flatten())
        self.previous_ball_xyz[same_round] = xyz[same_round]

    def _sync_course(self):
        previous_steps = self.course_steps
        super()._sync_course()
        if not hasattr(self, 'direction_steps'):
            return
        if self.curriculum_training:
            c = RETURN_CONFIG
            self.direction_steps = min(self.direction_steps + (self.course_steps - previous_steps)
                                       * self.direction_advance_rate, c['ramp_steps'])
            if self.course_steps - self._direction_window_start >= c['window_steps']:
                counts = self._return_counts()
                completed, hits = (a - b for a, b in zip(counts, self._direction_window_counts))
                self._direction_window_start, self._direction_window_counts = self.course_steps, counts
                self.recent_completed_rounds = completed
                self.recent_target_hit_rate = hits / max(completed, 1)
                self.direction_advance_rate = float(completed >= c['min_completed']
                    and self.recent_target_hit_rate >= c['advance_hit_rate']
                    and self.recent_recovery_share >= c['advance_recovery'])

    def curriculum_state_dict(self):
        data = super().curriculum_state_dict()
        data['return_direction'] = dict(steps=self.direction_steps, advance_rate=self.direction_advance_rate,
            recent_hit_rate=self.recent_target_hit_rate, recent_completed=self.recent_completed_rounds)
        return data

    def validate_curriculum_state_dict(self, data):
        if not isinstance(data, dict) or data.get('config') != self.course_config:
            raise ValueError('Incompatible v4 return curriculum: expected ' + REVISION)
        AgileKickballV2State.validate_curriculum_state_dict(self, data)
        direction = data.get('return_direction')
        if not isinstance(direction, dict):
            raise ValueError('Missing v4 direction curriculum')
        for key in ('steps', 'advance_rate', 'recent_hit_rate'):
            value = direction.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid v4 direction ' + key)
        if (direction['steps'] > RETURN_CONFIG['ramp_steps'] or direction['advance_rate'] not in (0., 1.)
                or direction['recent_hit_rate'] > 1. or type(direction.get('recent_completed')) is not int
                or direction['recent_completed'] < 0):
            raise ValueError('Invalid v4 direction bounds')

    def load_curriculum_state_dict(self, data):
        self.validate_curriculum_state_dict(data)
        super().load_curriculum_state_dict(data)
        direction = data['return_direction']
        self.direction_steps = float(direction['steps'])
        self.direction_advance_rate = float(direction['advance_rate'])
        self.recent_target_hit_rate = float(direction['recent_hit_rate'])
        self.recent_completed_rounds = direction['recent_completed']
        self._direction_window_start = self.course_steps
        self._direction_window_counts = self._return_counts()

    def metrics(self):
        result = {key.replace('AgileV3/', 'AgileV4/'): value for key, value in super().metrics().items()}
        completed = self.completed_rounds.sum().item()
        result.update({'AgileV4/target_half_width_m': self.target_half_width,
            'AgileV4/direction_progress': self.direction_steps / RETURN_CONFIG['ramp_steps'],
            'AgileV4/direction_advance_rate': self.direction_advance_rate,
            'AgileV4/recent_target_hit_rate': self.recent_target_hit_rate,
            'AgileV4/recent_completed_rounds': self.recent_completed_rounds,
            'AgileV4/completed_rounds': completed,
            'AgileV4/completed_target_hits': self.completed_target_hits.sum().item(),
            'AgileV4/completed_strict_20cm_hits': self.completed_strict_hits.sum().item(),
            'AgileV4/completed_foot_strikes': self.completed_foot_strikes.sum().item(),
            'AgileV4/completed_target_hit_rate': self.completed_target_hits.sum().item() / max(completed, 1),
            'AgileV4/completed_strict_20cm_hit_rate': self.completed_strict_hits.sum().item() / max(completed, 1),
            'AgileV4/foot_strike_rounds': self.foot_strike_rounds.sum().item(),
            'AgileV4/target_hits': self.target_hits.sum().item(),
            'AgileV4/strict_20cm_hits': self.strict_hits.sum().item()})
        return result


def setup_agilekickball_v4(env, env_ids, revision=REVISION, initial_exposure_steps=60000.):
    if revision != REVISION:
        raise ValueError('v4 source/config revision mismatch: ' + str(revision))
    env._kickball = AgileKickballV4State(env, initial_exposure_steps)
    print('[AgileKickball-v4] revision=' + REVISION
          + '; sender gate half-width=0.6->0.2m; v3 geometry/feedback; v3 weights-only initialization', flush=True)


def return_to_sender_dense(env):
    return env._kickball.return_dense


def return_to_sender_kick(env):
    return env._kickball.return_kick_quality


def return_to_sender_hit(env):
    return env._kickball.return_target_pulse


def return_to_sender_miss(env):
    return env._kickball.return_miss_pulse
