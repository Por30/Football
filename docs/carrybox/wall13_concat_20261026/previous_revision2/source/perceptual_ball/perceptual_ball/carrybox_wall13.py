"""Wall13 revision 2: explicit predicted box pose inside the 128-D visual feature."""
from .carrybox_wall12 import POSE_CONTRACT

POSE_FEEDBACK_CONTRACT = dict(POSE_CONTRACT, actor_feedback=True)
VISUAL_FEEDBACK_CONTRACT = dict(
    schema=1, latent_dim=128, prediction_dim=9, concat_dim=137, output_dim=128,
    fusion='linear137to128_elu', prediction='raw_camera_xyz_metres_rotation6',
    inputs='depth_only_prediction_no_privileged_substitution',
    gradients='ppo_and_policy_smooth_through_prediction_and_encoder_no_detach',
    deployment='encoder_pose_head_fusion_actor',
)
