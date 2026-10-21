"""Walled camera poses with batched parent reads instead of world traversal."""
from isaaclab.sensors import TiledCamera
from isaaclab.utils.math import convert_camera_frame_orientation_convention, quat_apply, quat_mul


class FabricTiledCamera(TiledCamera):
    def _initialize_impl(self):
        self._mount_cache = None
        if hasattr(self, '_parent_view'):
            del self._parent_view
        super()._initialize_impl()

    def set_mount_poses(self, positions, orientations, env_ids):
        """Write OpenGL mount poses and refresh exactly the modified rows."""
        self._view.set_local_poses(positions, orientations, indices=env_ids)
        if getattr(self, '_mount_cache', None) is not None:
            self._mount_cache[0][env_ids] = positions
            self._mount_cache[1][env_ids] = orientations

    def set_world_poses(self, *args, **kwargs):
        self._mount_cache = None
        return super().set_world_poses(*args, **kwargs)

    def set_world_poses_from_view(self, *args, **kwargs):
        self._mount_cache = None
        return super().set_world_poses_from_view(*args, **kwargs)

    def _update_poses(self, env_ids):
        if len(self._sensor_prims) == 0:
            raise RuntimeError("Camera prim is None. Please call 'sim.play()' first.")
        # PhysX owns the parent's Fabric world transform. Creating one on the
        # camera child itself can freeze its parent-relative pose in Sim 4.5.
        if not hasattr(self, '_parent_view'):
            from isaacsim.core.prims import XFormPrim
            self._parent_view = XFormPrim(self.cfg.prim_path.rsplit('/', 1)[0], reset_xform_properties=False)
            self._parent_view.initialize()
            expected = [p.rsplit('/', 1)[0] for p in self._view.prim_paths]
            if self._parent_view.prim_paths != expected:
                raise RuntimeError('Camera/parent view ordering differs')
        # Full-view query avoids Sim 4.5's int64 -> Warp uint32 index-view issue.
        # A reset/render can rebuild Fabric storage without a physics step (the
        # view's normal invalidation callback). Never reuse that selection.
        if self._parent_view._view_in_fabric_prepared:
            self._parent_view._selection = None
        positions, rotations = self._parent_view.get_world_poses(usd=False)
        # Mounts stay fixed between resets. All supported camera setters above
        # update or invalidate these rows; world poses remain fresh every frame.
        if getattr(self, '_mount_cache', None) is None:
            self._mount_cache = tuple(v.clone() for v in self._view.get_local_poses())
        local_pos, local_rot = (v[env_ids] for v in self._mount_cache)
        self._data.pos_w[env_ids] = positions[env_ids] + quat_apply(rotations[env_ids], local_pos)
        self._data.quat_w_world[env_ids] = convert_camera_frame_orientation_convention(
            quat_mul(rotations[env_ids], local_rot), origin='opengl', target='world')
