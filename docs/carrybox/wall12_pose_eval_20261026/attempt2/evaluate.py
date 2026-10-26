"""Fixed-checkpoint, same-frame depth-to-pose diagnostic; no optimizer updates."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
app=AppLauncher(args).app
from pathlib import Path
import json
import hashlib
from datetime import datetime
import torch
import warp as wp
import numpy as np
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import matrix_from_quat
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall12_env_cfg import CarryBoxWalled12EnvCfg, CarryBoxWalled12PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall10 import variable_box_depth
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox import hand_contacts
from perceptual_ball.rsl_rl_extensions.carrybox_wall12 import CarryBoxWall12OnPolicyRunner
from perceptual_ball.carrybox_wall12 import box_rotations, box_symmetry_mask
from metrics import measurements, summarize

OUT=Path(__file__).resolve().parent
N,STEPS,SEED=64,1000,12345


def main():
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32=True
    torch.backends.cudnn.allow_tf32=True
    analysis=json.loads((OUT/'training_analysis.json').read_text())
    checkpoint=Path(analysis['checkpoint'])
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()==analysis['checkpoint_sha256']
    cfg,agent=CarryBoxWalled12EnvCfg(),CarryBoxWalled12PPORunnerCfg()
    cfg.scene.num_envs=N;cfg.seed=SEED;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled12-v0',cfg=cfg)
    try:
        base=env.unwrapped
        wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        obs,_=wrapped.reset()
        runner=CarryBoxWall12OnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
        runner.load(str(checkpoint),load_optimizer=False)
        policy=runner.alg.policy;policy.eval()
        camera=base.scene['depth_camera']
        ids=torch.arange(N,device=args.device,dtype=torch.int32)
        box_only=torch.full_like(camera._depth,camera.cfg.far)
        saved={k:[] for k in ('prediction','target','visible_pixels','held','ground_start','episode_age')}
        ended=0
        with torch.inference_mode():
            for step in range(STEPS):
                latent=policy.perception_encoder(obs['perception'].float())
                prediction=policy.pose_head(latent)
                action=policy.actor(torch.cat((obs['proprio'].float(),latent),-1))
                target=obs['box_pose_target']
                assert torch.isfinite(prediction).all() and torch.isfinite(target).all()
                if step%100==0:
                    data=camera.data;box=base.scene['box'].data
                    inverse=matrix_from_quat(data.quat_w_ros).transpose(-1,-2)
                    xyz=(inverse@(box.root_pos_w-data.pos_w).unsqueeze(-1)).squeeze(-1)
                    rotation=inverse@matrix_from_quat(box.root_quat_w)
                    expected=torch.cat((xyz,rotation[...,:2].transpose(-1,-2).flatten(-2),camera.box_sizes),-1)
                    torch.testing.assert_close(target,expected,atol=2.e-5,rtol=1.e-5)
                    print(f'EVAL_PROGRESS step={step}/{STEPS}',flush=True)
                # Isolate the box's exact ray intersections, without modifying
                # scene/camera/noise/history/RNG. Compare with clean scene depth.
                box_only.fill_(camera.cfg.far)
                with wp.ScopedStream(wp.stream_from_torch(torch.cuda.current_stream(args.device))):
                    wp.launch(variable_box_depth,dim=(N,len(camera._rays)),inputs=[
                        wp.from_torch(ids),wp.from_torch(camera._data.pos_w,dtype=wp.vec3),
                        wp.from_torch(camera._data.quat_w_world),wp.from_torch(camera._rays,dtype=wp.vec3),
                        wp.from_torch(camera._box_view.get_transforms(),dtype=wp.transform),
                        wp.from_torch(camera.box_sizes,dtype=wp.vec3),camera.cfg.near,camera.cfg.far,
                        wp.from_torch(box_only)],device=args.device)
                visible=((box_only<camera.cfg.far-1.e-5)&((box_only-camera._depth).abs()<1.e-4)).sum(-1)
                box=base.scene['box'].data
                rotation=matrix_from_quat(box.root_quat_w)
                clearance=(box.root_pos_w[:,2]-base.scene.env_origins[:,2]
                           -(rotation[:,2].abs()*camera.box_sizes/2).sum(-1))
                held=hand_contacts(base).all(-1)&(clearance>.10)&(rotation[:,2,2]>.8)
                row=dict(prediction=prediction,target=target,visible_pixels=visible,held=held,
                         ground_start=base._walled.from_ground,episode_age=base.episode_length_buf)
                for key,value in row.items():saved[key].append(value.clone())
                obs,reward,done,extra=wrapped.step(action)
                assert torch.isfinite(reward).all()
                ended+=int(done.sum())
        data={k:torch.stack(v).flatten(0,1).cpu() for k,v in saved.items()}
        assert len(data['prediction'])==N*STEPS
        np.savez_compressed(OUT/'samples.npz',**{k:v.numpy() for k,v in data.items()})
        symmetries=box_rotations(torch.device('cpu'),torch.float64)
        allowed=box_symmetry_mask(data['target'][:,9:].double(),symmetries)
        assert allowed.any(-1).all()
        values=measurements(data['prediction'],data['target'],symmetries,allowed)
        visible=data['visible_pixels']>0;held=data['held'].bool()
        groups={'all':torch.ones(N*STEPS,dtype=torch.bool),'geometrically_visible':visible,
            'not_geometrically_visible':~visible,'at_least_10_visible_pixels':data['visible_pixels']>=10,
            'held':held,'not_held':~held,'visible_and_held':visible&held,
            'ground_start_episodes':data['ground_start'].bool(),
            'reference_airborne_start_episodes':~data['ground_start'].bool(),
            'after_first_4_episode_frames':data['episode_age']>=4}
        result=dict(at=datetime.now().astimezone().isoformat(),status='PASS',checkpoint=str(checkpoint),
            checkpoint_sha256=analysis['checkpoint_sha256'],num_envs=N,steps=STEPS,seed=SEED,
            frames=N*STEPS,sim_seconds_per_env=STEPS*base.step_dt,action_mode='deterministic_mean',
            sampled_episode_terminations=ended,depth_noise=cfg.depth_noise,config_contract=base.checkpoint_contract(),
            geometry_visibility='at least one box-only depth ray equal to clean scene depth within 0.1mm; before sensor noise',
            angular_metric='Gram-Schmidt 6D to SO(3), geodesic angle minimized over size-preserving proper box symmetries',
            aggregation='per-frame, one seed; correlated frames, not episode success rate or real-world accuracy',
            groups={name:summarize(values,mask) for name,mask in groups.items()},
            geometric_visibility_fraction=float(visible.float().mean()),held_fraction=float(held.float().mean()),
            same_frame_checks=True,optimizer_updated=False)
        (OUT/'evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result['groups'],ensure_ascii=False,indent=2),flush=True)
        print('WALL12_POSE_EVAL_PASS',flush=True)
    finally:env.close()


try:main()
except BaseException:
    import traceback
    traceback.print_exc()
    (OUT/'failure.txt').write_text(traceback.format_exc())
    raise
finally:app.close(wait_for_replicator=False)
