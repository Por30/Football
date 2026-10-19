"""Read actual USD physics bindings and PhysX shape coefficients from a live scene."""
import torch
from pxr import Usd,UsdPhysics,UsdShade,PhysxSchema

def inspect_materials(env):
    stage=env.sim.get_initial_stage();materials=[];bindings=[]
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.MaterialAPI):
            m=UsdPhysics.MaterialAPI(prim);p=PhysxSchema.PhysxMaterialAPI(prim)
            materials.append(dict(path=str(prim.GetPath()),static=m.GetStaticFrictionAttr().Get(),
                dynamic=m.GetDynamicFrictionAttr().Get(),restitution=m.GetRestitutionAttr().Get(),
                friction_combine=p.GetFrictionCombineModeAttr().Get()))
    for root in ('/World/ground','/World/envs/env_0/Robot','/World/envs/env_0/Box'):
        for prim in Usd.PrimRange(stage.GetPrimAtPath(root),Usd.TraverseInstanceProxies()):
            if not prim.HasAPI(UsdPhysics.CollisionAPI):continue
            material,_=UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial(materialPurpose='physics')
            bindings.append(dict(collider=str(prim.GetPath()),material=str(material.GetPath()) if material else None))
    robot=env.scene['robot'];box=env.scene['box']
    props=robot.root_physx_view.get_material_properties().cpu()
    box_props=box.root_physx_view.get_material_properties().cpu()
    return dict(materials=materials,bindings=bindings,robot_shape=tuple(props.shape),
                robot_env0_coefficients=props[0].tolist(),robot_unique=torch.unique(props.reshape(-1,3),dim=0).tolist(),
                box_coefficients=box_props.tolist(),body_names=robot.body_names)
