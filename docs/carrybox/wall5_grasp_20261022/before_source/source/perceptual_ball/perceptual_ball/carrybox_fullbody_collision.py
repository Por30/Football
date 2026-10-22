"""Wall5-only full-body external collision coverage; shared USD stays immutable."""

FULL_BODY_COLLISION_PROFILE = 'g1_visual_convex_hull_full_body_v1'
ADDED_COLLISION_LINKS = (
    'pelvis', 'waist_yaw_link', 'waist_roll_link', 'head_link',
    'left_wrist_yaw_link', 'right_wrist_yaw_link', 'logo_link',
)
REPLACED_COLLISION_LINKS = (
    'left_knee_link', 'right_knee_link',
    'left_shoulder_pitch_link', 'right_shoulder_pitch_link',
    'left_shoulder_roll_link', 'right_shoulder_roll_link',
)


def add_full_body_collisions(robot_prim):
    """Reference each physical shell in its own link frame, including head offset.

    The existing 22 mesh hulls (including feet and rubber hands) are untouched.
    Empty sensor/palm frames and the pelvis contact marker have no physical shell.
    CollisionAPI on the instance root matches the original USD's merged hulls.
    No mass, inertia, joint, visual or shared asset properties are rewritten.
    """
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    stage = robot_prim.GetStage()
    for name in ADDED_COLLISION_LINKS + REPLACED_COLLISION_LINKS:
        link = robot_prim.GetChild(name)
        visual = link.GetChild('visuals') if link else None
        if not link or not link.HasAPI(UsdPhysics.RigidBodyAPI) or not visual:
            raise ValueError(f'Missing physical G1 shell: {name}')
        meshes = [p for p in Usd.PrimRange(visual, Usd.TraverseInstanceProxies())
                  if p.IsA(UsdGeom.Mesh)]
        if not meshes:
            raise ValueError(f'Missing G1 visual mesh: {name}')
        # Do not mutate a referenced/instanced source or retain duplicate shapes.
        old = link.GetChild('collisions')
        if old:
            old.SetActive(False)
        path = link.GetPath().AppendChild('full_body_collisions')
        collider = stage.DefinePrim(path, 'Xform')
        collider.GetReferences().SetReferences([Sdf.Reference(primPath=visual.GetPath())])
        collider.SetInstanceable(True)
        UsdGeom.Imageable(collider).CreateVisibilityAttr().Set('invisible')
        UsdGeom.Imageable(collider).CreatePurposeAttr().Set('proxy')
        UsdPhysics.CollisionAPI.Apply(collider).CreateCollisionEnabledAttr().Set(True)
        UsdPhysics.MeshCollisionAPI.Apply(collider).CreateApproximationAttr().Set('convexHull')
