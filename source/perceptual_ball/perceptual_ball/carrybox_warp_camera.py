"""Optical depth from complete visual meshes and live PhysX link poses.

BVHs are built once in rigid-link frames, shared across all cloned environments.
The sensor never creates an RTX camera or modifies simulation/render settings.
"""
import hashlib
import numpy as np
import torch
import warp as wp
from pxr import Usd, UsdGeom, UsdPhysics
import omni.physics.tensors.impl.api as physx
from isaaclab.sensors import SensorBase, SensorBaseCfg, CameraData, TiledCameraCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply, quat_apply_inverse, quat_mul, quat_conjugate
from isaaclab.utils.math import convert_camera_frame_orientation_convention as convert
from .carrybox_raycast import optical_depth


def visual_mesh(stage, root_path):
    """Bake every visible descendant surface into the rigid root frame."""
    import trimesh
    root = stage.GetPrimAtPath(root_path)
    cache = UsdGeom.XformCache()
    inverse = cache.GetLocalToWorldTransform(root).GetInverse()
    vertices, triangles, sources = [], [], []
    count = 0
    for prim in Usd.PrimRange(root, Usd.TraverseInstanceProxies()):
        if not prim.IsA(UsdGeom.Gprim):
            continue
        imageable = UsdGeom.Imageable(prim)
        if imageable.ComputeVisibility() == 'invisible' or imageable.ComputePurpose() in ('guide', 'proxy'):
            continue
        if prim.IsA(UsdGeom.Mesh):
            mesh = UsdGeom.Mesh(prim)
            points = np.asarray(mesh.GetPointsAttr().Get(), dtype=np.float32)
            indices = list(mesh.GetFaceVertexIndicesAttr().Get())
            faces, offset = [], 0
            for size in mesh.GetFaceVertexCountsAttr().Get():
                faces.extend((indices[offset], indices[offset+i], indices[offset+i+1]) for i in range(1, size-1))
                offset += size
            faces = np.asarray(faces, dtype=np.int32)
        elif prim.IsA(UsdGeom.Cube):
            geometry = trimesh.creation.box(extents=[UsdGeom.Cube(prim).GetSizeAttr().Get()] * 3)
            points, faces = geometry.vertices, geometry.faces
        elif prim.IsA(UsdGeom.Sphere):
            geometry = trimesh.creation.uv_sphere(radius=UsdGeom.Sphere(prim).GetRadiusAttr().Get(), count=[64, 64])
            points, faces = geometry.vertices, geometry.faces
        else:
            raise RuntimeError(f'Unsupported visible primitive {prim.GetPath()}: {prim.GetTypeName()}')
        if not len(points) or not len(faces):
            raise RuntimeError(f'Empty visible surface: {prim.GetPath()}')
        matrix = np.asarray(cache.GetLocalToWorldTransform(prim) * inverse)
        points = np.c_[points, np.ones(len(points))] @ matrix
        vertices.append(points[:, :3].astype(np.float32))
        triangles.append(faces.astype(np.int32) + count)
        count += len(points)
        sources.append(dict(path=str(prim.GetPath()), vertices=len(points), triangles=len(faces)))
    if not vertices:
        return None
    return np.concatenate(vertices), np.concatenate(triangles).flatten(), sources


class WarpDepthCamera(SensorBase):
    @property
    def data(self):
        self._update_outdated_buffers()
        return self._data

    @property
    def image_shape(self):
        return self.cfg.height, self.cfg.width

    def _initialize_impl(self):
        super()._initialize_impl()
        self._physics = physx.create_simulation_view(self._backend)
        self._physics.set_subspace_roots('/')
        # Scene cloning preserves numerical environment order, assert it rather
        # than relying on lexicographic sorting (env_10 before env_2).
        self._parent_view = self._physics.create_rigid_body_view(self.cfg.prim_path.replace('.*', '*'))
        expected = [self.cfg.prim_path.replace('.*', str(i)) for i in range(self._num_envs)]
        if self._parent_view.prim_paths != expected:
            raise RuntimeError('Warp camera parent/environment ordering differs')
        env_root = '/World/envs/env_0'
        robot = self.stage.GetPrimAtPath(env_root + '/Robot')
        roots = [str(p.GetPath()) for p in Usd.PrimRange(robot)
                 if p.HasAPI(UsdPhysics.RigidBodyAPI)]
        roots += [env_root + '/' + name for name in self.cfg.object_names]
        roots += ['/World/ground']
        self.mesh_manifest, self._meshes, self._views = [], [], []
        unique, ids = {}, []
        for root in roots:
            result = visual_mesh(self.stage, root)
            if result is None:
                if '/Robot/' not in root:
                    raise RuntimeError(f'No visible geometry in required object: {root}')
                continue  # Explicitly listed in manifest below as a geometry-free link.
            vertices, faces, sources = result
            digest = hashlib.sha256(vertices.tobytes() + faces.tobytes()).hexdigest()
            if digest not in unique:
                unique[digest] = wp.Mesh(points=wp.array(vertices, dtype=wp.vec3, device=self.device),
                                         indices=wp.array(faces, dtype=wp.int32, device=self.device))
            mesh = unique[digest]
            self._meshes.append(mesh)  # Keep meshes and BVHs alive for the sensor lifetime.
            ids.append(mesh.id)
            if root.startswith(env_root):
                pattern = root.replace('env_0', 'env_*', 1)
                view = self._physics.create_rigid_body_view(pattern)
                if view.prim_paths != [root.replace('env_0', f'env_{i}', 1) for i in range(self._num_envs)]:
                    raise RuntimeError(f'Warp mesh/environment ordering differs: {root}')
                self._views.append(view)
            else:
                transform = UsdGeom.XformCache().GetLocalToWorldTransform(self.stage.GetPrimAtPath(root))
                q = transform.ExtractRotationQuat()
                pose = [*transform.ExtractTranslation(), *q.GetImaginary(), q.GetReal()]
                self._views.append(torch.tensor(pose, device=self.device, dtype=torch.float32).repeat(self._num_envs, 1))
            self.mesh_manifest.append(dict(root=root, sources=sources, digest=digest, dynamic=root.startswith(env_root)))
        self.geometry_free_links = [p for p in roots if not any(m['root'] == p for m in self.mesh_manifest)]
        self._mesh_ids = wp.array(ids, dtype=wp.uint64, device=self.device)
        self._ids = torch.arange(self._num_envs, dtype=torch.int32, device=self.device)
        self._offset_pos = torch.tensor(self.cfg.offset.pos, device=self.device).repeat(self._num_envs, 1)
        self._offset_quat = convert(torch.tensor(self.cfg.offset.rot, device=self.device).repeat(self._num_envs, 1),
                                    origin=self.cfg.offset.convention, target='world')
        self._data = CameraData()
        self._data.pos_w = torch.zeros(self._num_envs, 3, device=self.device)
        self._data.quat_w_world = torch.zeros(self._num_envs, 4, device=self.device)
        self._data.image_shape = self.image_shape
        self._depth = torch.full((self._num_envs, self.cfg.width*self.cfg.height), self.cfg.far, device=self.device)
        self._data.output = {'distance_to_image_plane': self._depth.view(self._num_envs, *self.image_shape, 1)}
        fx = self.cfg.focal_length * self.cfg.width / self.cfg.horizontal_aperture
        fy = self.cfg.focal_length * self.cfg.height / self.cfg.vertical_aperture
        cx, cy = self.cfg.width/2, self.cfg.height/2
        pixel_offset = .5  # Original walled camera uses image-edge coordinates.
        if self.cfg.intrinsics is not None:
            fx, fy, cx, cy = self.cfg.intrinsics
            pixel_offset = 0.  # CameraInfo/OpenCV: integer coordinates at pixel centres.
        intrinsic = torch.tensor([[fx, 0., cx], [0., fy, cy], [0., 0., 1.]], device=self.device)
        self._data.intrinsic_matrices = intrinsic.repeat(self._num_envs, 1, 1)
        v, u = torch.meshgrid(torch.arange(self.cfg.height, device=self.device), torch.arange(self.cfg.width, device=self.device), indexing='ij')
        rays = torch.stack((torch.ones_like(u), -(u+pixel_offset-cx)/fx, -(v+pixel_offset-cy)/fy), -1).float().reshape(-1, 3)
        self._rays = (rays / rays.norm(dim=-1, keepdim=True)).contiguous()
        self._update_poses(self._ids.long())

    def _parent_poses(self):
        p = self._parent_view.get_transforms()
        return p[:, :3], p[:, [6, 3, 4, 5]]

    def _update_poses(self, env_ids):
        p, q = self._parent_poses()
        self._data.pos_w[env_ids] = p[env_ids] + quat_apply(q[env_ids], self._offset_pos[env_ids])
        self._data.quat_w_world[env_ids] = quat_mul(q[env_ids], self._offset_quat[env_ids])

    def _update_buffers_impl(self, env_ids):
        self._update_poses(env_ids)
        camera = torch.cat((self._data.pos_w, self._data.quat_w_world[:, [1, 2, 3, 0]]), -1).contiguous()
        poses = torch.stack([view if isinstance(view, torch.Tensor) else view.get_transforms() for view in self._views], 1).contiguous()
        with wp.ScopedStream(wp.stream_from_torch(torch.cuda.current_stream(self.device))):
            wp.launch(optical_depth, dim=(len(env_ids), self.cfg.width*self.cfg.height), inputs=[
                wp.from_torch(env_ids.to(torch.int32)), wp.from_torch(camera, dtype=wp.transform),
                wp.from_torch(self._rays, dtype=wp.vec3), self._mesh_ids, wp.from_torch(poses, dtype=wp.transform),
                self.cfg.near, self.cfg.far, wp.from_torch(self._depth)], device=self.device)

    def set_mount_poses(self, positions, orientations, env_ids):
        self._offset_pos[env_ids] = positions
        self._offset_quat[env_ids] = convert(orientations, origin='opengl', target='world')
        self._is_outdated[env_ids] = True

    def set_world_poses(self, positions=None, orientations=None, env_ids=None, convention='ros'):
        ids = self._ids.long() if env_ids is None else env_ids
        p, q = self._parent_poses()
        if positions is not None:
            self._offset_pos[ids] = quat_apply_inverse(q[ids], positions-p[ids])
        if orientations is not None:
            target = convert(orientations, origin=convention, target='world')
            self._offset_quat[ids] = quat_mul(quat_conjugate(q[ids]), target)
        self._is_outdated[ids] = True
        self._update_poses(ids)


@configclass
class WarpDepthCameraCfg(SensorBaseCfg):
    class_type: type = WarpDepthCamera
    prim_path: str = '{ENV_REGEX_NS}/Robot/torso_link'
    update_period: float = .02
    width: int = 48
    height: int = 27
    near: float = .1
    far: float = 3.
    focal_length: float = 18.
    horizontal_aperture: float = 35.477
    vertical_aperture: float = 19.956
    object_names: tuple[str, ...] = ('Box', 'Wall', 'Cylinder0', 'Cylinder1', 'Cylinder2', 'Platform')
    intrinsics: tuple[float, float, float, float] | None = None
    offset: TiledCameraCfg.OffsetCfg = TiledCameraCfg.OffsetCfg()
