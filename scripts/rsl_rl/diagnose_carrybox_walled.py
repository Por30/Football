"""Fresh-scene diagnostics; toggled cases are diagnostics, never training readiness."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser()
p.add_argument('--case',choices=['normal','zero','no_rsi','no_mount','no_obstacles','sync_targets','parked','disable_teleport','keep_buffers','height32','bury_platform','no_platform','no_cylinders','mesh_obstacles','mesh_robot_cylinders'],default='normal')
p.add_argument('--iterations',type=int,default=5)
p.add_argument('--num_envs',type=int,default=4)
p.add_argument('--episode',type=float,default=.4)
p.add_argument('--variant',type=int,default=4)
p.add_argument('--output',required=True)
AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_walled_env_cfg as cfgs
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner

def main():
    torch.set_num_threads(2)
    cfg=getattr(cfgs,f'CarryBoxWalled{args.variant}EnvCfg')()
    agent=getattr(cfgs,f'CarryBoxWalled{args.variant}PPORunnerCfg')()
    cfg.scene.num_envs=args.num_envs;cfg.sim.device=args.device;cfg.seed=42;cfg.episode_length_s=args.episode
    agent.algorithm.num_learning_epochs=1;agent.algorithm.num_mini_batches=1
    if args.case=='height32':cfg.scene.depth_camera.height=32
    if args.case=='mesh_robot_cylinders':
        import isaaclab.sim as sim_utils
        import trimesh
        import numpy as np
        from pxr import Usd,UsdGeom,UsdPhysics
        spawn=cfg.scene.robot.spawn.func
        def robot_mesh(path,scfg,**kw):
            prim=spawn(path,scfg,**kw)
            total=0
            for root in sim_utils.find_matching_prims(path):
                for child in list(Usd.PrimRange(root)):
                    if child.IsInstance():child.SetInstanceable(False)
                for child in list(Usd.PrimRange(root)):
                    if child.IsA(UsdGeom.Cylinder) and '/collisions/' in str(child.GetPath()):
                        c=UsdGeom.Cylinder(child);radius=c.GetRadiusAttr().Get();height=c.GetHeightAttr().Get();axis=c.GetAxisAttr().Get()
                        t=None
                        if axis=='X':t=trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0])
                        elif axis=='Y':t=trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0])
                        geometry=trimesh.creation.cylinder(radius=radius,height=height,sections=32,transform=t)
                        child.SetTypeName('Mesh');mesh=UsdGeom.Mesh(child)
                        mesh.CreatePointsAttr().Set(geometry.vertices.tolist())
                        mesh.CreateFaceVertexIndicesAttr().Set(geometry.faces.flatten().tolist())
                        mesh.CreateFaceVertexCountsAttr().Set([3]*len(geometry.faces))
                        mesh.CreateSubdivisionSchemeAttr().Set('none')
                        UsdPhysics.MeshCollisionAPI.Apply(child).CreateApproximationAttr().Set('convexHull')
                        total+=1
            print('REPLACED_ROBOT_COLLISION_CYLINDERS',total,flush=True)
            return prim
        cfg.scene.robot.spawn.func=robot_mesh
    if args.case=='mesh_obstacles':
        import isaaclab.sim as sim_utils
        from pxr import Usd,UsdPhysics
        def spawn_triangle(path,scfg,**kw):
            fn=sim_utils.spawn_mesh_cuboid if hasattr(scfg,'size') else sim_utils.spawn_mesh_cylinder
            prim=fn(path,scfg,**kw)
            for root in sim_utils.find_matching_prims(path):
                for child in Usd.PrimRange(root):
                    if child.HasAPI(UsdPhysics.MeshCollisionAPI):
                        UsdPhysics.MeshCollisionAPI(child).GetApproximationAttr().Set('none')
            return prim
        for n in ('wall','platform'):
            o=getattr(cfg.scene,n);o.spawn=sim_utils.MeshCuboidCfg(size=o.spawn.size,collision_props=o.spawn.collision_props,func=spawn_triangle)
        for i in range(3):getattr(cfg.scene,f'cylinder{i}').spawn.func=spawn_triangle
    if args.case=='no_cylinders':
        for i in range(3):getattr(cfg.scene,f'cylinder{i}').spawn.collision_props.collision_enabled=False
    if args.case=='no_platform':cfg.scene.platform.spawn.collision_props.collision_enabled=False
    if args.case=='bury_platform':
        from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
        reset=cfg.events.reset_box.func
        def reset_without_coplanar(env,ids):
            reset(env,ids)
            pose=task.obstacle_pose(env,'platform')[ids].clone()
            hidden=pose[:,2]-env.scene.env_origins[ids,2]<=-.4+1e-5
            pose[hidden,2]=env.scene.env_origins[ids[hidden],2]-1.4
            task.write_obstacle_pose(env,'platform',pose,ids)
        cfg.events.reset_box.func=reset_without_coplanar
    if args.case=='no_rsi':cfg.reference_init=False
    if args.case=='no_mount':cfg.camera_position_error_m=0;cfg.camera_rotation_error_deg=0
    if args.case=='no_obstacles':
        for n in ('wall','platform','cylinder0','cylinder1','cylinder2'):
            getattr(cfg.scene,n).spawn.collision_props.collision_enabled=False
    if args.case=='parked':
        for i,n in enumerate(('wall','platform','cylinder0','cylinder1','cylinder2')):
            getattr(cfg.scene,n).init_state.pos=(20.+i*10.,0.,-5.)
    if args.case in ('sync_targets','disable_teleport'):
        from isaaclab.assets import RigidObject
        from isaaclab.utils.math import convert_quat
        original=RigidObject.write_root_pose_to_sim
        def teleport(obj,pose,env_ids=None):
            kin=obj.cfg.spawn.rigid_props.kinematic_enabled
            ids=obj._ALL_INDICES if env_ids is None else env_ids
            if kin and args.case=='disable_teleport':
                flag=torch.ones((obj.root_physx_view.count,1),dtype=torch.uint8,device=obj.device)
                obj.root_physx_view.set_disable_simulations(flag,ids)
            original(obj,pose,env_ids)
            if kin and args.case=='disable_teleport':
                obj.root_physx_view.set_disable_simulations(torch.zeros_like(flag),ids)
            if kin and args.case=='sync_targets':
                full=obj.data.root_link_pose_w.clone();full[:,3:]=convert_quat(full[:,3:],to='xyzw')
                ids=obj._ALL_INDICES if env_ids is None else env_ids
                obj.root_physx_view.set_kinematic_targets(full,ids)
        RigidObject.write_root_pose_to_sim=teleport
    if args.case=='keep_buffers':
        from omni.physics.tensors.impl.frontend_torch import FrontendTorch
        retained=[]
        for method in ('as_contiguous_float32','as_contiguous_uint32'):
            orig=getattr(FrontendTorch,method)
            def keep(frontend,value,orig=orig):
                result=orig(frontend,value);retained.append(result);return result
            setattr(FrontendTorch,method,keep)
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    env=gym.make(f'Template-Perceptual-Ball-CarryBox-Walled{args.variant}-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        r=CarryBoxOnPolicyRunner(w,agent.to_dict(),log_dir=str(output/'train'),device=args.device)
        step=w.step;counter=0
        def checked_step(a):
            nonlocal counter
            counter+=1
            torch.cuda.synchronize()
            robot=b.scene['robot'].data;box=b.scene['box'].data
            print('STEP_BEFORE',counter,'action',float(a.abs().max()),'root',robot.root_pos_w.tolist(),
                  'qvel',float(robot.joint_vel.abs().max()),'box',box.root_pos_w.tolist(),flush=True)
            if counter<=2:
                for name in ('box','platform','wall','cylinder0'):
                    o=b.scene[name]
                    if hasattr(o,'root_physx_view'):
                        print('BODY',name,'count',o.root_physx_view.count,'pose',o.root_physx_view.get_transforms().tolist(),'vel',o.root_physx_view.get_velocities().tolist(),flush=True)
            if float(box.root_lin_vel_w.norm(dim=-1).max())>50:
                raise RuntimeError('Box launched above 50 m/s before next physics step')
            result=step(a)
            torch.cuda.synchronize();print('STEP_AFTER',counter,flush=True)
            return result
        w.step=checked_step
        update=r.alg.update
        def checked_update():
            torch.cuda.synchronize();print('UPDATE_BEFORE',flush=True)
            out=update();torch.cuda.synchronize();print('UPDATE_AFTER',flush=True);return out
        r.alg.update=checked_update
        if args.case=='zero':
            with torch.inference_mode():
                for _ in range(args.iterations*24):w.step(torch.zeros(args.num_envs,29,device=args.device))
        else:r.learn(args.iterations,init_at_random_ep_len=False)
        (output/'result.json').write_text(json.dumps(dict(status='PASS',case=args.case,steps=counter,iterations=args.iterations,num_envs=args.num_envs))+'\n')
        print('WALLED_DIAGNOSTIC_PASS',flush=True)
    finally:env.close()
try:main()
except BaseException:
    import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
