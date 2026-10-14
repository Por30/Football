"""One-touch directed return and recovery. Every served ball is settled exactly once."""
import torch
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import quat_apply_inverse
from .kickball_state import KickballState, _rand_range

PREPARE, RECOVER, READY, WAIT = range(4)


class SoccerV3State(KickballState):
    def __init__(self, env, robot_cfg, ball_cfg, recovery_timeout=2.0, stable_duration=0.3,
                 target_distance=2.0, target_half_width=0.6, max_serve_speed=0.8):
        super().__init__(env, robot_cfg, ball_cfg, rsi_probability=0.,
                         strike_gated_return_speed=True, require_foot_contact=True)
        n, device = env.num_envs, env.device
        self.phase = torch.full((n,), WAIT, device=device, dtype=torch.long)
        self.elapsed = torch.zeros(n, device=device)
        self.stable_elapsed = torch.zeros(n, device=device)
        self.target_distance, self.target_half_width = target_distance, target_half_width
        self.recovery_timeout, self.stable_duration = recovery_timeout, stable_duration
        self.max_serve_speed = max_serve_speed
        self.target_direction = torch.zeros(n, 2, device=device)
        self.target_reached = torch.zeros(n, device=device, dtype=torch.bool)
        self.previous_ball_xy = torch.zeros(n, 2, device=device)
        self.contact_held = torch.zeros(n, device=device, dtype=torch.bool)
        self.open_serve = torch.zeros(n, device=device, dtype=torch.bool)
        self.round_success = torch.zeros(n, device=device, dtype=torch.bool)
        self.round_failure = torch.zeros(n, device=device, dtype=torch.bool)
        self.last_tick = -1
        self.counts = {key: 0 for key in ("served", "settled", "contact", "success", "miss",
                                          "bad_return", "recovery_timeout", "terminated", "multi_touch", "nonfoot")}
        self.recovery_time_sum = 0.
        self.foot_sensors = [env.scene[name] for name in ("left_ball_contact", "right_ball_contact")]
        self.ball_sensor = env.scene["ball_robot_contact"]

    def reset(self, env_ids):
        if len(env_ids):
            self._finish(env_ids[self.open_serve[env_ids]], False, "terminated")
            super().reset(env_ids)

    def _serve(self, env_ids):
        if len(env_ids) == 0:
            return
        super()._serve(env_ids)
        self.phase[env_ids] = PREPARE
        self.elapsed[env_ids] = 0
        self.stable_elapsed[env_ids] = 0
        self.target_reached[env_ids] = False
        self.contact_held[env_ids] = False
        self.open_serve[env_ids] = True
        self.round_success[env_ids] = False
        self.round_failure[env_ids] = False
        angle = self.anchor_yaw[env_ids] + _rand_range(-0.25, 0.25, (len(env_ids),), self.anchor_xy.device)
        self.target_direction[env_ids] = torch.stack((angle.cos(), angle.sin()), -1)
        self.previous_ball_xy[env_ids] = self.ball.data.root_pos_w[env_ids, :2]
        self.counts["served"] += len(env_ids)
        # Clear prior serve's contact history, including when it ended without an episode reset.
        for sensor in [*self.foot_sensors, self.ball_sensor]:
            sensor.reset(env_ids)

    def _finish(self, ids, success, reason):
        ids = ids[self.open_serve[ids]]
        if len(ids) == 0:
            return
        self.open_serve[ids] = False
        self.ball_active[ids] = False
        self.phase[ids] = READY if success else WAIT
        if success:
            self.round_success[ids] = True
            self.recovery_time_sum += self.elapsed[ids].sum().item()
        else:
            self.round_failure[ids] = True
        self.elapsed[ids] = 0
        self.counts["settled"] += len(ids)
        self.counts["success" if success else reason] += len(ids)

    def _contact(self):
        contacts, supports = [], []
        for sensor in self.foot_sensors:
            data = sensor.data
            history = data.force_matrix_w_history
            if history is None or history.ndim != 5 or history.shape[2:4] != (1, 1):
                raise RuntimeError("Each v3 foot sensor must filter exactly one Ball with force history")
            if history.shape[1] < self.env.cfg.decimation:
                raise RuntimeError("Contact history must cover every physics substep")
            contacts.append(history[:, :self.env.cfg.decimation].norm(dim=-1).amax(dim=(1, 2, 3)) > 0.5)
            # Ground support is vertical net force, excluding ball's vertical normal force.
            ball_force = data.force_matrix_w[:, 0, 0, 2]
            supports.append((data.net_forces_w[:, 0, 2] - ball_force) > 5.)
        body = self.ball_sensor.data.force_matrix_w_history
        if (body is None or body.ndim != 5 or body.shape[2] != 1 or body.shape[3] == 0
                or body.shape[1] < self.env.cfg.decimation):
            raise RuntimeError("Ball sensor requires named Robot filters and complete substep history")
        body = body[:, :self.env.cfg.decimation, 0].sum(dim=2)
        residual = body.clone()
        for sensor in self.foot_sensors:
            residual += sensor.data.force_matrix_w_history[:, :self.env.cfg.decimation, 0, 0]
        nonfoot = (residual.norm(dim=-1) > (0.5 + 0.05 * body.norm(dim=-1))).any(-1)
        return torch.stack(contacts, -1), torch.stack(supports, -1), nonfoot

    def tick(self):
        if self.last_tick == self.env.common_step_counter:
            return
        self.last_tick = self.env.common_step_counter
        dt = self.env.step_dt
        self.kick_success_flag.zero_()
        self.round_success.zero_()
        self.round_failure.zero_()
        self.just_missed.zero_()
        self.elapsed += dt
        pos = self.ball.data.root_pos_w[:, :2]
        vel = self.ball.data.root_lin_vel_w[:, :2]
        contacts, supports, nonfoot = self._contact()
        contact = contacts.any(-1)
        new_contact = contact & ~self.contact_held
        self.contact_held = contact
        terminated = self.env.reset_buf.bool()
        ids = (self.open_serve & terminated).nonzero().flatten()
        self._finish(ids, False, "terminated")
        self._finish((self.open_serve & nonfoot).nonzero().flatten(), False, "nonfoot")
        # Routing is initialized from the serve and locked through contact/recovery.
        strike = self.open_serve & (self.phase == PREPARE) & new_contact
        self.kick_success_flag[:] = strike
        self.ball_kicked |= strike
        self.phase[strike] = RECOVER
        self.elapsed[strike] = 0
        self.counts["contact"] += strike.sum().item()
        repeated = self.open_serve & (self.phase == RECOVER) & new_contact & ~strike
        self._finish(repeated.nonzero().flatten(), False, "multi_touch")
        self.ball_return_speed = torch.where(self.ball_kicked & self.open_serve,
                                             (vel * self.target_direction).sum(-1), torch.zeros_like(self.elapsed))

        relative = pos - self.anchor_xy
        old_relative = self.previous_ball_xy - self.anchor_xy
        along = (relative * self.target_direction).sum(-1)
        old_along = (old_relative * self.target_direction).sum(-1)
        crossed = (old_along < self.target_distance) & (along >= self.target_distance)
        fraction = ((self.target_distance - old_along) / (along - old_along).clamp(min=1.e-6)).clamp(0, 1)
        crossing_pos = old_relative + fraction[:, None] * (relative - old_relative)
        perpendicular = torch.stack((-self.target_direction[:, 1], self.target_direction[:, 0]), -1)
        lateral_error = (crossing_pos * perpendicular).sum(-1).abs()
        valid_return = (lateral_error <= self.target_half_width) & (vel.norm(dim=-1) >= 0.4) & (vel.norm(dim=-1) <= 4.)
        valid_return &= self.ball.data.root_pos_w[:, 2] < 0.5
        recovering = self.open_serve & (self.phase == RECOVER)
        self.target_reached |= recovering & crossed & valid_return
        self._finish((recovering & crossed & ~valid_return).nonzero().flatten(), False, "bad_return")
        data = self.robot.data
        stable = (data.projected_gravity_b[:, :2].norm(dim=-1) < 0.15)
        stable &= data.root_lin_vel_w[:, :2].norm(dim=-1) < 0.3
        stable &= data.root_ang_vel_b.norm(dim=-1) < 0.6
        stable &= data.root_pos_w[:, 2] > 0.65
        stable &= data.joint_vel.square().mean(-1).sqrt() < 2.
        stable &= supports.all(-1)
        self.stable_elapsed = torch.where(stable & (self.phase == RECOVER), self.stable_elapsed + dt, 0.)
        complete = self.open_serve & self.target_reached & (self.stable_elapsed >= self.stable_duration)
        self._finish(complete.nonzero().flatten(), True, "success")
        timeout = self.open_serve & (self.phase == RECOVER) & (self.elapsed >= self.recovery_timeout)
        self._finish(timeout.nonzero().flatten(), False, "recovery_timeout")
        forward = torch.stack((self.anchor_yaw.cos(), self.anchor_yaw.sin()), -1)
        missed = self.open_serve & (self.phase == PREPARE) & (
            ((relative * forward).sum(-1) < -0.3) | (relative.norm(dim=-1) > 3.) |
            (vel.norm(dim=-1) < 0.15) | (self.elapsed > 8.))
        self.just_missed[:] = missed
        self._finish(missed.nonzero().flatten(), False, "miss")
        self.previous_ball_xy.copy_(pos)
        self.prev_ball_vel_xy.copy_(vel)
        # Finite waiting time independent of the policy reporting readiness.
        serve = ~self.open_serve & (self.elapsed >= 0.4) & ~terminated
        self._serve(serve.nonzero().flatten())

    def metrics(self):
        return {**{f"Soccer/{k}": float(v) for k, v in self.counts.items()},
                "Soccer/pending": float(self.open_serve.sum()),
                "Soccer/success_per_served": self.counts["success"] / max(1, self.counts["served"]),
                "Soccer/mean_recovery_s": self.recovery_time_sum / max(1, self.counts["success"])}


def setup_soccer_v3(env, env_ids, recovery_timeout=3.0, stable_duration=0.3,
                    target_distance=2.0, target_half_width=0.6, max_serve_speed=0.8):
    env._kickball = SoccerV3State(env, SceneEntityCfg("robot"), SceneEntityCfg("ball"),
                                 recovery_timeout, stable_duration, target_distance,
                                 target_half_width, max_serve_speed)


def target_command(env):
    kb = getattr(env, "_kickball", None)
    if kb is None:
        return torch.zeros(env.num_envs, 2, device=env.device)
    direction = torch.cat((kb.target_direction, torch.zeros(env.num_envs, 1, device=env.device)), -1)
    return quat_apply_inverse(env.scene["robot"].data.root_quat_w, direction)[:, :2]


def complete_return(env):
    return env._kickball.round_success.float()


def failed_return(env):
    return env._kickball.round_failure.float()


def recovery_reward(env):
    kb = env._kickball
    return (kb.phase == RECOVER).float() * (kb.stable_elapsed / kb.stable_duration).clamp(max=1.)


def speed_curriculum(env, env_ids):
    kb = getattr(env, "_kickball", None)
    if kb is None:
        return 0.8
    # Conservative, bounded stage schedule; every ended serve (including falls) counts.
    settled = kb.counts["settled"]
    if settled - getattr(kb, "_curriculum_settled", 0) >= 200:
        successes = kb.counts["success"] - getattr(kb, "_curriculum_successes", 0)
        rate = successes / (settled - getattr(kb, "_curriculum_settled", 0))
        top = kb.serve_speed_range[1]
        top += 0.1 if rate > 0.75 else (-0.1 if rate < 0.3 else 0.)
        kb.serve_speed_range = (0.4, min(kb.max_serve_speed, max(0.8, top)))
        kb._curriculum_settled, kb._curriculum_successes = settled, kb.counts["success"]
    return kb.serve_speed_range[1]
