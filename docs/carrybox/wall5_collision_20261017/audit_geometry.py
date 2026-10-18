"""CPU USD audit; execute production shoulder conversion on a transient stage."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import trimesh
import yaml
from pxr import Usd, UsdGeom, UsdPhysics

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SRC = ROOT / 'source/perceptual_ball/perceptual_ball'
ASSET = SRC / 'assets/robots/g1_29dof/g1_29dof.usd'
SPAWN = SRC / 'tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py'
SAVED = ROOT / 'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a/params/env.yaml'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def geometries(stage):
    cache = UsdGeom.XformCache()
    rows = []
    root = stage.GetDefaultPrim()
    for collider in Usd.PrimRange(root, Usd.TraverseInstanceProxies()):
        if not collider.HasAPI(UsdPhysics.CollisionAPI):
            continue
        assert UsdPhysics.CollisionAPI(collider).GetCollisionEnabledAttr().Get()
        link = collider.GetParent()
        inverse = cache.GetLocalToWorldTransform(link).GetInverse()
        row = dict(link=link.GetName(),path=str(collider.GetPath()),
                   approximation=UsdPhysics.MeshCollisionAPI(collider).GetApproximationAttr().Get()
                   if collider.HasAPI(UsdPhysics.MeshCollisionAPI) else None, geometries=[])
        for p in Usd.PrimRange(collider, Usd.TraverseInstanceProxies()):
            if not p.IsA(UsdGeom.Gprim):
                continue
            item = dict(path=str(p.GetPath()),type=p.GetTypeName())
            if p.HasAPI(UsdPhysics.MeshCollisionAPI):
                item['approximation'] = UsdPhysics.MeshCollisionAPI(p).GetApproximationAttr().Get()
            if p.IsA(UsdGeom.Mesh):
                points = np.asarray(UsdGeom.Mesh(p).GetPointsAttr().Get(), dtype=float)
                item['vertices'] = len(points)
            elif p.IsA(UsdGeom.Cube):
                size = UsdGeom.Cube(p).GetSizeAttr().Get()
                points = np.asarray(trimesh.creation.box(extents=[size]*3).vertices)
            elif p.IsA(UsdGeom.Cylinder):
                c = UsdGeom.Cylinder(p)
                item.update(radius_m=c.GetRadiusAttr().Get(),length_m=c.GetHeightAttr().Get(),axis=c.GetAxisAttr().Get())
                assert item['axis']=='Z'
                points = np.asarray(trimesh.creation.cylinder(radius=item['radius_m'],height=item['length_m'],sections=32).vertices)
            else:
                raise AssertionError(p.GetPath())
            assert np.isfinite(points).all()
            mat = np.asarray(cache.GetLocalToWorldTransform(p) * inverse)
            local = (np.c_[points,np.ones(len(points))] @ mat)[:,:3]
            item.update(link_bounds_m=[local.min(0).tolist(),local.max(0).tolist()],
                        link_axis_extents_m=np.ptp(local,axis=0).tolist())
            row['geometries'].append(item)
        assert row['geometries']
        rows.append(row)
    return rows

sources = [*ASSET.parent.rglob('*.usd'),SPAWN,SRC/'assets/robots/g1_29dof.py',SAVED]
hashes = {str(p.relative_to(ROOT)):digest(p) for p in sources}
stage = Usd.Stage.CreateInMemory()
root = stage.DefinePrim('/g1_29dof','Xform')
root.GetReferences().AddReference(str(ASSET))
stage.SetDefaultPrim(root)
before = geometries(stage)
node = next(n for n in ast.parse(SPAWN.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='spawn_walled_robot')
namespace = {'sim_utils':SimpleNamespace(spawn_from_usd=lambda *a,**k:root,find_matching_prims=lambda path:[root])}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(SPAWN),'exec'),namespace)
namespace['spawn_walled_robot']('/g1_29dof',None)
after = geometries(stage)
count = lambda rows:dict(Counter(g['type'] for row in rows for g in row['geometries']))
assert count(before)=={'Mesh':22,'Cube':4,'Cylinder':4},count(before)
assert count(after)=={'Mesh':26,'Cube':4},count(after)
assert len(after)==28
changed=[]
for a,b in zip(before,after):
    assert a['link']==b['link']
    if a!=b:
        changed.append(a['link'])
        assert 'shoulder_pitch' in a['link'] or 'shoulder_roll' in a['link']
        assert b['geometries'][0]['approximation']=='convexHull'
        assert np.allclose(a['geometries'][0]['link_bounds_m'],b['geometries'][0]['link_bounds_m'],atol=1e-7)
assert len(changed)==4
saved=yaml.load(SAVED.read_text(),Loader=yaml.BaseLoader)
robot=saved['scene']['robot']['spawn']
assert robot['func'].endswith(':spawn_walled_robot')
assert robot['articulation_props']['enabled_self_collisions']=='false'
colliding={r['link'] for r in after}
rigid=[p.GetName() for p in Usd.PrimRange(root) if p.HasAPI(UsdPhysics.RigidBodyAPI)]
result=dict(status='PASS',method='CPU authored USD + unmodified production spawn function on transient stage; no PhysX cooking/simulation',
            asset=str(ASSET.relative_to(ROOT)),saved_configuration=str(SAVED.relative_to(ROOT)),
            self_collisions=False,before_geometry_counts=count(before),wall5_geometry_counts=count(after),
            collision_link_count=len(after),shoulder_links_converted=changed,
            rigid_links_without_own_collider=[x for x in rigid if x not in colliding],
            source_rows=before,wall5_rows=after,source_sha256=hashes)
assert all(digest(ROOT/p)==sha for p,sha in hashes.items())
(OUT/'geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('source_rows','wall5_rows','source_sha256')},ensure_ascii=False,indent=2))
for r in after:
    print(r['link'],r['approximation'],[(g['type'],np.round(g['link_axis_extents_m'],5).tolist()) for g in r['geometries']])
