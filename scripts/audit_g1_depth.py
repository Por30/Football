"""Audit local G1 model extrinsics and the actual FindBox RTX observation path."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/carrybox/depth_audit'
TASKS=ROOT/'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball'


def geometry():
    import numpy as np
    from scipy.spatial.transform import Rotation
    source=ROOT/'source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/config.yaml'
    urdf=Path(next(line.split(': ',1)[1] for line in source.read_text().splitlines() if line.startswith('asset_path:')))
    files=[urdf,Path('/home/cao/unitree_rl_lab/unitree_ros/robots/g1_description/g1_29dof_rev_1_0.urdf'),
           Path('/home/cao/unitree_rl_lab/unitree_ros/robots/g1_description/g1_29dof.urdf')]
    mounts=[]
    for path in files:
        joint=ET.parse(path).getroot().find("joint[@name='d435_joint']")
        mounts.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
             parent=joint.find('parent').get('link'),child=joint.find('child').get('link'),
             xyz=[float(x) for x in joint.find('origin').get('xyz').split()],
             rpy=[float(x) for x in joint.find('origin').get('rpy').split()]))
    tree=ast.parse((TASKS/'carrybox_env_cfg.py').read_text())
    offset=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='OffsetCfg')
    offset={kw.arg:ast.literal_eval(kw.value) for kw in offset.keywords}
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse((TASKS/'perceptual_ball_env_cfg.py').read_text()).body
               if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('CAMERA_OFFSET_POS','CAMERA_OFFSET_QUAT')}
    expected=Rotation.from_euler('xyz',mounts[0]['rpy'])
    quat=np.array(offset['rot']);actual=Rotation.from_quat(quat[[1,2,3,0]])
    angle=math.degrees((expected.inv()*actual).magnitude())
    assert offset['convention']=='world' and mounts[0]['parent']=='torso_link'
    assert np.allclose(offset['pos'],mounts[0]['xyz'],atol=1e-8) and angle<.05
    fq=np.array(constants['CAMERA_OFFSET_QUAT']);football=Rotation.from_quat(fq[[1,2,3,0]])
    football_forward=football.apply([0.,0.,1.]);carry_forward=actual.apply([1.,0.,0.])
    assert np.allclose(constants['CAMERA_OFFSET_POS'],mounts[0]['xyz'],atol=1e-8)
    report=dict(status='PASS',model_mounts=mounts,findbox_offset=offset,findbox_model_angle_error_deg=angle,
                football_optical_forward=football_forward.tolist(),findbox_forward=carry_forward.tolist(),
                football_mount_position_matches=True,hardware_calibration_verified=False,
                hardware_gap='Actual robot revision, optical-frame calibration, CameraInfo, stream/crop/resize and depth-unit preprocessing not provided',
                football_pipeline='analytic sphere-only; ray range; no scene or self occlusion',
                findbox_pipeline='RTX distance_to_image_plane; optical Z; /3 normalization')
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print('G1_DEPTH_GEOMETRY_PASS',json.dumps(report),flush=True)


def render_audit(args):
    import copy
    import numpy as np
    import torch
    import gymnasium as gym
    import perceptual_ball.tasks
    from PIL import Image,ImageDraw
    from isaaclab.utils.math import quat_apply,quat_apply_inverse,quat_mul,quat_conjugate,quat_from_euler_xyz
    from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_env_cfg import CarryBoxEnvCfg
    from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled3EnvCfg,CarryBoxWalled4EnvCfg
    from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox as base
    from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as wall
    torch.set_num_threads(2)
    cfg={'baseline':CarryBoxEnvCfg,'walled3':CarryBoxWalled3EnvCfg,'walled4':CarryBoxWalled4EnvCfg}[args.variant]()
    cfg.scene.num_envs=1;cfg.sim.device=args.device;cfg.seed=42
    if args.variant=='baseline':
        obstacle_scene=CarryBoxWalled3EnvCfg().scene
        for name in ('wall','cylinder0','cylinder1','cylinder2','platform'):
            setattr(cfg.scene,name,copy.deepcopy(getattr(obstacle_scene,name)))
        task_id='Template-Perceptual-Ball-CarryBox-v0'
    else:
        cfg.reference_init=False
        cfg.depth_noise_std_m=0.;cfg.depth_max_delay_steps=0;cfg.depth_freeze_probability=0.
        cfg.camera_position_error_m=0.;cfg.camera_rotation_error_deg=0.
        task_id=f'Template-Perceptual-Ball-CarryBox-Walled{args.variant[-1]}-v0'
    env=gym.make(task_id,cfg=cfg)
    try:
        b=env.unwrapped
        with torch.inference_mode():
            env.reset()
            robot=b.scene['robot'];camera=b.scene['depth_camera'];torso=robot.find_bodies('torso_link')[0][0]
            frames={}
            def capture(name):
                b.scene.write_data_to_sim();b.sim.forward()
                for _ in range(3):b.sim.render()
                b.scene.update(.02)
                b.common_step_counter+=1
                raw=camera.data.output['distance_to_image_plane'][...,0].clone()
                normalized=base.depth_image(b).clone()
                observations=b.observation_manager.compute(update_history=True)
                torch.testing.assert_close(observations['perception'][:,-1],normalized)
                assert torch.isfinite(normalized).all() and (normalized>=.1/3-1e-5).all() and (normalized<=1.).all()
                torch.testing.assert_close(normalized,torch.nan_to_num(raw,nan=3.,posinf=3.,neginf=3.).clamp(.1,3.)/3.)
                if name:frames[name]=normalized[0].cpu().numpy()
                return raw[0]
            def extrinsics():
                c=camera.data
                q=robot.data.body_quat_w[:,torso]
                pos=quat_apply_inverse(q,c.pos_w-robot.data.body_pos_w[:,torso])
                relative=quat_mul(quat_conjugate(q),c.quat_w_world)
                return pos.clone(),relative.clone()
            capture(None)
            pos,q=extrinsics()
            nominal_pos=torch.tensor(cfg.scene.depth_camera.offset.pos,device=args.device)[None]
            nominal_q=torch.tensor(cfg.scene.depth_camera.offset.rot,device=args.device)[None]
            nominal_q=torch.nn.functional.normalize(nominal_q,dim=-1)
            torch.testing.assert_close(pos,nominal_pos,atol=2e-4,rtol=0)
            assert float((q*nominal_q).sum(-1).abs())>1-1e-5
            initial_camera_pos=camera.data.pos_w.clone()
            # Actual articulation root translation+yaw; the attached sensor must follow it.
            root=robot.data.root_state_w.clone();root[:,0]+=.3;root[:,2]+=.1
            zero=torch.zeros(1,device=args.device)
            root[:,3:7]=quat_from_euler_xyz(zero,zero,zero+.35)
            robot.write_root_state_to_sim(root);capture(None)
            followed_pos,followed_q=extrinsics()
            torch.testing.assert_close(followed_pos,nominal_pos,atol=2e-4,rtol=0)
            assert float((followed_q*nominal_q).sum(-1).abs())>1-1e-5
            assert float((camera.data.pos_w-initial_camera_pos).norm())>.2
            env.reset();capture(None)
            cpos=camera.data.pos_w.clone();cros=camera.data.quat_w_ros.clone();cworld=camera.data.quat_w_world.clone()
            def point(z):
                return cpos+quat_apply(cros,torch.tensor([[0.,0.,z]],device=args.device))
            def place(name,position,orientation=None):
                obj=b.scene[name];p=obj.data.root_state_w.clone();p[:,:3]=position
                p[:,3:7]=cros if orientation is None else orientation;p[:,7:]=0.
                obj.write_root_pose_to_sim(p[:,:7])
            far=b.scene.env_origins+torch.tensor([[10.,10.,3.]],device=args.device)
            for name in ('box','wall','cylinder0','cylinder1','cylinder2','platform'):place(name,far)
            empty=capture('empty')
            place('box',point(1.));clear=capture('box_clear')
            h,w=clear.shape;roi=(slice(h//2-1,h//2+1),slice(w//2-1,w//2+1))
            # Box local Z is optical Z: nearest face at 1 - .25/2 = .875m.
            assert (clear[roi]-.875).abs().max()<.02,clear[roi]
            box_pixels=(clear-empty).abs()>.03
            assert int(box_pixels.sum())>=8
            expected_pose=base.box_pose_target(b)
            torch.testing.assert_close(expected_pose[:,:3],torch.tensor([[0.,0.,1.]],device=args.device),atol=2e-4,rtol=0)
            cases={}
            for name in ('wall','cylinder0'):
                orientation=cworld if name=='wall' else torch.tensor([[1.,0.,0.,0.]],device=args.device)
                place(name,point(.55),orientation)
                blocked=capture(name+'_occludes_box')
                assert (blocked[roi]<clear[roi]-.1).all(),(name,blocked[roi],clear[roi])
                if name=='wall':
                    plane=blocked[h//4:3*h//4,w//4:3*w//4]
                    assert (plane-.45).abs().max()<.02,plane
                place('box',far);hidden_removed=capture(name+'_box_removed')
                # If the obstacle occludes the box, removing the hidden box changes no center rays.
                assert (hidden_removed[roi]-blocked[roi]).abs().max()<.003
                place('box',point(1.));place(name,far);restored=capture(name+'_removed')
                torch.testing.assert_close(restored[roi],clear[roi],atol=.003,rtol=0)
                cases[name]=dict(clear_center_m=clear[roi].mean().item(),blocked_center_m=blocked[roi].mean().item(),
                    hidden_box_removal_max_change_m=(hidden_removed[roi]-blocked[roi]).abs().max().item(),
                    restored_max_error_m=(restored[roi]-clear[roi]).abs().max().item())
            K=camera.data.intrinsic_matrices[0].cpu().tolist()
            # Inspect model's own D435 link at the same articulation pose.
            d435=robot.find_bodies('d435_link')[0][0]
            mount=quat_apply_inverse(robot.data.body_quat_w[:,torso],robot.data.body_pos_w[:,d435]-robot.data.body_pos_w[:,torso])
            torch.testing.assert_close(mount,nominal_pos,atol=2e-4,rtol=0)
            report=dict(status='PASS',variant=args.variant,physics_device=args.device,scope='static RTX render / no PPO',
                        nominal_mount_torso_m=pos[0].cpu().tolist(),asset_d435_mount_torso_m=mount[0].cpu().tolist(),
                        attached_pose_follows_root=True,intrinsics=K,resolution=[w,h],
                        vfov_deg=math.degrees(2*math.atan(h/(2*K[1][1]))),hfov_deg=math.degrees(2*math.atan(w/(2*K[0][0]))),
                        observation_matches_rendered_depth=True,optical_z_verified=True,occlusion=cases,
                        probe_overrides='one environment; walled RSI/mount noise/depth noise/delay/freeze disabled for deterministic geometry',
                        hardware_calibration_verified=False)
            OUT.mkdir(parents=True,exist_ok=True)
            (OUT/f'{args.variant}.json').write_text(json.dumps(report,indent=2)+'\n')
            np.savez_compressed(OUT/f'{args.variant}_depth.npz',**frames)
            tile_w,tile_h=384,280
            image=Image.new('RGB',(tile_w*3,tile_h*3),(25,25,25));draw=ImageDraw.Draw(image)
            for i,(name,depth) in enumerate(frames.items()):
                x=(i%3)*tile_w;y=(i//3)*tile_h
                gray=Image.fromarray((np.clip(depth,0,1)*255).astype('uint8')).convert('RGB')
                image.paste(gray.resize((384,h*8),Image.Resampling.NEAREST),(x,y+24))
                draw.text((x+5,y+5),name,fill='white')
            image.save(OUT/f'{args.variant}.png')
            print('G1_DEPTH_RENDER_PASS',json.dumps(report),flush=True)
    finally:env.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry-only',action='store_true')
    parser.add_argument('--variant',choices=['baseline','walled3','walled4'],default='walled4')
    if '--geometry-only' in sys.argv:
        parser.parse_args();geometry();return
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(parser);args=parser.parse_args();app=AppLauncher(args).app
    try:render_audit(args)
    except BaseException:
        import traceback;traceback.print_exc();raise
    finally:app.close(wait_for_replicator=False)

if __name__=='__main__':main()
