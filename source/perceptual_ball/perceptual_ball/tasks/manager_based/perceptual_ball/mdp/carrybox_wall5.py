"""Wall4 physical task with the independent Wall5 AMP observation contract."""
from perceptual_ball.carrybox_wall5 import project_frame, WALL5_FEATURE_SCHEMA
from . import carrybox as base
from .carrybox_walled import WalledCarryBoxEnv


def amp_frame(env):
    return project_frame(base.amp_frame(env))


class Wall5CarryBoxEnv(WalledCarryBoxEnv):
    amp_warmup_steps = 0

    def terminal_frame(self, group):
        return amp_frame(self) if group == 'amp' else super().terminal_frame(group)

    def checkpoint_contract(self):
        contract = super().checkpoint_contract()
        contract.update(migration_revision=9, physical_parent='walled4_revision8',
                        amp_frame_schema=WALL5_FEATURE_SCHEMA, amp_shape=[10, 35],
                        amp_history='repeat_reset_frame_reward_and_training_from_step1')
        return contract
