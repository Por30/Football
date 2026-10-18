"""Offline production-spawn geometry validation and authored-hull visualization."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

import numpy as np
import trimesh
from pxr import Usd, UsdGeom, UsdPhysics

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SRC = ROOT/'source/perceptual_ball/perceptual_ball'
CFG = SRC/'tasks/manager_based/perceptual_ball'
USD = SRC/'assets/robots/g1_29dof/g1_29dof.usd'


def hash_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def function(path, name, namespace):
    node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


def stage(full_body):
    s = Usd.Stage.CreateInMemory()
    root = s.DefinePrim('/Robot', 'Xform')
    root.GetReferences().AddReference(str(USD)); s.SetDefaultPrim(root)
    fake = types.ModuleType('isaaclab.sim')
    fake.spawn_from_usd = lambda *a, **k: root
    fake.find_matching_prims = lambda path: [root]
    pkg = types.ModuleType('isaaclab'); pkg.__path__ = []; pkg.sim = fake
    sys.modules['isaaclab'] = pkg; sys.modules['isaaclab.sim'] = fake
    namespace = {'sim_utils': fake}
    base = function(CFG/'carrybox_walled_env_cfg.py', 'spawn_walled_robot', namespace)
    spawn = function(CFG/'carrybox_wall5_env_cfg.py', 'spawn_wall5_full_body_robot', namespace) if full_body else base
    spawn('/Robot', None)
    return s


def local_points(p, link, cache):
    if p.IsA(UsdGeom.Mesh):
        points = np.asarray(UsdGeom.Mesh(p).GetPointsAttr().Get(), dtype=float)
    elif p.IsA(UsdGeom.Cube):
        points = np.asarray(trimesh.creation.box(extents=[UsdGeom.Cube(p).GetSizeAttr().Get()]*3).vertices)
    else:
        raise AssertionError(p.GetTypeName())
    matrix = np.asarray(cache.GetLocalToWorldTransform(p)*cache.GetLocalToWorldTransform(link).GetInverse())
    return (np.c_[points, np.ones(len(points))] @ matrix)[:, :3]


def colliders(s):
    cache = UsdGeom.XformCache(); result = []
    for link in s.GetDefaultPrim().GetChildren():
        if not link.HasAPI(UsdPhysics.RigidBodyAPI):
            continue
        for p in Usd.PrimRange(link, Usd.TraverseInstanceProxies()):
            if not p.HasAPI(UsdPhysics.CollisionAPI):
                continue
            assert UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()
            geometry = [g for g in Usd.PrimRange(p, Usd.TraverseInstanceProxies()) if g.IsA(UsdGeom.Gprim)]
            approximation = UsdPhysics.MeshCollisionAPI(p).GetApproximationAttr().Get() if p.HasAPI(UsdPhysics.MeshCollisionAPI) else None
            if approximation is None and len(geometry)==1 and geometry[0].HasAPI(UsdPhysics.MeshCollisionAPI):
                approximation=UsdPhysics.MeshCollisionAPI(geometry[0]).GetApproximationAttr().Get()
            # A merged convex hull uses all descendant vertices; knee boxes stay separate.
            sets = [np.concatenate([local_points(g, link, cache) for g in geometry])] if approximation else [local_points(g, link, cache) for g in geometry]
            for points in sets:
                hull = trimesh.convex.convex_hull(points)
                if not approximation:
                    assert len(geometry)==2  # Only historical knee cubes.
                matrix = np.asarray(cache.GetLocalToWorldTransform(link))
                world = (np.c_[hull.vertices,np.ones(len(hull.vertices))] @ matrix)[:, :3]
                result.append(dict(link=link.GetName(),path=str(p.GetPath()),points=points,
                                   vertices=world,faces=np.asarray(hull.faces),approximation=approximation or 'box'))
    return result


def physical_snapshot(s):
    result = {}
    for p in Usd.PrimRange(s.GetDefaultPrim()):
        if p.HasAPI(UsdPhysics.RigidBodyAPI) or p.IsA(UsdPhysics.Joint):
            result[str(p.GetPath())] = {a.GetName(): str(a.Get()) for a in p.GetAttributes()
                if a.GetName().startswith(('physics:', 'physx'))}
    return result


def main():
    pkg = types.ModuleType('perceptual_ball'); pkg.__path__ = [str(SRC)]
    sys.modules['perceptual_ball'] = pkg
    from perceptual_ball.carrybox_fullbody_collision import ADDED_COLLISION_LINKS, REPLACED_COLLISION_LINKS
    protected = [*USD.parent.rglob('*.usd'), SRC/'assets/robots/g1_29dof.py', CFG/'carrybox_walled_env_cfg.py']
    hashes = {str(p.relative_to(ROOT)):hash_file(p) for p in protected}
    old, new = stage(False), stage(True)
    assert physical_snapshot(old) == physical_snapshot(new)
    visual_fn = function(SRC/'carrybox_warp_camera.py', 'visual_mesh', dict(Usd=Usd, UsdGeom=UsdGeom, np=np))
    before, after = colliders(old), colliders(new)
    assert len(before)==30 and len(after)==35
    assert all(x['approximation']=='convexHull' for x in after)
    final = {x['link']:x for x in after}; previous = {}
    for x in before: previous.setdefault(x['link'],[]).append(x)
    checked, geometry_free = [], []
    cache = UsdGeom.XformCache()
    for link in new.GetDefaultPrim().GetChildren():
        if not link.HasAPI(UsdPhysics.RigidBodyAPI): continue
        name = link.GetName(); path = str(link.GetPath())
        a,b = visual_fn(old,path),visual_fn(new,path)
        if a is None:
            assert b is None; geometry_free.append(name); continue
        assert np.array_equal(a[0],b[0]) and np.array_equal(a[1],b[1]), name
        meshes = [p for p in Usd.PrimRange(link.GetChild('visuals'), Usd.TraverseInstanceProxies()) if p.IsA(UsdGeom.Mesh)]
        if not meshes:
            assert name=='pelvis_contact_link' and name not in final
            continue
        points = np.concatenate([local_points(p,link,cache) for p in meshes])
        target = final[name]['points']
        # Exact vertex correspondence proves containment in the defined convex hull,
        # without an AABB-only approximation or a sampled surface test.
        assert points.shape==target.shape and np.allclose(points,target,rtol=0,atol=1e-9), name
        if name not in ADDED_COLLISION_LINKS+REPLACED_COLLISION_LINKS:
            assert len(previous[name])==1
            assert np.array_equal(previous[name][0]['points'],target), name
        else:
            assert not new.GetPrimAtPath(path+'/collisions').IsActive()
            collision=new.GetPrimAtPath(path+'/full_body_collisions')
            assert collision.IsInstance()
            for p in Usd.PrimRange(collision, Usd.TraverseInstanceProxies()):
                assert not p.HasAPI(UsdPhysics.RigidBodyAPI) and not p.HasAPI(UsdPhysics.MassAPI)
                if p.IsA(UsdGeom.Gprim):
                    assert UsdGeom.Imageable(p).ComputeVisibility()=='invisible'
                    assert UsdGeom.Imageable(p).ComputePurpose()=='proxy'
        checked.append(dict(link=name,visual_vertices=len(points),collision=str(final[name]['path']),
                            bounds_link_m=[points.min(0).tolist(),points.max(0).tolist()],
                            visual_digest=hashlib.sha256(b[0].tobytes()+b[1].tobytes()).hexdigest()))
    assert len(checked)==35
    assert set(final)-set(previous)==set(ADDED_COLLISION_LINKS)
    assert all(hash_file(ROOT/p)==value for p,value in hashes.items())
    from visualize import create_visualizations
    create_visualizations(before,after,ADDED_COLLISION_LINKS,REPLACED_COLLISION_LINKS,OUT)
    result=dict(status='PASS',old_shapes_authored=30,new_shapes_authored=35,physical_links_covered=35,
                added=list(ADDED_COLLISION_LINKS),replaced=list(REPLACED_COLLISION_LINKS),
                preserved=22,coverage='Every physical visual vertex equals a final convex-hull input vertex',
                visual_geometry_unchanged=True,mass_inertia_joints_unchanged=True,self_collisions=False,
                geometry_free_links=geometry_free,excluded_visual_marker='pelvis_contact_link',
                links=checked,protected_source_sha256=hashes,
                visualization='Authored convex-hull preview at USD reference pose; PhysX may simplify during cooking')
    (OUT/'geometry.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FULLBODY_GEOMETRY_PASS',json.dumps({k:result[k] for k in ('physical_links_covered','added','replaced','preserved')}))


if __name__=='__main__': main()
