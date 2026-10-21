"""V3 state feedback on the unchanged v2 physical task and speed curriculum."""
from .agilekickball_v2 import AgileKickballV2State

REVISION = 'feedback_stable_20261008'


class AgileKickballV3State(AgileKickballV2State):
    curriculum_checkpoint_key = 'agile_v3_state_feedback_curriculum'

    def __init__(self, env, initial_exposure_steps=0.):
        super().__init__(env)
        self.course_config['revision'] = REVISION
        self.course_config['initial_exposure_steps'] = self._validate_exposure(initial_exposure_steps)
        self.exposure_offset = float(initial_exposure_steps)
        self._sync_course()

    def validate_curriculum_state_dict(self, data):
        if (not isinstance(data, dict) or data.get('schema') != 5
                or data.get('config') != self.course_config):
            raise ValueError('Incompatible v3 curriculum; expected ' + REVISION
                             + '; old v2/outcome checkpoints cannot be resumed as this task')
        super().validate_curriculum_state_dict(data)

    def metrics(self):
        return {key.replace('AgileV2/', 'AgileV3/'): value
                for key, value in super().metrics().items()}


def setup_agilekickball_v3(env, env_ids, revision=REVISION, initial_exposure_steps=60000.):
    if revision != REVISION:
        raise ValueError('v3 source/config revision mismatch: ' + str(revision))
    env._kickball = AgileKickballV3State(env, initial_exposure_steps=initial_exposure_steps)
    print('[AgileKickball-v3] revision=' + REVISION
          + '; v2 geometry: distance<=2m; aim=0.25m; travel<=0.6m; detached predictor; initial exposure=' + str(initial_exposure_steps) + '', flush=True)
