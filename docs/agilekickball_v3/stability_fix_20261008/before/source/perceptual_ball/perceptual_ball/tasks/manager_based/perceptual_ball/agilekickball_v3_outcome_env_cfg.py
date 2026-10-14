"""V2 direct feedback control with wider serves and a training-only outcome auxiliary."""
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationTermCfg as ObsTerm, ObservationGroupCfg as ObsGroup
from isaaclab.utils import configclass
from .agilekickball_v2_env_cfg import AgileKickballV2EnvCfg, AgileKickballV2PPORunnerCfg
from .agilekickball_env_cfg import AgileObservationsCfg, AgileAlgorithmCfg
from .mdp.agilekickball_v3_outcome import (
    REVISION, MAX_ROBOT_ANCHOR_DISTANCE, setup_agilekickball_v3, outcome_training_state)


@configclass
class OutcomeObservationsCfg(AgileObservationsCfg):
    @configclass
    class OutcomeStateCfg(ObsGroup):
        state = ObsTerm(func=outcome_training_state)

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    outcome_state: OutcomeStateCfg = OutcomeStateCfg()


@configclass
class AgileKickballV3EnvCfg(AgileKickballV2EnvCfg):
    observations: OutcomeObservationsCfg = OutcomeObservationsCfg()

    def __post_init__(self):
        super().__post_init__()
        self.events.setup_kickball_state = EventTerm(
            func=setup_agilekickball_v3, mode="startup", params={"revision": REVISION})
        self.terminations.walked_away.params["max_dist"] = MAX_ROBOT_ANCHOR_DISTANCE


@configclass
class OutcomeAlgorithmCfg(AgileAlgorithmCfg):
    outcome_aux_coef: float = .1
    outcome_aux_lr: float = 1.e-4
    outcome_horizon: int = 8
    outcome_max_samples: int = 8192
    outcome_batch_size: int = 2048
    outcome_max_kl: float = .005


@configclass
class AgileKickballV3PPORunnerCfg(AgileKickballV2PPORunnerCfg):
    experiment_name = "agilekickball_v3"
    algorithm = OutcomeAlgorithmCfg(**AgileKickballV2PPORunnerCfg().algorithm.to_dict())

    def __post_init__(self):
        self.policy.class_name = "OutcomeActorCritic"
        self.algorithm.class_name = "ContactOutcomePPO"
