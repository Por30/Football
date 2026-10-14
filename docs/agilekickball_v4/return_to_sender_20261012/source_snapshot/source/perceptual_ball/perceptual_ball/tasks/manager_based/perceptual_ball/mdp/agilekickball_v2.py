"""V1 ball rounds unchanged; a recovery-gated incoming-speed extension to 6 m/s."""
import copy
from .agilekickball import AgileKickballState
from .agilekickball_v1 import AgileKickballV1State

REVISION = 'v1_speed_only_20260925'


class AgileKickballV2State(AgileKickballV1State):
    curriculum_checkpoint_key = 'agile_v2_recovery_curriculum'

    def __init__(self, env):
        # V1's constructor calls the virtual _sync_course before v2 fields exist.
        AgileKickballState.__init__(self, env)
        self.course_config = dict(revision=REVISION, bootstrap_steps=240_000,
            distance_steps=60_000, window_steps=6_000, min_serves=128,
            unlock_recovery=.8, unlock_kick_proxy=.6, pause_recovery=.5,
            extension_steps=288_000, speed_bounds=[.4, .8, 2., 6.])
        self.curriculum_training = True
        self.course_exposure = 0.
        self.course_steps = 0
        self.extension_unlocked = False
        self.extension_start_upper = .8
        self.extension_steps = 0.
        self.advance_rate = 0.
        self.recent_recovery_share = 0.
        self.recent_kick_proxy_share = 0.
        self.recent_serves = 0
        self.recent_window_steps = 0
        self._last_control_step = int(env.common_step_counter)
        self._window_start = 0
        self._window_counts = self._counts()
        self._sync_course()

    def _counts(self):
        return tuple(int(x.sum().item()) for x in
                     (self.serves, self.recovered_serves, self.successes))

    def _bootstrap_upper(self):
        return .8 + 1.2 * min(self.course_exposure, self.course_config['bootstrap_steps']) / self.course_config['bootstrap_steps']

    def _measure_window(self):
        c = self.course_config
        elapsed = self.course_steps - self._window_start
        if elapsed < c['window_steps']:
            return
        counts = self._counts()
        served, recovered, kicked = (a - b for a, b in zip(counts, self._window_counts))
        self._window_start, self._window_counts = self.course_steps, counts
        self.recent_serves, self.recent_window_steps = served, elapsed
        # These are separate marginal shares, not per-ball joint success rates.
        self.recent_recovery_share = recovered / max(served, 1)
        self.recent_kick_proxy_share = kicked / max(served, 1)
        if served < c['min_serves']:
            self.advance_rate = 0.
            return
        recovery = min(max(self.recent_recovery_share, 0.), 1.)
        kick = min(max(self.recent_kick_proxy_share, 0.), 1.)
        if (not self.extension_unlocked and self.course_exposure >= c['distance_steps']
                and recovery >= c['unlock_recovery'] and kick >= c['unlock_kick_proxy']):
            self.extension_unlocked = True
            self.extension_start_upper = self._bootstrap_upper()
        if self.extension_unlocked:
            self.advance_rate = min(max((recovery - c['pause_recovery']) /
                (c['unlock_recovery'] - c['pause_recovery']), 0.), 1.) * min(kick / c['unlock_kick_proxy'], 1.)

    def _sync_course(self):
        now = int(self.env.common_step_counter)
        delta = max(now - self._last_control_step, 0)
        self._last_control_step = now
        c = self.course_config
        if self.curriculum_training:
            self.course_exposure = self._validate_exposure(self.exposure_steps)
            self.course_steps += delta
            if self.extension_unlocked:
                self.extension_steps = min(self.extension_steps + delta * self.advance_rate, c['extension_steps'])
            self._measure_window()  # new rate applies only to future steps
        progress = self.extension_steps / c['extension_steps']
        self.course_upper = (self.extension_start_upper + (6. - self.extension_start_upper) * progress
                             if self.extension_unlocked else self._bootstrap_upper())
        self.serve_speed_range = self.serve_speed_override or (.4, self.course_upper)
        p = min(self.course_exposure / c['distance_steps'], 1.)
        self.serve_distance_range = (.5 + .8 * p, .7 + 1.3 * p)

    def curriculum_state_dict(self):
        self._sync_course()
        return dict(schema=5, config=copy.deepcopy(self.course_config),
            exposure_steps=self.course_exposure, control_steps=self.course_steps,
            extension_unlocked=self.extension_unlocked, extension_start_upper=self.extension_start_upper,
            extension_steps=self.extension_steps, advance_rate=self.advance_rate,
            recent_recovery_share=self.recent_recovery_share, recent_kick_proxy_share=self.recent_kick_proxy_share,
            recent_serves=self.recent_serves, recent_window_steps=self.recent_window_steps)

    def validate_curriculum_state_dict(self, data):
        if not isinstance(data, dict) or data.get('schema') != 5 or data.get('config') != self.course_config:
            raise ValueError('Incompatible v2 curriculum schema/config. Expected schema5 ' + REVISION +
                             '; start fresh without --resume for old v2 checkpoints.')
        for key in ('control_steps', 'recent_serves', 'recent_window_steps'):
            if type(data.get(key)) is not int or data[key] < 0:
                raise ValueError(key + ' must be a nonnegative integer')
        for key in ('exposure_steps', 'extension_steps', 'extension_start_upper', 'advance_rate',
                    'recent_recovery_share', 'recent_kick_proxy_share'):
            self._validate_exposure(data.get(key))
        if type(data.get('extension_unlocked')) is not bool:
            raise ValueError('extension_unlocked must be bool')
        if not (.8 <= data['extension_start_upper'] <= 2. and 0 <= data['advance_rate'] <= 1.
                and data['extension_steps'] <= self.course_config['extension_steps']):
            raise ValueError('Invalid v2 extension bounds')
        if not data['extension_unlocked'] and (data['extension_steps'] != 0. or data['advance_rate'] != 0.):
            raise ValueError('Locked extension cannot advance')
        if data['extension_unlocked'] and data['exposure_steps'] < self.course_config['distance_steps']:
            raise ValueError('Extension unlocked before bootstrap exposure')

    def load_curriculum_state_dict(self, data):
        self.validate_curriculum_state_dict(data)
        self.course_exposure = self.exposure_offset = float(data['exposure_steps'])
        self.incoming_steps.zero_()
        self.course_steps = data['control_steps']
        for key in ('extension_unlocked', 'extension_start_upper', 'extension_steps', 'advance_rate',
                    'recent_recovery_share', 'recent_kick_proxy_share', 'recent_serves', 'recent_window_steps'):
            setattr(self, key, data[key])
        # Physics and round counters belong to the new environment. Discard the partial window.
        self._last_control_step = int(self.env.common_step_counter)
        self._window_start, self._window_counts = self.course_steps, self._counts()
        self._sync_course()

    def metrics(self):
        # Like v1, logging does not change the reset-time curriculum update schedule.
        result = AgileKickballState.metrics(self)
        result.update({'AgileV2/schema': 5, 'AgileV2/speed_upper_m_s': self.serve_speed_range[1],
            'AgileV2/course_upper_m_s': self.course_upper,
            'AgileV2/extension_unlocked': int(self.extension_unlocked),
            'AgileV2/advance_rate': self.advance_rate,
            'AgileV2/extension_progress': self.extension_steps / self.course_config['extension_steps'],
            'AgileV2/recent_recovered_serve_share': self.recent_recovery_share,
            'AgileV2/recent_kick_proxy_share': self.recent_kick_proxy_share,
            'AgileV2/recent_serves': self.recent_serves,
            'AgileV2/recent_window_control_steps': self.recent_window_steps,
            'AgileV2/course_control_steps': self.course_steps,
            'AgileV2/distance_min_m': self.serve_distance_range[0],
            'AgileV2/distance_max_m': self.serve_distance_range[1],
            'AgileV2/updates_enabled': int(self.curriculum_training)})
        return result


def setup_agilekickball_v2(env, env_ids, revision=REVISION):
    if revision != REVISION:
        raise ValueError('v2 source/config revision mismatch: ' + str(revision))
    env._kickball = AgileKickballV2State(env)
    print('[AgileKickball-v2] revision=' + REVISION + '; schema=5; v1 rewards and recovery', flush=True)
