"""Pure tensor success criterion; no state-machine information is exposed to the policy."""
import torch


class LiftHoldState:
    def __init__(self, num_envs, device, hold_steps=25):
        self.hold_steps = hold_steps
        self.count = torch.zeros(num_envs, dtype=torch.long, device=device)
        self.last_step = -1
        self.success = torch.zeros(num_envs, dtype=torch.bool, device=device)

    def reset(self, ids):
        self.count[ids] = 0
        self.success[ids] = False

    def update(self, step, bottom_clearance, contacts, upright, speed):
        if step != self.last_step:
            valid = (bottom_clearance >= .12) & contacts.all(-1) & (upright > .9) & (speed < .25)
            self.count = torch.where(valid, self.count + 1, 0)
            self.success = self.count >= self.hold_steps
            self.last_step = step
        return self.success
