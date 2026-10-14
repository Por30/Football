"""Stable continuous returns, speed-conditioned serves and a non-stalling speed ceiling.

The strict return detector is a kinematic proxy, NOT a contact-force measurement.
All round statistics use closed serves, including terminated rounds, as denominator.
"""
import copy
import torch
from .agilekickball import AgileKickballState
from .agilekickball_v1 import AgileKickballV1State
from .kickball_state import KickballState


class AgileKickballV2State(AgileKickballV1State):
    curriculum_checkpoint_key = 'agile_v2_recovery_curriculum'

    def __init__(self, env):
        # V1.__init__ calls virtual _sync_course before v2 fields exist.
        AgileKickballState.__init__(self, env)
        self.course_config = dict(kind='stable_return_v2', control_knots=[0, 120000, 360000, 720000, 840000],
                                  speed_knots=[.8, .8, 2., 5., 6.], bin_edges=[1., 2., 3., 4., 5.],
                                  ema_samples=512., mastery_min_closed=128, mastery_rate=.65,
                                  challenge_probability=[.05, .5], coverage_probability=[.10, .20], hold_bounds_s=[.3, .3],
                                  distance_base_m=[.5, .7], distance_per_speed=.3,
                                  timeout_s=5., anchor_radius_m=.6, return_distance_m=.5,
                                  foot_distance_m=.3, foot_outward_speed_m_s=.5)
        self.curriculum_training = True
        self.course_steps = 0
        self.course_exposure = 0.
        self._clock_steps = 0
        self._clock_anchor = env.common_step_counter
        z = lambda: torch.zeros(env.num_envs, device=env.device)
        self.round_open = z().bool()
        self.round_bin = z().long()
        self.round_speed = z()
        self.recovering = z().bool()
        self.recovery_elapsed = z()
        self.peak_disturbance = z()
        self.required_hold = z() + .3
        self.first_ready_s = z() - 1.
        self.proxy_seen = z().bool()
        self.active_kick_flag = z().bool()
        self.joint_success_flag = z().bool()
        self._pending_serve_speed = None
        self.strict_candidate = z().bool()
        self.returned = z().bool()
        self.strike_xy = torch.zeros_like(self.anchor_xy)
        self.strike_direction = torch.zeros_like(self.anchor_xy)
        self.streak = z().long()
        self.max_streak = z().long()
        self.bin_edges = torch.tensor(self.course_config['bin_edges'], device=env.device)
        self.budgets = torch.tensor([.5, 1., 2., 5.], device=env.device)
        self.closed = torch.zeros(6, dtype=torch.long, device=env.device)
        self.joint_success = torch.zeros_like(self.closed)
        self.censored = torch.zeros_like(self.closed)
        self.cdf_success = torch.zeros(6, 4, dtype=torch.long, device=env.device)
        self.recovery_sum = torch.zeros(6, device=env.device)
        self.train_closed = torch.zeros_like(self.closed)
        self.train_ema = torch.zeros(6, device=env.device)
        self.sampled = torch.zeros_like(self.closed)
        self.challenge_serves = torch.zeros((), dtype=torch.long, device=env.device)
        self.above_five_serves = torch.zeros_like(self.challenge_serves)
        self._sync_course()

    def _sync_course(self):
        if self.curriculum_training:
            self.course_steps = self._clock_steps + max(0, self.env.common_step_counter - self._clock_anchor)
        knots, speeds = self.course_config['control_knots'], self.course_config['speed_knots']
        upper = speeds[-1]
        for lo, hi, v0, v1 in zip(knots[:-1], knots[1:], speeds[:-1], speeds[1:]):
            if self.course_steps <= hi:
                upper = v0 + (v1 - v0) * max(0., (self.course_steps - lo) / (hi - lo))
                break
        self.scheduled_upper = upper
        self.serve_speed_range = self.serve_speed_override or (.4, upper)
        # Public range describes the envelope; each real serve uses its sampled speed.
        max_speed = self.serve_speed_range[1]
        self.serve_distance_range = (.5, .7 + .3 * min(max(max_speed - .8, 0.), 5.2))

    def _teacher(self):
        passed = ((self.train_closed >= self.course_config['mastery_min_closed'])
                  & (self.train_ema >= self.course_config['mastery_rate']))
        contiguous = passed.long().cumprod(0).sum()
        bounds = torch.tensor([.4, 1., 2., 3., 4., 5., 6.], device=self.env.device)
        frontier = bounds[contiguous]
        # Equal speed-bin weighting over observed bins, not a low-speed-dominated average.
        seen = self.train_closed > 0
        rate = (self.train_ema * seen).sum() / seen.sum().clamp(min=1)
        return frontier, .05 + .45 * rate

    def _sample_serve_speed(self, env_ids):
        if self._pending_serve_speed is not None:
            return self._pending_serve_speed
        self._sync_course()
        n, device = len(env_ids), self.env.device
        low, upper = self.serve_speed_range
        if self.serve_speed_override is not None:
            speed = low + torch.rand(n, device=device) * (upper - low)
            challenge = torch.zeros(n, dtype=torch.bool, device=device)
        else:
            frontier, probability = self._teacher()
            practice_upper = (frontier + .5).clamp(min=.8, max=upper)
            draw = torch.rand(n, device=device)
            challenge = draw < probability
            coverage_probability = .10 + .10 * ((probability - .05) / .45)
            coverage = (draw >= probability) & (draw < probability + coverage_probability)
            practice = low + torch.rand(n, device=device) * (practice_upper - low)
            hard_low = max(low, upper - 1.)
            hard = hard_low + torch.rand(n, device=device) * (upper - hard_low)
            broad = low + torch.rand(n, device=device) * (upper - low)
            speed = torch.where(challenge, hard, torch.where(coverage, broad, practice))
        self.round_speed[env_ids] = speed
        # right=True: exact 1/2/3/4/5 m/s goes to the next bin; last bin is >=5.
        bins = torch.bucketize(speed, self.bin_edges, right=True)
        self.round_bin[env_ids] = bins
        self.sampled += torch.bincount(bins, minlength=6)
        self.challenge_serves += challenge.sum()
        self.above_five_serves += (speed > 5.).sum()
        return speed

    def balanced(self):
        return (AgileKickballV1State.balanced(self)
                & ((self.robot.data.root_pos_w[:, :2] - self.anchor_xy).norm(dim=-1) < .6))

    def _disturbance(self):
        q = self.robot.data
        return torch.stack((q.projected_gravity_b[:, :2].norm(dim=-1) / .15,
                            q.root_lin_vel_w.norm(dim=-1) / .25,
                            q.root_ang_vel_b.norm(dim=-1) / .5), -1).amax(-1)

    def _settle(self, env_ids, recovered=False, censored=False):
        ids = env_ids[self.round_open[env_ids]]
        if not len(ids):
            return
        bins = self.round_bin[ids]
        count = torch.bincount(bins, minlength=6)
        success = (self.strict_candidate[ids] & self.returned[ids]
                   & (self.first_ready_s[ids] >= 0)) if recovered else torch.zeros_like(ids, dtype=torch.bool)
        if censored:
            self.censored += count
        else:
            win = torch.bincount(bins[success], minlength=6)
            self.closed += count
            self.joint_success += win
            self.recovery_sum.index_add_(0, bins[success], self.first_ready_s[ids][success])
            for i, budget in enumerate(self.budgets):
                within = success & (self.first_ready_s[ids] <= budget)
                self.cdf_success[:, i] += torch.bincount(bins[within], minlength=6)
            if self.curriculum_training:
                # Batch-order invariant exponential update, 512 closed serves e-folding scale.
                alpha = -torch.expm1(-count.float() / self.course_config['ema_samples'])
                self.train_ema += alpha * (win.float() / count.clamp(min=1) - self.train_ema)
                self.train_closed += count
        if recovered and not censored:
            self.joint_success_flag[ids] = success
        self.streak[ids] = torch.where(success & (not censored), self.streak[ids] + 1, 0)
        self.max_streak[ids] = torch.maximum(self.max_streak[ids], self.streak[ids])
        self.round_open[ids] = False

    def reset(self, env_ids):
        # Tick closes natural terminations before reset; explicit resets censor unfinished rounds.
        self._settle(env_ids, censored=True)
        self.streak[env_ids] = 0
        self.active_kick_flag[env_ids] = False
        self.joint_success_flag[env_ids] = False
        super().reset(env_ids)

    def _ready_to_serve(self, env_ids):
        ready = (~self.ball_active[env_ids] & self.recovering[env_ids]
                 & (self.steps_since_ball_ended[env_ids] >= 20)
                 & (self.stable_elapsed[env_ids] >= self.required_hold[env_ids])
                 & (self.wait_elapsed[env_ids] >= self.serve_cooldown)
                 & (self.wait_elapsed[env_ids] < self.recovery_timeout)
                 & self.balanced()[env_ids])
        reset = getattr(self.env, 'reset_buf', None)
        if reset is not None:
            ready &= ~reset[env_ids].bool()
        return env_ids[ready]

    def _serve(self, env_ids):
        ids = env_ids if self._initializing else self._ready_to_serve(env_ids)
        if not len(ids):
            return
        if not self._initializing:
            self._settle(ids, recovered=True)
        self._sync_course()  # distance also belongs to the current control-step curriculum
        speed = self._sample_serve_speed(ids)
        nominal_distance = self.serve_distance_range
        extra_distance = .3 * (speed - .8).clamp(0., 5.2)
        self.serve_distance_range = (.5 + extra_distance, .7 + extra_distance)
        self._pending_serve_speed = speed
        try:
            # Parent draws a per-env distance using tensor bounds, then consumes the SAME speeds.
            KickballState._serve(self, ids)
        finally:
            self._pending_serve_speed = None
            self.serve_distance_range = nominal_distance
        self.serves[ids] += 1
        if self._initializing:
            self.initial_serves[ids] += 1
        else:
            self.recovered_serves[ids] += 1
        self.round_open[ids] = True
        self.proxy_seen[ids] = False
        self.recovering[ids] = False
        self.recovery_elapsed[ids] = self.stable_elapsed[ids] = self.wait_elapsed[ids] = 0.
        self.peak_disturbance[ids] = self._disturbance()[ids]
        self.required_hold[ids] = .3
        self.first_ready_s[ids] = -1.
        self.strict_candidate[ids] = self.returned[ids] = False

    def tick(self):
        if self.last_tick == self.env.common_step_counter:
            return
        self.last_tick = self.env.common_step_counter
        self.active_kick_flag.zero_()
        self.joint_success_flag.zero_()
        self._sync_course()
        alive = ~self.env.reset_buf.bool()
        status = self.observation_status()
        self.incoming_steps += status[:, 1] * alive
        self.near_steps += status[:, 2] * alive
        self.peak_disturbance = torch.maximum(self.peak_disturbance, self._disturbance())
        self.required_hold.fill_(.3)
        self.recovery_elapsed += self.recovering * self.env.step_dt
        self.wait_elapsed = torch.where(~self.ball_active, self.wait_elapsed + self.env.step_dt, 0.)
        self.stable_elapsed = torch.where(~self.ball_active & self.balanced(),
                                          self.stable_elapsed + self.env.step_dt, 0.)
        # Invalidate transient readiness: the reported recovery must persist until serve.
        not_ready = self.recovering & (self.stable_elapsed < self.required_hold)
        self.first_ready_s[not_ready] = -1.
        first = self.recovering & (self.first_ready_s < 0) & (self.stable_elapsed >= self.required_hold)
        self.first_ready_s[first] = self.recovery_elapsed[first]
        # Read OLD ball before parent tick can teleport it. Later stability still gates settlement.
        displacement = ((self.ball.data.root_pos_w[:, :2] - self.strike_xy) * self.strike_direction).sum(-1)
        self.returned |= self.strict_candidate & (displacement >= .5)
        failed = (self.env.reset_buf.bool() | (~self.ball_active & (self.wait_elapsed >= self.recovery_timeout)))
        self._settle(failed.nonzero().flatten())
        active_before = self.ball_active.clone()
        KickballState.tick(self)
        ended = active_before & ~self.ball_active
        self.wait_elapsed[ended] = self.stable_elapsed[ended] = 0.
        self.kick_success_flag &= alive & ~failed
        self.successes += (self.kick_success_flag & ~self.proxy_seen).long()
        self.proxy_seen |= self.kick_success_flag
        xy = self.ball.data.root_pos_w[:, :2]
        direction = xy - self.anchor_xy
        direction = direction / direction.norm(dim=-1, keepdim=True).clamp(min=1.e-6)
        dist, nearest = self.foot_ball_dist.min(-1)
        feet_v = self.robot.data.body_link_lin_vel_w[:, self.foot_body_ids, :2]
        foot_v = feet_v[torch.arange(self.env.num_envs, device=self.env.device), nearest]
        relative_outward = ((foot_v - self.robot.data.root_lin_vel_w[:, :2]) * direction).sum(-1)
        strict = self.kick_success_flag & (dist < .3) & (relative_outward > .5)
        self.active_kick_flag.copy_(strict)
        self.strict_candidate |= strict
        self.strike_xy[strict] = xy[strict]
        self.strike_direction[strict] = direction[strict]
        # Raw collisions remain diagnostic; only active foot returns earn kick status/rewards.
        self.ball_kicked &= self.strict_candidate
        self.just_missed |= ended & ~self.strict_candidate
        trigger = self.round_open & ~self.recovering & (self.active_kick_flag | ended)
        self.recovering[trigger] = True
        self.recovery_elapsed[trigger] = self.stable_elapsed[trigger] = 0.
        self.first_ready_s[trigger] = -1.


    def curriculum_state_dict(self):
        self._sync_course()
        if self.curriculum_training:
            self.course_exposure = self.exposure_steps
        return dict(schema=4, config=copy.deepcopy(self.course_config), control_steps=self.course_steps,
                    exposure_steps=self.course_exposure, train_closed=self.train_closed.tolist(),
                    train_ema=self.train_ema.tolist())

    def validate_curriculum_state_dict(self, data):
        if not isinstance(data, dict) or data.get('schema') != 4 or data.get('config') != self.course_config:
            raise ValueError('Incompatible v2 recovery curriculum. Start fresh (no --resume).')
        if type(data.get('control_steps')) is not int or data['control_steps'] < 0:
            raise ValueError('control_steps must be a nonnegative integer')
        self._validate_exposure(data.get('exposure_steps'))
        count, ema = data.get('train_closed'), data.get('train_ema')
        if not isinstance(count, list) or len(count) != 6 or any(type(x) is not int or x < 0 or x > 2**60 for x in count):
            raise ValueError('Invalid closed-round counts')
        if not isinstance(ema, list) or len(ema) != 6:
            raise ValueError('Invalid recovery EMA')
        for x in ema:
            if self._validate_exposure(x) > 1.:
                raise ValueError('Invalid recovery EMA')

    def load_curriculum_state_dict(self, data):
        self.validate_curriculum_state_dict(data)
        self.course_steps = self._clock_steps = data['control_steps']
        self._clock_anchor = self.env.common_step_counter
        self.course_exposure = self.exposure_offset = data['exposure_steps']
        self.incoming_steps.zero_()
        self.train_closed.copy_(torch.tensor(data['train_closed'], device=self.env.device))
        self.train_ema.copy_(torch.tensor(data['train_ema'], device=self.env.device))
        self._sync_course()

    def metrics(self):
        result = AgileKickballState.metrics(self)
        frontier, probability = self._teacher()
        denominator = self.closed.clamp(min=1)
        bins = torch.stack((self.sampled.float(), self.closed.float(), self.joint_success.float(),
                            (self.closed-self.joint_success).float(), self.censored.float(),
                            self.joint_success/denominator, self.train_ema,
                            self.recovery_sum/self.joint_success.clamp(min=1),
                            *(self.cdf_success[:, j]/denominator for j in range(4))), -1).cpu().tolist()
        names = ['served', 'closed', 'joint_success', 'failure', 'censored', 'joint_rate', 'training_ema',
                 'successful_recovery_mean_s', 'joint_within_0.5s', 'joint_within_1s', 'joint_within_2s', 'joint_within_5s']
        for i, row in enumerate(bins):
            for name, value in zip(names, row):
                result[f'AgileV2/bin{i}/{name}'] = value
        result.update({'AgileV2/speed_upper_m_s': self.serve_speed_range[1],
                       'AgileV2/control_steps': self.course_steps,
                       'AgileV2/empirical_mastered_upper_m_s': frontier.item(),
                       'AgileV2/challenge_probability': probability.item(),
                       'AgileV2/above_5m_s_serves': self.above_five_serves.item(),
                       'AgileV2/challenge_serves': self.challenge_serves.item(),
                       'AgileV2/distance_envelope_max_m': self.serve_distance_range[1],
                       'AgileV2/joint_success_pulse_count': self.joint_success_flag.sum().item(),
                       'AgileV2/open_rounds': self.round_open.sum().item(),
                       'AgileV2/max_joint_streak': self.max_streak.max().item(),
                       'AgileV2/current_joint_streak_mean': self.streak.float().mean().item(),
                       'AgileV2/required_hold_mean_s': self.required_hold.mean().item(),
                       'AgileV2/peak_normalized_disturbance_mean': self.peak_disturbance.mean().item(),
                       'AgileV2/anchor_drift_mean_m': (self.robot.data.root_pos_w[:, :2]-self.anchor_xy).norm(dim=-1).mean().item()})
        return result


def setup_agilekickball_v2(env, env_ids):
    env._kickball = AgileKickballV2State(env)


def recovery_timed_out(env):
    kb = env._kickball
    # Restore v1: the five-second recovery deadline starts AFTER the ball ends.
    return ~kb.ball_active & (kb.wait_elapsed >= kb.recovery_timeout)


def active_kick_bonus(env):
    return env._kickball.active_kick_flag.float()


def stable_return_bonus(env):
    """Paid once when the SAME actively returned ball is settled and the next is served."""
    return env._kickball.joint_success_flag.float()


def failed_episode(env):
    """Physical/recovery failures, excluding a normal episode time limit."""
    return env.termination_manager.terminated.float()


def stable_return_speed(env):
    from .rewards import kick_return_task
    return kick_return_task(env) * env._kickball.strict_candidate.float()


def stand_until_kick_window(env, target_height=.8):
    from .rewards import stand_task
    kb = env._kickball
    distance = (kb.ball.data.root_pos_w[:, :2] - kb.robot.data.root_pos_w[:, :2]).norm(dim=-1)
    preparing_close = kb.ball_active & ~kb.ball_kicked & (distance < .8)
    return stand_task(env, target_height=target_height) * torch.where(preparing_close, .25, 1.)
