"""Continuous v0 ball rounds, with a quiet standing interval before every serve."""
import torch
from isaaclab.managers import SceneEntityCfg
from .kickball_state import KickballState


class AgileKickballState(KickballState):
    def __init__(self, env, stable_duration=.3, serve_cooldown=.4, recovery_timeout=5.):
        if not 0 < stable_duration <= serve_cooldown < recovery_timeout:
            raise ValueError("Require 0 < stable_duration <= serve_cooldown < recovery_timeout")
        super().__init__(env, SceneEntityCfg("robot"), SceneEntityCfg("ball"), rsi_probability=0.)
        self.stable_duration = stable_duration
        self.serve_cooldown = serve_cooldown
        self.recovery_timeout = recovery_timeout
        self.stable_elapsed = torch.zeros(env.num_envs, device=env.device)
        self.wait_elapsed = torch.zeros_like(self.stable_elapsed)
        self.serves = torch.zeros(env.num_envs, device=env.device, dtype=torch.long)
        self.initial_serves = torch.zeros_like(self.serves)
        self.recovered_serves = torch.zeros_like(self.serves)
        self.incoming_steps = torch.zeros_like(self.stable_elapsed)
        self.near_steps = torch.zeros_like(self.stable_elapsed)
        self.successes = torch.zeros_like(self.serves)
        self.exposure_offset = 0.0
        self.serve_distance_range = (.5, .7)
        self._initializing = False
        self.last_tick = -1

    def balanced(self):
        data = self.robot.data
        height = data.root_pos_w[:, 2] - self.env_origins[:, 2]
        feet_z = data.body_link_pos_w[:, self.foot_body_ids, 2] - self.env_origins[:, 2, None]
        return ((data.projected_gravity_b[:, :2].norm(dim=-1) < .15)
                & (data.projected_gravity_b[:, 2] < -.98)
                & (data.root_lin_vel_w.norm(dim=-1) < .25)
                & (data.root_ang_vel_b.norm(dim=-1) < .5)
                & (height > .7) & (height < .9)
                & (data.joint_vel.square().mean(-1).sqrt() < 1.5)
                & (feet_z < .12).all(-1) & (feet_z > -.03).all(-1))

    def reset(self, env_ids):
        self.stable_elapsed[env_ids] = 0
        self.wait_elapsed[env_ids] = 0
        # Robot/joints have already reset. This bootstrap is NOT a recovered round.
        self._initializing = True
        try:
            super().reset(env_ids)
        finally:
            self._initializing = False

    @property
    def exposure_steps(self):
        return self.exposure_offset + self.incoming_steps.mean().item()

    def observation_status(self):
        delta = self.ball.data.root_pos_w[:, :2] - self.robot.data.root_pos_w[:, :2]
        incoming = self.ball_active & ((delta * self.ball.data.root_lin_vel_w[:, :2]).sum(-1) < -.02)
        feet = self.robot.data.body_link_pos_w[:, self.foot_body_ids]
        near = self.ball_active & ((feet - self.ball.data.root_pos_w[:, None]).norm(dim=-1).amin(-1) < .35)
        return torch.stack((self.ball_active, incoming, near), -1).float()

    def _serve(self, env_ids):
        if self._initializing:
            super()._serve(env_ids)
            self.serves[env_ids] += 1
            self.initial_serves[env_ids] += 1
            return
        ids = self._ready_to_serve(env_ids)
        if len(ids):
            super()._serve(ids)
            self.stable_elapsed[ids] = 0
            self.wait_elapsed[ids] = 0
            self.serves[ids] += 1
            self.recovered_serves[ids] += 1

    def _ready_to_serve(self, env_ids):
        ready = ((self.stable_elapsed[env_ids] >= self.stable_duration)
                 & (self.wait_elapsed[env_ids] >= self.serve_cooldown)
                 & (self.wait_elapsed[env_ids] < self.recovery_timeout))
        # IsaacLab creates reset_buf on the first step, after the initial reset event.
        terminated = getattr(self.env, "reset_buf", None)
        if terminated is not None:
            ready &= ~terminated[env_ids].bool()
        return env_ids[ready]

    def tick(self):
        if self.last_tick == self.env.common_step_counter:
            return
        self.last_tick = self.env.common_step_counter
        status = self.observation_status()
        alive = ~self.env.reset_buf.bool()
        self.incoming_steps += status[:, 1] * alive
        self.near_steps += status[:, 2] * alive
        active_before = self.ball_active.clone()
        waiting = ~active_before
        self.stable_elapsed = torch.where(waiting & self.balanced(), self.stable_elapsed + self.env.step_dt, 0.)
        self.wait_elapsed = torch.where(waiting, self.wait_elapsed + self.env.step_dt, 0.)
        super().tick()  # v0 strike, reward pulses, ball-end criteria and cooldown bookkeeping
        ended = active_before & ~self.ball_active
        self.stable_elapsed[ended] = 0
        self.wait_elapsed[ended] = 0
        # A failed episode cannot receive a last-moment kick bonus before reset.
        self.kick_success_flag &= ~self.env.reset_buf.bool()
        self.successes += self.kick_success_flag.long()

    def metrics(self):
        return {"AgileKickball/serves": self.serves.sum().item(),
                "AgileKickball/initial_serves": self.initial_serves.sum().item(),
                "AgileKickball/recovered_serves": self.recovered_serves.sum().item(),
                "AgileKickball/incoming_steps_per_env": self.exposure_steps,
                "AgileKickball/near_steps_per_env": self.near_steps.mean().item(),
                "AgileKickball/kick_proxy_successes": self.successes.sum().item(),
                "AgileKickball/waiting_fraction": (~self.ball_active).float().mean().item()}


def setup_agilekickball(env, env_ids, stable_duration=.3, serve_cooldown=.4, recovery_timeout=5.):
    env._kickball = AgileKickballState(env, stable_duration, serve_cooldown, recovery_timeout)


def recovery_timed_out(env):
    kb = env._kickball
    return ~kb.ball_active & (kb.wait_elapsed >= kb.recovery_timeout)


def ball_training_status(env):
    """Diagnostics only: active, inward world velocity, within 35 cm of a foot."""
    if not hasattr(env, "_kickball"):
        return torch.zeros(env.num_envs, 3, device=env.device)
    return env._kickball.observation_status()


def exposure_speed_curriculum(env, env_ids, ramp_steps=240_000):
    """One averaged incoming control step per env, not parallel sample count."""
    kb = env._kickball
    progress = min(kb.exposure_steps / ramp_steps, 1.)
    kb.serve_speed_range = (.4, .8 + 1.2 * progress)
    # Short approach bootstrap; grow to v0 distances as real incoming exposure accumulates.
    distance_progress = min(kb.exposure_steps / 60_000, 1.)
    kb.serve_distance_range = (.5 + .8 * distance_progress, .7 + 1.3 * distance_progress)
    return kb.serve_speed_range[1]
