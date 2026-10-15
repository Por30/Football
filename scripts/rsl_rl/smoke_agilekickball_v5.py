"""Four-env depth geometry, PPO/AMP, resume and export smoke; no formal run."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();parser.add_argument('--output',default='docs/agilekickball_v5/validation');AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import copy
import json
from pathlib import Path
import torch
import numpy as np
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab.sensors import TiledCameraCfg
from isaaclab.sim import PinholeCameraCfg
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply, quat_mul, matrix_from_quat
from perceptual_ball.carrybox_camera import FabricTiledCamera
from perceptual_ball.carrybox_warp_camera import WarpDepthCameraCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v4_env_cfg import AgileKickballV4EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_v5_env_cfg import AgileKickballV5EnvCfg, AgileKickballV5PPORunnerCfg
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import export_depth_policy


def main():
    torch.set_num_threads(2)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    cfg,agent=AgileKickballV5EnvCfg(),AgileKickballV5PPORunnerCfg()
    old=AgileKickballV4EnvCfg()
    assert old.observations.perception.depth_image.func.__name__=='synthetic_ball_depth_image'
    assert not hasattr(old.scene,'depth_camera')
    assert WarpDepthCameraCfg().object_names==('Box','Wall','Cylinder0','Cylinder1','Cylinder2','Platform')
    assert WarpDepthCameraCfg().intrinsics is None
    cfg.scene.num_envs=4;cfg.sim.device=args.device;cfg.seed=42
    p=cfg.camera_profile;fx,fy,cx,cy=cfg.scene.depth_camera.intrinsics
    cfg.scene.depth_reference=TiledCameraCfg(class_type=FabricTiledCamera,
        prim_path='{ENV_REGEX_NS}/Robot/torso_link/DepthReference',width=48,height=27,
        update_period=.02,update_latest_camera_pose=True,data_types=['distance_to_image_plane'],offset=cfg.scene.depth_camera.offset,
        spawn=PinholeCameraCfg(focal_length=18.,horizontal_aperture=18.*48/fx,
            vertical_aperture=18.*27/fy,clipping_range=(.1,3.)))
    env=gym.make('Template-Perceptual-Ball-AgileKickball-v5',cfg=cfg)
    wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);b=env.unwrapped
    cam,ref=b.scene['depth_camera'],b.scene['depth_reference']
    comparisons=[]
    try:
        with torch.inference_mode():
            obs,_=wrapped.reset()
            assert obs['perception'].shape==(4,8,27,48)
            # Same capture is immutable under repeated observation/diagnostic reads.
            first=cam.data.output['distance_to_image_plane'].clone();count=cam.capture_count.clone()
            for _ in range(3):
                torch.testing.assert_close(cam.data.output['distance_to_image_plane'],first,atol=0,rtol=0)
            torch.testing.assert_close(cam.capture_count,count,atol=0,rtol=0)
            clean=cam.data.output['distance_to_image_plane_clean']
            assert (first[clean>=3.] == 3.).all()
            assert ((first-clean).abs()>1.e-6).any()
            robot=b.scene['robot']
            def check_gains(nominal=False):
                kp=robot.data.joint_stiffness;kd=robot.data.joint_damping
                for actual,default,bounds in ((kp,robot.data.default_joint_stiffness,cfg.kp_scale_range),(kd,robot.data.default_joint_damping,cfg.kd_scale_range)):
                    ratio=actual/default
                    if nominal:torch.testing.assert_close(ratio,torch.ones_like(ratio),atol=1.e-6,rtol=0)
                    else:assert ((ratio>=bounds[0]-1.e-6)&(ratio<=bounds[1]+1.e-6)).all()
                torch.testing.assert_close(robot.root_physx_view.get_dof_stiffnesses().to(kp.device),kp)
                torch.testing.assert_close(robot.root_physx_view.get_dof_dampings().to(kd.device),kd)
                for actuator in robot.actuators.values():
                    torch.testing.assert_close(actuator.stiffness,kp[:,actuator.joint_indices])
                    torch.testing.assert_close(actuator.damping,kd[:,actuator.joint_indices])
                return kp.clone(),kd.clone()
            check_gains()
            for _ in range(2):wrapped.reset();check_gains()
            off=AgileKickballV5EnvCfg(randomize_gains=False,randomize_depth=False)
            assert not off.scene.depth_camera.noise_enabled
            assert off.events.randomize_motor_gains.params['stiffness_distribution_params']==(1.,1.)
            gain_term=b.event_manager.get_term_cfg('randomize_motor_gains')
            params=dict(gain_term.params,stiffness_distribution_params=(1.,1.),damping_distribution_params=(1.,1.))
            gain_term.func(b,None,**params);check_gains(nominal=True)
            wrapped.reset();check_gains()
            timings={}
            import time
            torch.cuda.synchronize();start=time.perf_counter()
            for _ in range(10):gain_term.func(b,torch.arange(4,device=args.device),**gain_term.params)
            torch.cuda.synchronize();timings['gain_reset_4env_mean_ms']=(time.perf_counter()-start)*100.
            raw=cam.clean_depth.view(4,27,48)
            torch.cuda.synchronize();start=time.perf_counter()
            for _ in range(20):cam.randomizer.apply(raw,torch.arange(4,device=args.device))
            torch.cuda.synchronize();timings['noise_4env_mean_ms']=(time.perf_counter()-start)*50.

            assert len(cam.mesh_manifest)==38
            from pxr import UsdPhysics, UsdGeom
            collider=cam.stage.GetPrimAtPath('/World/envs/env_0/Ball/geometry/mesh')
            visual=cam.stage.GetPrimAtPath('/World/envs/env_0/Ball/geometry/depth_visual')
            assert collider.IsA(UsdGeom.Sphere) and collider.HasAPI(UsdPhysics.CollisionAPI)
            assert not visual.HasAPI(UsdPhysics.CollisionAPI)
            assert UsdGeom.Imageable(collider).ComputeVisibility()=='invisible'
            roots=[x['root'] for x in cam.mesh_manifest]
            assert '/World/ground' in roots and '/World/envs/env_0/Ball' in roots
            torso=b.scene['robot'].find_bodies('torso_link')[0][0]
            def compare(name,check_mount=True):
                from isaaclab.utils.math import convert_camera_frame_orientation_convention as convert
                ref.set_mount_poses(cam._offset_pos, convert(cam._offset_quat, origin='world', target='opengl'), torch.arange(4,device=args.device))
                b.scene.write_data_to_sim();b.sim.forward();b.sim.render();b.scene.update(.02)
                cam._is_outdated[:]=True;ref._is_outdated[:]=True
                actual=cam.data.output['distance_to_image_plane_clean'][...,0].clone()
                expected=ref.data.output['distance_to_image_plane'][...,0].nan_to_num(nan=3.,posinf=3.).clamp(.1,3.)
                error=(actual-expected).abs()
                interior=torch.ones_like(expected,dtype=torch.bool)
                for dim in (1,2):
                    for shift in (-1,1):interior &= (expected-expected.roll(shift,dim)).abs()<.1
                interior[:,[0,-1],:]=False;interior[:,:,[0,-1]]=False
                row=dict(name=name,max_m=error.max().item(),interior_max_m=error[interior].max().item(),fraction_over_2cm=(error>.02).float().mean().item())
                torch.save(dict(warp=actual.cpu(),rtx=expected.cpu(),warp_pos=cam.data.pos_w.cpu(),rtx_pos=ref.data.pos_w.cpu(),warp_q=cam.data.quat_w_world.cpu(),rtx_q=ref.data.quat_w_world.cpu(),warp_K=cam.data.intrinsic_matrices.cpu(),rtx_K=ref.data.intrinsic_matrices.cpu()),out/(name+'_comparison.pt'))
                comparisons.append(row);(out/'comparisons.json').write_text(json.dumps(comparisons,indent=2))
                assert row['interior_max_m']<.002 and row['fraction_over_2cm']<.01,row
                if check_mount:
                    r=b.scene['robot'].data
                    pos=r.body_link_pos_w[:,torso]+quat_apply(r.body_link_quat_w[:,torso],cam._offset_pos)
                    torch.testing.assert_close(cam.data.pos_w,pos,atol=2e-4,rtol=0)
                torch.testing.assert_close(cam.data.pos_w,ref.data.pos_w,atol=2e-4,rtol=0)
                torch.testing.assert_close(matrix_from_quat(cam.data.quat_w_world),matrix_from_quat(ref.data.quat_w_world),atol=2e-5,rtol=0)
                return actual
            compare('reset')
            for i in range(12):
                obs,reward,done,info=wrapped.step(torch.zeros(4,29,device=args.device))
                assert all(torch.isfinite(v).all() for v in obs.values())
                torch.testing.assert_close(obs['perception'][:,-1],cam.data.output['distance_to_image_plane'][...,0])
                compare('motion_'+str(i))
            counts=cam.capture_count.clone();before=cam.data.output['distance_to_image_plane'].clone()
            kp,kd=check_gains()
            parameters={k:v.clone() for k,v in cam.randomizer.parameters.items()}
            b._reset_idx(torch.tensor([3,1],device=args.device))
            check_gains()
            torch.testing.assert_close(robot.data.joint_stiffness[[0,2]],kp[[0,2]],atol=0,rtol=0)
            torch.testing.assert_close(robot.data.joint_damping[[0,2]],kd[[0,2]],atol=0,rtol=0)
            for k,v in cam.randomizer.parameters.items():
                torch.testing.assert_close(v[[0,2]],parameters[k][[0,2]],atol=0,rtol=0)
            after=cam.data.output['distance_to_image_plane']
            torch.testing.assert_close(after[[0,2]],before[[0,2]],atol=0,rtol=0)
            torch.testing.assert_close(cam.capture_count[[0,2]],counts[[0,2]])
            assert (cam.capture_count[[3,1]]==1).all()
            compare('reverse_partial_reset')
            # A slower sensor holds the already-noisy frame across policy reads.
            cam.cfg.update_period=.04
            cam.data
            saved=cam.data.output['distance_to_image_plane'].clone();counts=cam.capture_count.clone()
            cam.update(.02)
            torch.testing.assert_close(cam.data.output['distance_to_image_plane'],saved,atol=0,rtol=0)
            torch.testing.assert_close(cam.capture_count,counts)
            cam.update(.02);cam.data
            torch.testing.assert_close(cam.capture_count,counts+1)
            assert not torch.equal(cam.data.output['distance_to_image_plane'],saved)
            cam.cfg.update_period=.02

            # Controlled camera/ball test: static camera does not depend on robot articulation.
            origins=b.scene.env_origins
            identity=torch.tensor([1.,0.,0.,0.],device=args.device).expand(4,4)
            def view(pos,q):
                for c in (cam,ref):c.set_world_poses(origins+torch.tensor(pos,device=args.device),q,convention='world')
            def ball(pos):
                pose=torch.cat((origins+torch.tensor(pos,device=args.device),identity),-1)
                b.scene['ball'].write_root_state_to_sim(torch.cat((pose,torch.zeros(4,6,device=args.device)),-1))
            view([1.,0.,1.],identity);ball([2.,0.,1.]);visible=compare('ball_near',False)
            assert ((visible[:,13,24]>.87)&(visible[:,13,24]<.92)).all()
            # Independent ideal-sphere reference, not the coarse default RTX sphere.
            rays=cam._rays
            projection=rays[:,0]  # Ball centre exactly 1 m down the +X optical axis.
            discriminant=.11**2-(1.-projection.square())
            hit=discriminant>0
            ideal=(projection[hit]-discriminant[hit].sqrt())*rays[hit,0]
            torch.testing.assert_close(visible.flatten(1)[:,hit],ideal.expand(4,-1),atol=.002,rtol=0)
            ball([2.5,0.,1.]);farther=compare('ball_far',False)
            assert (farther[:,13,24]-visible[:,13,24]>.45).all()
            # Torso blocks a ball placed behind the robot, independent of hidden ball motion.
            # Anchor to the actual torso after randomized gains/resets, not a world
            # point that may miss a translated/tilted robot and expose the ball.
            torso_q=robot.data.body_link_quat_w[:,torso]
            centre=robot.data.body_link_pos_w[:,torso]+quat_apply(torso_q,torch.tensor([0.,0.,.18],device=args.device).expand(4,3))
            forward=quat_apply(torso_q,torch.tensor([1.,0.,0.],device=args.device).expand(4,3))
            back=quat_mul(torso_q,torch.tensor([0.,0.,0.,1.],device=args.device).expand(4,4))
            for c in (cam,ref):c.set_world_poses(centre+1.2*forward,back,convention='world')
            def behind_torso(distance):
                pose=torch.cat((centre-distance*forward,identity,torch.zeros(4,6,device=args.device)),-1)
                b.scene['ball'].write_root_state_to_sim(pose)
            behind_torso(.6);blocked=compare('body_blocks_ball',False)
            behind_torso(1.);hidden=compare('hidden_ball_moved',False)
            torch.testing.assert_close(blocked[:,13,24],hidden[:,13,24],atol=1e-4,rtol=0)
            assert (blocked[:,13,24]<1.4).all()
            from PIL import Image
            panels=[]
            for title,frame in [('visible',visible),('self_occlusion',blocked)]:
                torch.save(frame.cpu(),out/(title+'.pt'))
                panels.append(Image.fromarray((frame[0].cpu().numpy()/3.*255).astype('uint8')).resize((480,270)))
            panel=Image.new('L',(960,270));panel.paste(panels[0],(0,0));panel.paste(panels[1],(480,0));panel.save(out/'depth.png')
            # Restore original camera mount for actual PPO updates.
            from isaaclab.utils.math import convert_camera_frame_orientation_convention as convert
            ids=torch.arange(4,device=args.device)
            pos=torch.tensor(p['position_m'],device=args.device).repeat(4,1)
            q=torch.tensor(p['quaternion_wxyz_world'],device=args.device).repeat(4,1)
            for c in (cam,ref):c.set_mount_poses(pos,convert(q,origin='world',target='opengl'),ids)
            wrapped.reset()
        runner=BallRegressionOnPolicyRunner(wrapped,agent.to_dict(),log_dir=str(out/'train'),device=args.device)
        runner.learn(2,init_at_random_ep_len=True)
        checkpoint=out/'validation_model.pt';runner.save(str(checkpoint))
        # Match train/play: load into a fresh runner, not inference-mode normalizer buffers
        # mutated by a completed learn() in the same Python object.
        runner=BallRegressionOnPolicyRunner(wrapped,agent.to_dict(),log_dir=str(out/'resumed'),device=args.device)
        runner.load(str(checkpoint));runner.learn(1)
        for model in (runner.alg.policy,runner.alg.amp):
            assert all(torch.isfinite(v).all() for v in model.state_dict().values())
        state=torch.load(checkpoint,weights_only=False,map_location='cpu')
        key='agile_v5_scene_depth_curriculum'
        assert state[key]['config']['depth_contract']==b.depth_contract
        for kind in ('missing','different','randomization','old_revision'):
            broken=copy.deepcopy(state)
            if kind=='missing':del broken[key]
            elif kind=='different':broken[key]['config']['depth_contract']['profile']['depth_unit_m']=1.
            elif kind=='randomization':broken[key]['config']['depth_contract']['training_randomization']['gains']['kp_scale_range']=[.8,1.2]
            else:broken[key]['config']['revision']='scene_depth_self_occlusion_20261014'
            path=out/('invalid_'+kind+'.pt');torch.save(broken,path)
            try:runner.load(str(path),load_optimizer=False)
            except ValueError:pass
            else:raise AssertionError('Invalid camera checkpoint accepted')
        for method in (runner.warm_start_from_v2,runner.warm_start_from_v3):
            try:method(str(checkpoint))
            except ValueError:pass
            else:raise AssertionError('Old warm start accepted')
        with torch.inference_mode():
            obs=wrapped.get_observations()
            wrapper=export_depth_policy(runner.alg.policy,obs,out/'export',{'depth_contract':b.depth_contract})
            flat=obs['proprio_hist'][:1].cpu();depth=obs['perception'][:1].cpu()
            expected=runner.alg.policy.act_inference(obs)[:1].cpu()
            torch.testing.assert_close(wrapper(flat,depth),expected,atol=2e-5,rtol=2e-5)
            torch.testing.assert_close(torch.jit.load(str(out/'export/policy.pt'))(flat,depth),expected,atol=2e-5,rtol=2e-5)
            import onnxruntime as ort
            session=ort.InferenceSession(str(out/'export/policy.onnx'),providers=['CPUExecutionProvider'])
            actual=session.run(None,{'flat':flat.numpy(),'depth':depth.numpy()})[0]
            np.testing.assert_allclose(actual,expected.numpy(),atol=2e-5,rtol=2e-5)
        report=dict(status='PASS',num_envs=4,iterations=3,mesh_manifest=cam.mesh_manifest,
                    comparisons=comparisons,depth_contract=b.depth_contract,randomization_timings=timings,
                    hardware_calibration_verified=False,formal_training_started=False)
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print('AGILEKICKBALL_V5_PASS',flush=True)
    finally:env.close()

try:main()
except Exception:
    import traceback
    traceback.print_exc()
    raise
finally:app.close()
