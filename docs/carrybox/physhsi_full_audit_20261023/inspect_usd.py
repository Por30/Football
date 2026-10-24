"""Read authored USD properties without starting Isaac Sim or GPU physics."""
from pathlib import Path
import json, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '/home/cao/isaacsim/extscache/omni.usd.libs-1.0.1+d02c707b.lx64.r.cp310')
from pxr import Usd, UsdPhysics
R = Path(__file__).resolve().parents[3]
asset = R/'source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/g1_29dof.usd'
stage = Usd.Stage.Open(str(asset))
assert stage
bodies, joints, collisions = {}, {}, []
for prim in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies()):
    attrs = {a.GetName(): str(a.Get()) for a in prim.GetAttributes() if a.HasAuthoredValueOpinion()
             and (a.GetName().startswith(('physics:', 'physx')))}
    if prim.HasAPI(UsdPhysics.MassAPI):
        bodies[prim.GetName()] = dict(path=str(prim.GetPath()), mass=float(UsdPhysics.MassAPI(prim).GetMassAttr().Get()), attrs=attrs)
    if prim.IsA(UsdPhysics.RevoluteJoint): joints[prim.GetName()] = attrs
    if prim.HasAPI(UsdPhysics.CollisionAPI):
        collisions.append(dict(path=str(prim.GetPath()), type=prim.GetTypeName(), attrs=attrs))
root = ET.parse('/home/cao/PhysHSI/legged_gym/resources/robots/g1/urdf/g1_29dof.urdf').getroot()
urdf_mass = {x.attrib['name']:float(x.find('inertial/mass').attrib['value']) for x in root.findall('link') if x.find('inertial/mass') is not None}
deltas = {name:bodies[name]['mass']-mass for name,mass in urdf_mass.items() if name in bodies}
assert len(joints)==29 and len(deltas)==len(urdf_mass)
assert max(abs(v) for v in deltas.values())<1.e-5
print(json.dumps(dict(asset=str(asset), note='Authored asset only; task spawn/config overrides and runtime defaults are separate',
                     urdf_mass_sum=sum(urdf_mass.values()),usd_mass_sum=sum(v['mass'] for v in bodies.values()),
                     mass_max_abs_error=max(abs(v) for v in deltas.values()),bodies=bodies,joints=joints,collisions=collisions)))
