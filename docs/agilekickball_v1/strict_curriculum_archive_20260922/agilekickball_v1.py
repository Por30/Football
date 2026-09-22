"""Success-window curriculum, with per-serve attribution and recovery-time settlement."""
import copy
import math
import torch
from .agilekickball import AgileKickballState

STAGE_UPPERS = (.8, 1.2, 1.6, 2., 2.5, 3., 3.5, 4., 4.5, 5.)


class AgileKickballV1State(AgileKickballState):
    def __init__(self, env, success_threshold=.8, window_size=4096, min_challenge_count=1024,
                 required_windows=2, min_stage_steps=1000):
        if not math.isfinite(success_threshold) or not 0 < success_threshold <= 1:
            raise ValueError('success_threshold must be in (0, 1]')
        for value in (window_size, min_challenge_count, required_windows, min_stage_steps):
            if type(value) is not int or value <= 0:
                raise ValueError('Curriculum counts must be positive integers')
        if min_challenge_count > window_size:
            raise ValueError('min_challenge_count must not exceed window_size')
        super().__init__(env)
        self.course_config = dict(success_threshold=success_threshold, window_size=window_size,
            min_challenge_count=min_challenge_count, required_windows=required_windows,
            min_stage_steps=min_stage_steps, stage_uppers=list(STAGE_UPPERS), min_speed=.4,
            challenge_probability=.5, distance_range=[1.3, 2.], return_progress=.5, active_foot_speed=.5)
        self.curriculum_training = True
        self.stage = self.stage_steps = self.passing_windows = 0
        self.window = self._empty_window()
        self.last_window = self._empty_window()
        self.settled_total = self.strict_success_total = self.truncated_on_load = 0
        self.serve_distance_range = (1.3, 2.)
        n, device = env.num_envs, env.device
        self.round_open = torch.zeros(n, dtype=torch.bool, device=device)
        self.round_stage = torch.zeros(n, dtype=torch.long, device=device)
        self.round_challenge = torch.zeros_like(self.round_open)
        self.round_speed = torch.zeros(n, device=device)
        self.candidate = torch.zeros_like(self.round_open)
        self.returned = torch.zeros_like(self.round_open)
        self.strike_xy = torch.zeros(n, 2, device=device)
        self.strike_direction = torch.zeros_like(self.strike_xy)
        self._sync_course()

    @staticmethod
    def _empty_window():
        return dict(total=0, successes=0, challenge=0, challenge_successes=0)

    def _sync_course(self):
        self.serve_speed_range = (.4, STAGE_UPPERS[self.stage])
        self.serve_distance_range = (1.3, 2.)

    def _sample_serve_speed(self, env_ids):
        if self.serve_speed_override is not None:
            speed = super()._sample_serve_speed(env_ids)
            self.round_speed[env_ids] = speed
            self.round_challenge[env_ids] = False  # explicit eval range is not a training stratum
            return speed
        n = len(env_ids)
        challenge = torch.ones(n, dtype=torch.bool, device=self.env.device) if self.stage == 0 else torch.rand(n, device=self.env.device) < .5
        upper = STAGE_UPPERS[self.stage]
        previous = STAGE_UPPERS[self.stage-1] if self.stage else .4
        low = torch.where(challenge, previous, .4)
        high = torch.where(challenge, upper, previous)
        speed = low + (high-low) * torch.rand(n, device=self.env.device)
        self.round_challenge[env_ids] = challenge
        self.round_speed[env_ids] = speed
        return speed

    def _settle(self, env_ids, success):
        live = self.round_open[env_ids]
        ids, success = env_ids[live], success[live].bool()
        if not len(ids):
            return
        success &= ~self.env.reset_buf[ids].bool() if hasattr(self.env, 'reset_buf') else True
        self.settled_total += len(ids)
        self.strict_success_total += int(success.sum())
        if self.curriculum_training:
            current = self.round_stage[ids] == self.stage
            challenge = self.round_challenge[ids] & current
            self.window['total'] += int(current.sum())
            self.window['successes'] += int((current & success).sum())
            self.window['challenge'] += int(challenge.sum())
            self.window['challenge_successes'] += int((challenge & success).sum())
        self.round_open[ids] = False

    def reset(self, env_ids):
        # An explicit episode reset terminates any unfinished ball, even after a kick.
        self._settle(env_ids, torch.zeros(len(env_ids), dtype=torch.bool, device=self.env.device))
        super().reset(env_ids)  # dynamic _serve creates the NEW round; do not clear it afterwards

    def _serve(self, env_ids):
        ids = env_ids if self._initializing else self._ready_to_serve(env_ids)
        if not len(ids):
            return
        # Only actual recovery-gated serves settle an old round. Do this before sampling,
        # teleporting, or clearing the old candidate. Promotion occurs only at tick end.
        self._settle(ids, self.candidate[ids] & self.returned[ids])
        super()._serve(ids)
        self.round_open[ids] = True
        self.round_stage[ids] = self.stage
        self.candidate[ids] = False
        self.returned[ids] = False

    def _advance_window(self):
        c, w = self.course_config, self.window
        if not self.curriculum_training or w['total'] < c['window_size'] or w['challenge'] < c['min_challenge_count']:
            return
        passed = (w['successes']/w['total'] >= c['success_threshold']
                  and w['challenge_successes']/w['challenge'] >= c['success_threshold'])
        self.last_window = w.copy()
        self.window = self._empty_window()
        self.passing_windows = self.passing_windows + 1 if passed else 0
        if (self.passing_windows >= c['required_windows'] and self.stage_steps >= c['min_stage_steps']
                and self.stage < len(STAGE_UPPERS)-1):
            self.stage += 1
            self.stage_steps = self.passing_windows = 0
            self.last_window = self._empty_window()
            self._sync_course()

    def tick(self):
        if self.last_tick == self.env.common_step_counter:
            return
        if self.curriculum_training:
            self.stage_steps += 1
        # Read old ball before parent tick can serve/teleport a replacement.
        displacement = self.ball.data.root_pos_w[:, :2] - self.strike_xy
        self.returned |= self.round_open & self.candidate & ((displacement*self.strike_direction).sum(-1) >= .5)
        super().tick()
        direction = self.ball.data.root_pos_w[:, :2] - self.anchor_xy
        direction /= direction.norm(dim=-1, keepdim=True).clamp(min=1.e-6)
        nearest = self.foot_ball_dist.argmin(-1)
        foot_vel = self.robot.data.body_link_lin_vel_w[:, self.foot_body_ids, :2]
        foot_vel = foot_vel[torch.arange(self.env.num_envs, device=self.env.device), nearest]
        active_speed = ((foot_vel-self.robot.data.root_lin_vel_w[:, :2])*direction).sum(-1)
        candidate = (self.kick_success_flag & self.round_open & ~self.candidate
                     & (self.foot_ball_dist.amin(-1) < .3) & (active_speed > .5))
        self.candidate[candidate] = True
        self.strike_xy[candidate] = self.ball.data.root_pos_w[candidate, :2]
        self.strike_direction[candidate] = direction[candidate]
        terminated = self.env.reset_buf.nonzero().flatten()
        self._settle(terminated, torch.zeros(len(terminated), dtype=torch.bool, device=self.env.device))
        self._advance_window()

    def curriculum_state_dict(self):
        return copy.deepcopy(dict(schema=1, config=self.course_config, stage=self.stage,
            stage_steps=self.stage_steps, passing_windows=self.passing_windows, window=self.window,
            last_window=self.last_window, open_at_save=int(self.round_open.sum())))

    def load_curriculum_state_dict(self, data):
        if data is None:  # v0 policy/optimizer initialization, never infer success from exposure.
            data = dict(schema=1, config=self.course_config, stage=0, stage_steps=0,
                        passing_windows=0, window=self._empty_window(), last_window=self._empty_window(), open_at_save=0)
        if data.get('schema') != 1 or data.get('config') != self.course_config:
            raise ValueError('Incompatible v1 curriculum schema/config')
        for key in ('stage', 'stage_steps', 'passing_windows', 'open_at_save'):
            if type(data.get(key)) is not int or data[key] < 0:
                raise ValueError('Invalid v1 curriculum counter: '+key)
        if data['stage'] >= len(STAGE_UPPERS):
            raise ValueError('Invalid v1 stage')
        for key in ('window', 'last_window'):
            w = data.get(key, {})
            if set(w) != set(self._empty_window()) or any(type(v) is not int or v < 0 for v in w.values()):
                raise ValueError('Invalid v1 window')
            if not (w['challenge_successes'] <= w['challenge'] <= w['total'] and
                    w['challenge_successes'] <= w['successes'] <= w['total'] and
                    w['successes']-w['challenge_successes'] <= w['total']-w['challenge']):
                raise ValueError('Inconsistent v1 window counts')
        self.stage, self.stage_steps, self.passing_windows = data['stage'], data['stage_steps'], data['passing_windows']
        self.window, self.last_window = copy.deepcopy(data['window']), copy.deepcopy(data['last_window'])
        self.truncated_on_load = data['open_at_save']
        # No physics snapshot: do not transfer a saved in-flight candidate to a fresh ball.
        self.round_open.zero_(); self.candidate.zero_(); self.returned.zero_()
        self._sync_course()

    def metrics(self):
        result = super().metrics()
        result.update({'AgileV1/stage': self.stage, 'AgileV1/speed_upper_m_s': self.serve_speed_range[1],
            'AgileV1/stage_steps': self.stage_steps, 'AgileV1/passing_windows': self.passing_windows,
            'AgileV1/settled_rounds': self.settled_total, 'AgileV1/curriculum_proxy_successes': self.strict_success_total,
            'AgileV1/open_rounds': int(self.round_open.sum()), 'AgileV1/truncated_on_load': self.truncated_on_load,
            'AgileV1/updates_enabled': int(self.curriculum_training)})
        for prefix, w in [('window', self.window), ('last_window', self.last_window)]:
            result.update({f'AgileV1/{prefix}_{k}': v for k, v in w.items()})
            if w['total']:
                result[f'AgileV1/{prefix}_success_rate'] = w['successes']/w['total']
            if w['challenge']:
                result[f'AgileV1/{prefix}_challenge_success_rate'] = w['challenge_successes']/w['challenge']
        return result


def setup_agilekickball_v1(env, env_ids, success_threshold=.8, window_size=4096,
                          min_challenge_count=1024, required_windows=2, min_stage_steps=1000):
    env._kickball = AgileKickballV1State(env, success_threshold, window_size,
                                      min_challenge_count, required_windows, min_stage_steps)


def success_course_speed(env, env_ids):
    """Read-only manager log; outcomes are consumed once at the end of each tick."""
    return env._kickball.serve_speed_range[1]
