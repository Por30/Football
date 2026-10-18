"""Four-env ground-reset geometry and complete PPO/AMP update/restore smoke."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser(); AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app

import copy
import importlib.util
import json
from pathlib import Path
import numpy as np
import torch
import trimesh
import gymnasium as gym
from pxr import Usd,UsdGeom,UsdPhysics
from scipy.spatial.transform import Rotation
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as wall5
from perceptual_ball.carrybox_amp import DEFAULT_DATASET_PATH
from perceptual_ball.carrybox_wall5 import GROUND_DATASET_PATH
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner

OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[2]


def colliders(env):
    # Reuse the previous authored-collider geometry reader, without its stage mocks.
    path=ROOT/'docs/carrybox/wall5_fullbody_20261017/check_geometry.py'
    spec=importlib.util.spec_from_file_location('ground_geometry_reader',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    stage=env.sim.get_initial_stage();cache=UsdGeom.XformCache();result={}
    for name in env.scene['robot'].body_names:
        link=stage.GetPrimAtPath('/World/envs/env_0/Robot/'+name)
        for prim in Usd.PrimRange(link,Usd.TraverseInstanceProxies()):
            if not prim.HasAPI(UsdPhysics.CollisionAPI):continue
            assert UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()=='convexHull'
            points=np.concatenate([module.local_points(p,link,cache) for p in Usd.PrimRange(prim,Usd.TraverseInstanceProxies()) if p.IsA(UsdGeom.Mesh)])
            result[name]=trimesh.convex.convex_hull(points)
    assert len(result)==35
    return result


def penetration(hull, body_pose, box_pose):
    """Convex hull vs oriented box SAT; authored geometry, not a cooked-mesh claim."""
    rb=Rotation.from_quat(body_pose[3:][[1,2,3,0]]).as_matrix()
    ro=Rotation.from_quat(box_pose[3:][[1,2,3,0]]).as_matrix()
    vertices=((hull.vertices@rb.T+body_pose[:3])-box_pose[:3])@ro
    half=np.array([.15,.15,.125])
    if np.any(vertices.min(0)>half) or np.any(vertices.max(0)<-half):return 0.
    normals=hull.face_normals@rb.T@ro
    edges=vertices[hull.edges_unique[:,1]]-vertices[hull.edges_unique[:,0]]
    axes=np.concatenate([np.eye(3),normals,np.cross(edges[:,None,:],np.eye(3)[None,:,:]).reshape(-1,3)])
    norms=np.linalg.norm(axes,axis=1);axes=axes[norms>1e-9]/norms[norms>1e-9,None]
    projection=vertices@axes.T; radius=np.abs(axes)@half
    overlap=np.minimum(projection.max(0)+radius,radius-projection.min(0))
    return max(float(overlap.min()),0.)


def ground_check(b,ids=None):
    bottom,_,_=task.base.lift_geometry(b)
    if ids is None:ids=torch.arange(b.num_envs,device=b.device)
    torch.testing.assert_close(bottom[ids],torch.full_like(bottom[ids],.005),atol=2e-5,rtol=0)
    assert not (task.state(b).skills[ids]==2).any()
    assert torch.isfinite(b.scene['robot'].data.root_state_w).all()


def main():
    torch.set_num_threads(2)
    cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    assert cfg.reset_skill_probabilities==(.7,.3,0.)
    assert cfg.reference_motion_dataset==agent.algorithm.amp_data_dir==GROUND_DATASET_PATH
    assert cfg.scene.platform is None and 'Platform' not in cfg.scene.depth_camera.object_names
    old,old_agent=CarryBoxWalled4EnvCfg(),CarryBoxWalled4PPORunnerCfg()
    assert old.reset_skill_probabilities==(.6,.3,.1) and old.scene.platform is not None
    assert old_agent.algorithm.amp_data_dir==DEFAULT_DATASET_PATH
    cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        robot=b.scene['robot'];s=task.state(b)
        obs,_=w.reset();ground_check(b)
        assert not b.sim.get_initial_stage().GetPrimAtPath('/World/envs/env_0/Platform').IsValid()
        assert not any('/Platform' in m['root'] for m in b.scene['depth_camera'].mesh_manifest)
        assert obs['perception'].shape==(4,4,27,48) and obs['proprio'].shape==(4,372) and obs['amp'].shape==(4,350)
        assert s.library.num_clips==13
        shapes=colliders(b);index={name:robot.body_names.index(name) for name in shapes}
        slot=s.library.clip_names.index('pick_up/pick_up_03.pt');pool=s.ground_reference_frames[slot].clone()
        assert pool.tolist()==list(range(32))
        cfg.reset_skill_probabilities=(0.,1.,0.)
        overlap_rows=[];peak_box_speed=0.;peak_hand_force=0.;worst_overlap=0.
        with torch.inference_mode():
            for frame in pool.tolist():
                s.ground_reference_frames[slot]=torch.tensor([frame],device=b.device)
                obs,_=w.reset();ground_check(b)
                assert all(torch.isfinite(x).all() for x in obs.values())
                poses=torch.cat([robot.data.body_link_pos_w[0],robot.data.body_link_quat_w[0]],-1).cpu().numpy()
                box=b.scene['box'].data.root_state_w[0,:7].cpu().numpy()
                overlaps={name:penetration(h,poses[index[name]],box) for name,h in shapes.items()}
                worst=max(overlaps.values());worst_overlap=max(worst_overlap,worst)
                overlap_rows.append(dict(frame=frame,max_overlap_m=worst,overlaps_m={k:v for k,v in overlaps.items() if v>0}))
                robot.set_joint_position_target(robot.data.joint_pos.clone());b.scene.write_data_to_sim()
                frame_speed=0.
                for _ in range(4):
                    b.sim.step(render=False);b.scene.update(b.physics_dt)
                    assert torch.isfinite(robot.data.root_state_w).all() and torch.isfinite(robot.data.joint_vel).all()
                    assert torch.isfinite(b.scene['box'].data.root_state_w).all()
                    frame_speed=max(frame_speed,float(b.scene['box'].data.root_lin_vel_w.norm(dim=-1).max()))
                    peak_box_speed=max(peak_box_speed,frame_speed)
                    for side in ('left','right'):
                        force=b.scene[f'{side}_box_contact'].data.force_matrix_w
                        assert torch.isfinite(force).all()
                        peak_hand_force=max(peak_hand_force,float(force.norm(dim=-1).max()))
                overlap_rows[-1]['peak_box_speed_first_20ms_m_s']=frame_speed
            (OUT/'reset_geometry.json').write_text(json.dumps(dict(frames=overlap_rows,peak_box_speed_m_s=peak_box_speed,peak_hand_force_n=peak_hand_force),indent=2)+'\n')
            assert worst_overlap<=.003,('RSI robot/box overlap above 3mm',worst_overlap)
            assert peak_box_speed<.3,('Reset collision impulse',peak_box_speed)
            s.ground_reference_frames[slot]=pool
            cfg.reset_skill_probabilities=(1.,0.,0.)
            s.curriculum.set_iteration(0);s.curriculum.set_iteration(30000)
            for _ in range(12):w.reset();ground_check(b)
            cfg.reset_skill_probabilities=(.7,.3,0.)
            obs,_=w.reset()
            # Direct partial reset: surviving physical states and histories remain intact.
            states=robot.data.root_state_w[1:].clone();boxes=b.scene['box'].data.root_state_w[1:].clone()
            histories={g:b.observation_manager.compute_group(g)[1:].clone() for g in ('amp','perception')}
            b._reset_idx(torch.tensor([0],device=b.device));ground_check(b,torch.tensor([0],device=b.device))
            torch.testing.assert_close(robot.data.root_state_w[1:],states)
            torch.testing.assert_close(b.scene['box'].data.root_state_w[1:],boxes)
            for g in histories:torch.testing.assert_close(b.observation_manager.compute_group(g)[1:],histories[g])
            # Force per-env timeout and verify terminal versus reset AMP histories.
            obs,_=w.reset();done_count=0
            for step in range(8):
                previous=obs['amp'].reshape(4,10,35).clone();forced=step%4
                b.episode_length_buf[forced]=b.max_episode_length-1
                obs,reward,done,info=w.step(torch.zeros(4,29,device=b.device))
                assert done[forced] and all(torch.isfinite(x).all() for x in obs.values())
                ids=info['terminal_observations']['env_ids'];ground_check(b,ids)
                terminal=info['terminal_observations']['obs']['amp'].reshape(-1,10,35)
                torch.testing.assert_close(terminal[:,:-1],previous[ids,1:])
                current=obs['amp'].reshape(4,10,35)
                torch.testing.assert_close(current[ids],current[ids,-1:].expand(-1,10,-1))
                torch.testing.assert_close(current[~done.bool(),:-1],previous[~done.bool(),1:])
                done_count+=int(done.sum())
            w.reset()
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'train'),device=b.device)
        for path in (ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a/model_20600.pt',ROOT/'docs/carrybox/wall5_fullbody_20261017/model.pt'):
            try:runner.load(str(path),load_optimizer=False)
            except ValueError as e:assert 'environment' in str(e)
            else:raise AssertionError('Old contract accepted')
        before=copy.deepcopy(runner.alg.policy.state_dict());d_before=copy.deepcopy(runner.alg.amp.state_dict())
        runner.learn(2,init_at_random_ep_len=False)
        assert runner.alg.motion_library.num_clips==13 and runner.alg.amp_valid.all()
        assert any(not torch.equal(v,before[k]) for k,v in runner.alg.policy.state_dict().items())
        assert not torch.equal(d_before['amp_linear.weight'],runner.alg.amp.amp_linear.weight)
        assert runner.alg.optimizer.state and runner.alg.amp_optimizer.state
        runner.save(str(OUT/'model.pt'))
        restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'resumed'),device=b.device)
        restored.load(str(OUT/'model.pt'));restored.learn(1,init_at_random_ep_len=False)
        identity=s.library.metadata['manifest_sha256']
        s.library.metadata['manifest_sha256']='changed-RSI-only'
        try:restored.load(str(OUT/'model.pt'))
        except ValueError as e:assert 'environment' in str(e)
        else:raise AssertionError('Changed RSI identity accepted')
        finally:s.library.metadata['manifest_sha256']=identity
        for model in (restored.alg.policy,restored.alg.amp):assert all(torch.isfinite(v).all() for v in model.state_dict().values())
        for optimizer in (restored.alg.optimizer,restored.alg.amp_optimizer):
            for values in optimizer.state.values():
                for value in values.values():
                    if isinstance(value,torch.Tensor):assert torch.isfinite(value).all()
        assert b.checkpoint_contract()['migration_revision']==11
        result=dict(status='PASS',num_envs=4,ground_reference_frames=pool.tolist(),max_authored_hull_overlap_m=worst_overlap,
            peak_box_speed_first_20ms=peak_box_speed,peak_hand_force_first_20ms=peak_hand_force,
            forced_resets=done_count,partial_reset_preserved=True,history_checks=True,
            training_iterations=2,resumed_iterations=1,old_rev9_rev10_rejected=True,
            environment_contract=b.checkpoint_contract(),dataset=restored.alg.motion_metadata,
            formal_training_started=False,convergence='not_evaluated')
        (OUT/'smoke.json').write_text(json.dumps(result,indent=2)+'\n')
        print('GROUND_SMOKE_PASS',flush=True)
    finally:env.close()


try:main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:app.close(wait_for_replicator=False)
