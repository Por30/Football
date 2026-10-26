"""Wall12 behavior with an independent wall13 checkpoint and logging identity."""
from .carrybox_wall12 import Wall12CarryBoxEnv


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
        contract.update(variant='walled13', migration_revision=1, parent='walled12_revision1')
        return contract
