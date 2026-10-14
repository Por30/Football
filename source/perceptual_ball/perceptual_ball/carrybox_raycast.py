"""Nearest visible surface across shared BVHs with per-environment rigid poses."""
import warp as wp


@wp.kernel
def optical_depth(
    env_ids: wp.array(dtype=wp.int32),
    camera: wp.array(dtype=wp.transform),
    directions: wp.array(dtype=wp.vec3),
    meshes: wp.array(dtype=wp.uint64),
    poses: wp.array2d(dtype=wp.transform),
    near: float,
    far: float,
    depth: wp.array2d(dtype=float),
):
    row, pixel = wp.tid()
    env = env_ids[row]
    local_ray = directions[pixel]
    cosine = local_ray[0]  # camera world convention: +X optical axis
    direction = wp.transform_vector(camera[env], local_ray)
    # Query starts ON the near plane: a surface before near must not hide a
    # valid surface behind it. The final output is optical Z, not ray range.
    origin = wp.transform_get_translation(camera[env]) + direction * (near / cosine)
    closest = (far - near) / cosine
    for obj in range(meshes.shape[0]):
        inverse = wp.transform_inverse(poses[env, obj])
        hit = wp.mesh_query_ray(meshes[obj], wp.transform_point(inverse, origin),
                                wp.transform_vector(inverse, direction), closest)
        if hit.result:
            closest = wp.min(closest, hit.t)
    depth[env, pixel] = wp.min(far, near + closest * cosine)
