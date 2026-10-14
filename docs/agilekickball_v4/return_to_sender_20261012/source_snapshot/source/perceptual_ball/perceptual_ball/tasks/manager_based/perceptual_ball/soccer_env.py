"""Reset boundary bridge: preserve terminal training state without advancing history twice."""
import torch
from isaaclab.envs import ManagerBasedRLEnv


class SoccerEnv(ManagerBasedRLEnv):
    def step(self, action):
        self._terminal_snapshot = None
        self._inside_step = True
        try:
            obs, reward, terminated, truncated, extras = super().step(action)
        finally:
            self._inside_step = False
        if self._terminal_snapshot is not None:
            extras["terminal_observations"] = self._terminal_snapshot
        else:
            extras.pop("terminal_observations", None)
        if hasattr(self._kickball, "metrics"):
            extras.setdefault("log", {}).update(self._kickball.metrics())
        return obs, reward, terminated, truncated, extras

    def _reset_idx(self, env_ids):
        if getattr(self, "_inside_step", False):
            manager = self.observation_manager
            # Critic groups have no history/noise. AMP has one term, 10 ordered frames.
            terminal = {name: manager.compute_group(name)[env_ids].clone()
                        for name in ("proprio", "robot_vel", "privileged")}
            for name in ("skill", "target", "timing"):
                if name in manager.active_terms:
                    terminal[name] = manager.compute_group(name)[env_ids].clone()
            cfg = manager._group_obs_term_cfgs["amp"][0]
            frame = cfg.func(self, **cfg.params)[env_ids]
            history = manager.compute_group("amp")[env_ids]
            terminal["amp"] = torch.cat((history[:, frame.shape[-1]:], frame), dim=-1)
            self._terminal_snapshot = {"env_ids": env_ids.clone(), "obs": terminal}
        super()._reset_idx(env_ids)
