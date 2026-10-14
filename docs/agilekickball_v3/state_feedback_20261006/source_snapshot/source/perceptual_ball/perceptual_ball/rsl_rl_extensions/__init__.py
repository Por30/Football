# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Project-local rsl_rl extensions: an asymmetric actor-critic with an auxiliary head that
regresses the ball's privileged state from the depth camera, an AMP discriminator trained
against real retargeted kick clips, and the PPO/runner glue needed to train both (rsl-rl-lib
3.0.1 has no generic hook for either a custom supervised auxiliary loss or AMP)."""

from .algorithm import BallRegressionPPO, SkillAMPPPO
from .amp import AMP, SkillAMP
from .modules import PerceptionActorCritic
from .runner import BallRegressionOnPolicyRunner
