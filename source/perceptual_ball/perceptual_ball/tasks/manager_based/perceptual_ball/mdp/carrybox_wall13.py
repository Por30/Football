"""Wall12 behavior with an independent wall13 checkpoint and logging identity."""
from .carrybox_wall12 import Wall12CarryBoxEnv
from perceptual_ball.carrybox_wall13 import POSE_FEEDBACK_CONTRACT, VISUAL_FEEDBACK_CONTRACT


class Wall13CarryBoxEnv(Wall12CarryBoxEnv):
    def step(self, action):
        result = super().step(action)
        log = result[-1].get('log', {})
        for key in list(log):
            if key.startswith('Wall12/'):
                log[key.replace('Wall12/', 'Wall13/', 1)] = log.pop(key)
        return result

    def checkpoint_contract(self):
        contract = super().checkpoint_contract()
        contract.update(variant='walled13', migration_revision=3, parent='walled12_revision1',
                        actor='proprio93x6_depth4x27x48_pose_concat9_input695',
                        pose_supervision=dict(POSE_FEEDBACK_CONTRACT),
                        visual_feedback=dict(VISUAL_FEEDBACK_CONTRACT))
        return contract
