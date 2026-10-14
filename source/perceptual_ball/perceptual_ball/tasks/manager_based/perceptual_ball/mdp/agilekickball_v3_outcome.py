"""V2 speed/recovery, wider serves, and read-only short-horizon training labels."""
import torch
from .agilekickball_v2 import AgileKickballV2State

REVISION = "contact_outcome_20261003"
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
          + "; distance<=3m; aim<=0.35m; robot travel<=1.2m; outcome auxiliary", flush=True)


def outcome_training_state(env):
    """Privileged labels only; never routed to actor/critic. Does not tick state.

    Columns: serves, kick proxies, ball world vx/vy, robot yaw cos/sin,
    body projected gravity x/y, height above environment origin, ball active.
    Float64 preserves cumulative integer counters (float32 loses units at 2**24).
    """
    if not hasattr(env, "_kickball"):
        return torch.zeros(env.num_envs, 10, device=env.device, dtype=torch.float64)
    kb = env._kickball
    data = kb.robot.data
    w, x, y, z = data.root_quat_w.unbind(-1)
    yaw = torch.atan2(2 * (w * z + x * y), 1 - 2 * (y.square() + z.square()))
    values = (kb.serves, kb.successes, kb.ball.data.root_lin_vel_w[:, 0],
              kb.ball.data.root_lin_vel_w[:, 1], yaw.cos(), yaw.sin(),
              data.projected_gravity_b[:, 0], data.projected_gravity_b[:, 1],
              data.root_pos_w[:, 2] - kb.env_origins[:, 2], kb.ball_active)
    return torch.stack([v.to(torch.float64) for v in values], -1)
