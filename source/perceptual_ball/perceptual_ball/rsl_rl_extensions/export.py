"""Export the entire depth policy. Histories are managed by the caller, never by the MLP."""
import copy
import json
from pathlib import Path
import torch
from torch import nn
from .state_feedback import append_ball_feedback, bounded_ball_distribution


class DepthPolicyExport(nn.Module):
    def __init__(self, policy, observation_example):
        super().__init__()
        self.encoder = copy.deepcopy(policy.perception_encoder)
        self.actor = copy.deepcopy(policy.actor)
        self.uses_box_pose_feedback = getattr(policy, 'uses_box_pose_feedback', False)
        self.pose_head = copy.deepcopy(policy.pose_head) if self.uses_box_pose_feedback else nn.Identity()
        self.box_pose_fusion = copy.deepcopy(policy.box_pose_fusion) if self.uses_box_pose_feedback else nn.Identity()
        self.uses_ball_feedback = getattr(policy, 'uses_ball_feedback', False)
        self.ball_head = copy.deepcopy(policy.ball_head) if self.uses_ball_feedback else nn.Identity()
        self.feedback_logstd_min = getattr(policy, 'feedback_logstd_min', -4.)
        self.feedback_logstd_max = getattr(policy, 'feedback_logstd_max', 1.)
        self.feedback_smooth_std = getattr(policy, 'feedback_smooth_std', False)
        groups = policy.obs_groups["policy"]
        index = groups.index(policy.perception_group)
        self.before_dim = sum(observation_example[g].shape[-1] for g in groups[:index])

    def forward(self, flat, depth):
        latent = self.encoder(depth)
        if self.uses_box_pose_feedback:
            latent = self.box_pose_fusion(torch.cat((latent, self.pose_head(latent)), -1))
        features = torch.cat((flat[:, :self.before_dim], latent,
                              flat[:, self.before_dim:]), dim=-1)
        if self.uses_ball_feedback:
            distribution = bounded_ball_distribution(self.ball_head(features), self.feedback_logstd_min,
                                                     self.feedback_logstd_max, self.feedback_smooth_std)
            features = append_ball_feedback(features, depth, distribution)
        return self.actor(features)


def export_depth_policy(policy, obs, path, metadata=None):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    groups = [g for g in policy.obs_groups["policy"] if g != policy.perception_group]
    flat = torch.cat([obs[g][:1].cpu() for g in groups], dim=-1)
    depth = obs[policy.perception_group][:1].cpu()
    wrapper = DepthPolicyExport(policy, obs).cpu().eval()
    with torch.no_grad():
        torch.jit.script(wrapper).save(str(path / "policy.pt"))
        torch.onnx.export(wrapper, (flat, depth), str(path / "policy.onnx"), opset_version=17,
                          input_names=["flat", "depth"], output_names=["actions"],
                          dynamic_axes={"flat": {0: "batch"}, "depth": {0: "batch"}, "actions": {0: "batch"}},
                          dynamo=False)
    manifest = {"schema_version": 3, "flat_groups": groups,
                "flat_group_dims": [obs[g].shape[-1] for g in groups],
                "depth_shape": list(depth.shape[1:]), "depth_order": "oldest_to_newest",
                "proprio_history_order": "term_major_then_oldest_to_newest",
                "output": "raw joint action; apply external clip, scale and offset",
                "includes_ball_state_feedback": getattr(policy, 'uses_ball_feedback', False),
                "metadata": metadata or {}}
    if getattr(policy, 'uses_box_pose_feedback', False):
        manifest['box_pose_feedback'] = copy.deepcopy(policy.box_pose_feedback_contract)
    (path / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return wrapper
