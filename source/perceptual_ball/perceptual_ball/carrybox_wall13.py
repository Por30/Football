"""Wall13 revision 3: append predicted box pose to the unchanged depth latent."""
from .carrybox_wall12 import POSE_CONTRACT

POSE_FEEDBACK_CONTRACT = dict(POSE_CONTRACT, actor_feedback=True)
VISUAL_FEEDBACK_CONTRACT = dict(
    schema=2, latent_dim=128, prediction_dim=9, concat_dim=137, output_dim=137,
    actor_input_dim=695, order='proprio558_depth128_predicted_pose9',
    fusion='concat_only', prediction='raw_camera_xyz_metres_rotation6',
    inputs='depth_only_prediction_no_privileged_substitution',
    gradients='ppo_and_policy_smooth_through_prediction_and_encoder_no_detach',
    deployment='encoder_pose_head_concat_actor',
)
