"""4-env geometry/contact and inference-only integration; no formal training."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser()
parser.add_argument('--legacy',action='store_true')
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app

import json
from pathlib import Path
import numpy as np
import torch
import trimesh
import gymnasium as gym
from pxr import Usd,UsdGeom,UsdPhysics
import omni.physics.tensors.impl.api as physx
import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObjectCfg
from isaaclab.utils.math import quat_apply
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
import perceptual_ball.tasks
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,spawn_walled_robot
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.carrybox_fullbody_collision import ADDED_COLLISION_LINKS,REPLACED_COLLISION_LINKS
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
CHECKPOINT=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a/model_20600.pt'


def main():
    torch.set_num_threads(2)
    cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
    assert CarryBoxWalled4EnvCfg().scene.robot.spawn.func is spawn_walled_robot
    assert not cfg.scene.robot.spawn.articulation_props.enabled_self_collisions
    if args.legacy: cfg.scene.robot.spawn.func=spawn_walled_robot
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    cfg.scene.probe=RigidObjectCfg(prim_path='{ENV_REGEX_NS}/Probe',
        spawn=sim_utils.SphereCfg(radius=.02,activate_contact_sensors=True,
              rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True),
              collision_props=sim_utils.CollisionPropertiesCfg(),mass_props=sim_utils.MassPropertiesCfg(mass=.05)),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(10.,10.,10.)))
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        robot=b.scene['robot'];view=robot.root_physx_view
        physics=physx.create_simulation_view('torch');physics.set_subspace_roots('/')
        runtime=dict(body_names=robot.body_names,joint_names=robot.joint_names,
                     masses=view.get_masses().cpu().tolist(),inertias=view.get_inertias().cpu().tolist(),
                     articulation_shapes=view.max_shapes,
                     per_link_shapes={name:physics.create_rigid_body_view('/World/envs/env_*/Robot/'+name).max_shapes for name in robot.body_names})
        if args.legacy:
            assert runtime['articulation_shapes']==30,runtime['articulation_shapes']
            (OUT/'baseline.json').write_text(json.dumps(runtime,indent=2)+'\n')
            print('FULLBODY_BASELINE_PASS',flush=True);return
        old=json.loads((OUT/'baseline.json').read_text())
        assert runtime['body_names']==old['body_names'] and runtime['joint_names']==old['joint_names']
        assert len(robot.joint_names)==29
        for name in ('masses','inertias'):
            np.testing.assert_allclose(runtime[name],old[name],rtol=1e-6,atol=1e-8)
        assert runtime['articulation_shapes']==35,runtime['articulation_shapes']
        for name in ADDED_COLLISION_LINKS+REPLACED_COLLISION_LINKS:
            assert runtime['per_link_shapes'][name]==1,(name,runtime['per_link_shapes'][name])
        (OUT/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
        scene=b.sim.get_initial_stage();cache=UsdGeom.XformCache()
        contacts={}
        with torch.inference_mode():
            # Targeted sphere contact probes, suspended robot, no policy/episode step.
            for name in ADDED_COLLISION_LINKS+REPLACED_COLLISION_LINKS:
                link=scene.GetPrimAtPath('/World/envs/env_0/Robot/'+name)
                inverse=cache.GetLocalToWorldTransform(link).GetInverse();pts=[]
                for p in Usd.PrimRange(link.GetChild('full_body_collisions'),Usd.TraverseInstanceProxies()):
                    if p.IsA(UsdGeom.Mesh):
                        xyz=np.asarray(UsdGeom.Mesh(p).GetPointsAttr().Get())
                        matrix=np.asarray(cache.GetLocalToWorldTransform(p)*inverse)
                        pts.append((np.c_[xyz,np.ones(len(xyz))]@matrix)[:,:3])
                hull=trimesh.convex.convex_hull(np.concatenate(pts))
                eligible=np.flatnonzero(hull.face_normals[:,0]>.3)
                face=eligible[np.argmax(hull.area_faces[eligible])]
                point=hull.triangles_center[face]+hull.face_normals[face]*.008
                contact=physics.create_rigid_contact_view('/World/envs/env_*/Robot/'+name,
                    filter_patterns=['/World/envs/env_*/Probe'])
                root=robot.data.default_root_state.clone();root[:,:3]+=b.scene.env_origins
                root[:,2]+=3.;root[:,7:]=0
                robot.write_root_state_to_sim(root)
                q=robot.data.default_joint_pos.clone();robot.write_joint_state_to_sim(q,torch.zeros_like(q))
                robot.set_joint_position_target(q)
                b.scene.write_data_to_sim();b.sim.forward();b.scene.update(b.physics_dt)
                body=robot.find_bodies(name,preserve_order=True)[0][0]
                world=robot.data.body_link_pos_w[:,body]+quat_apply(robot.data.body_link_quat_w[:,body],
                    torch.tensor(point,device=b.device,dtype=torch.float32).repeat(4,1))
                pose=b.scene['probe'].data.default_root_state.clone();pose[:,:3]=world;pose[:,7:]=0
                b.scene['probe'].write_root_state_to_sim(pose)
                b.scene.write_data_to_sim();b.sim.forward()
                peak=torch.zeros(4,device=b.device)
                for _ in range(12):
                    b.sim.step(render=False);b.scene.update(b.physics_dt)
                    forces=contact.get_contact_force_matrix(b.physics_dt).reshape(4,-1,3).norm(dim=-1).sum(-1)
                    peak=torch.maximum(peak,forces)
                    assert torch.isfinite(robot.data.root_state_w).all() and torch.isfinite(robot.data.joint_vel).all()
                assert (peak>.01).all(),(name,peak)
                contacts[name]=peak.cpu().tolist()
                print('CONTACT_PASS',name,contacts[name],flush=True)
            # Park the diagnostic object before ordinary task reset/inference.
            pose=b.scene['probe'].data.default_root_state.clone();pose[:,:3]+=b.scene.env_origins
            b.scene['probe'].write_root_state_to_sim(pose)
            for skill in range(3):
                cfg.reset_skill_probabilities=tuple(float(i==skill) for i in range(3))
                obs,_=w.reset()
                assert (task.state(b).skills==skill).all()
                assert all(torch.isfinite(x).all() for x in obs.values())
                assert obs['perception'].shape==(4,4,27,48) and obs['proprio'].shape==(4,372)
                assert obs['amp'].shape==(4,350) and obs['box_pose_target'].shape==(4,9)
                for _ in range(12):
                    obs,reward,done,info=w.step(torch.zeros(4,29,device=b.device))
                    assert all(torch.isfinite(x).all() for x in obs.values()) and torch.isfinite(reward).all()
            cfg.reset_skill_probabilities=(.6,.3,.1)
            obs,_=w.reset()
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=None,device=b.device)
        try:
            runner.load(str(CHECKPOINT),load_optimizer=False)
        except ValueError as e:
            assert 'environment' in str(e)
        else: raise AssertionError('Old collision contract silently accepted')
        runner.warm_start(str(CHECKPOINT));policy=runner.get_inference_policy(device=b.device)
        before={k:v.clone() for k,v in runner.alg.policy.state_dict().items()}
        done_count=0
        with torch.inference_mode():
            for _ in range(200):
                actions=policy(obs);assert torch.isfinite(actions).all()
                obs,reward,done,info=w.step(actions);done_count+=int(done.sum())
                assert all(torch.isfinite(x).all() for x in obs.values()) and torch.isfinite(reward).all()
        assert all(torch.equal(v,before[k]) for k,v in runner.alg.policy.state_dict().items())
        assert not runner.alg.optimizer.state
        runner.save(str(OUT/'model.pt'));runner.load(str(OUT/'model.pt'),load_optimizer=False)
        assert b.checkpoint_contract()['migration_revision']==10
        result=dict(status='PASS',num_envs=4,contact_peak_force_n=contacts,
                    body_count=len(robot.body_names),dof_count=len(robot.joint_names),
                    old_shapes=old['articulation_shapes'],new_shapes=runtime['articulation_shapes'],
                    mass_inertia_match=True,all_three_rsi_finite=True,policy_steps=200,resets=done_count,
                    old_contract_rejected=True,explicit_weights_transfer=True,new_contract_roundtrip=True,
                    policy_parameters_unchanged=True,training_updates=0,environment_contract=b.checkpoint_contract(),
                    limitations='Contact/interface smoke only; no convergence or 4096 throughput conclusion')
        (OUT/'smoke.json').write_text(json.dumps(result,indent=2)+'\n')
        print('FULLBODY_SMOKE_PASS',flush=True)
    finally:env.close()


try:main()
finally:app.close(wait_for_replicator=False)
