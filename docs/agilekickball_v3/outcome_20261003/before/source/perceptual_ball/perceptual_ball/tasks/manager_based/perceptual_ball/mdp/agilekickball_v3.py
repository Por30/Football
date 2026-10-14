"""V2 speed and recovery with a wider, longer serving area."""
from .agilekickball_v2 import AgileKickballV2State

REVISION = "wide_serve_aim035_20260928"
MAX_ROBOT_ANCHOR_DISTANCE = 1.2


class AgileKickballV3State(AgileKickballV2State):
    curriculum_checkpoint_key = "agile_v3_wide_serve_curriculum"
    # Leave outbound room beyond the longest serve (including float roundoff).
    ball_end_max_distance = 4.0

    def __init__(self, env):
        super().__init__(env)
        # Same serialization format as v2, but a distinct task key and config.
        self.course_config.update(revision=REVISION, spatial_bounds={
            "distance_start_m": [.5, .7], "distance_final_m": [1.3, 3.],
            "aim_half_width_start_m": .25, "aim_half_width_final_m": .35,
            "robot_anchor_max_m": MAX_ROBOT_ANCHOR_DISTANCE,
            "ball_end_max_distance_m": self.ball_end_max_distance,
        })

    def _sync_course(self):
        super()._sync_course()
        progress = min(self.course_exposure / self.course_config["distance_steps"], 1.)
        self.serve_distance_range = (.5 + .8 * progress, .7 + 2.3 * progress)
        half_width = .25 + .1 * progress
        self.serve_aim_offset_range = (-half_width, half_width)

    def validate_curriculum_state_dict(self, data):
        if (not isinstance(data, dict) or data.get("schema") != 5
                or data.get("config") != self.course_config):
            raise ValueError("Incompatible v3 curriculum; expected " + REVISION
                             + "; start fresh without --resume for older task/config checkpoints.")
        super().validate_curriculum_state_dict(data)

    def metrics(self):
        result = {key.replace("AgileV2/", "AgileV3/"): value
                  for key, value in super().metrics().items()}
        result.update({"AgileV3/aim_half_width_m": self.serve_aim_offset_range[1],
                       "AgileV3/robot_anchor_max_m": MAX_ROBOT_ANCHOR_DISTANCE})
        return result


def setup_agilekickball_v3(env, env_ids, revision=REVISION):
    if revision != REVISION:
        raise ValueError("v3 source/config revision mismatch: " + str(revision))
    env._kickball = AgileKickballV3State(env)
    print("[AgileKickball-v3] revision=" + REVISION
          + "; distance<=3m; aim<=0.35m; robot travel<=1.2m", flush=True)
