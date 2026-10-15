"""V5-only noise at the capture boundary; the shared ray-caster stays unchanged."""
import copy
import torch
from isaaclab.utils import configclass
from .carrybox_warp_camera import WarpDepthCamera, WarpDepthCameraCfg
from .kickball_randomization import DepthRandomizer, DEFAULT_DEPTH_RANDOMIZATION


class RandomizedKickballCamera(WarpDepthCamera):
    def _initialize_impl(self):
        super()._initialize_impl()
        self.randomizer=DepthRandomizer(self._num_envs,self.device,self.cfg.noise,
            enabled=self.cfg.noise_enabled,near=self.cfg.near,far=self.cfg.far)
        self.clean_depth=self._depth.clone()
        self.capture_count=torch.zeros(self._num_envs,device=self.device,dtype=torch.long)
        self._data.output['distance_to_image_plane_clean']=self.clean_depth.view(self._num_envs,*self.image_shape,1)

    def reset(self, env_ids=None):
        super().reset(env_ids)
        if hasattr(self,'randomizer'):
            self.randomizer.reset(env_ids)
            ids=slice(None) if env_ids is None else env_ids
            self.clean_depth[ids]=self.cfg.far
            self._depth[ids]=self.cfg.far
            self.capture_count[ids]=0

    def _update_buffers_impl(self, env_ids):
        super()._update_buffers_impl(env_ids)
        self.clean_depth[env_ids]=self._depth[env_ids]
        raw=self.clean_depth[env_ids].view(-1,*self.image_shape)
        self._depth[env_ids]=self.randomizer.apply(raw,env_ids).flatten(1)
        self.capture_count[env_ids]+=1


@configclass
class RandomizedKickballCameraCfg(WarpDepthCameraCfg):
    class_type: type = RandomizedKickballCamera
    noise_enabled: bool = True
    noise: dict = copy.deepcopy(DEFAULT_DEPTH_RANDOMIZATION)
