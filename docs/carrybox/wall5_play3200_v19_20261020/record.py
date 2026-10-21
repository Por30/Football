"""Pinned latest rev19 inference video; live training untouched."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import json,hashlib
from pathlib import Path
import torch,numpy as np,imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as common
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];OUT=ROOT/'outputs/carrybox/wall5_play3200_v19_20261020'
SELECTION=json.loads((DOC/'selection.json').read_text())
CKPT=Path(SELECTION['checkpoint']);ITERATION=SELECTION['checkpoint_iteration']
VIDEO=Path(SELECTION['video'])
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_wall5_env_cfg as config
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task

def main():
    torch.set_num_threads(2);assert not VIDEO.exists(),'Preserve existing video; archive failed attempts explicitly'
    digest=hashlib.sha256(CKPT.read_bytes()).hexdigest();checkpoint=torch.load(CKPT,map_location=args.device,weights_only=False)
    assert digest==SELECTION['checkpoint_sha256']
    assert checkpoint['iter']==ITERATION and checkpoint['environment_contract']['migration_revision']==19
    for name,expected in SELECTION['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    cfg=config.CarryBoxWalled5EnvCfg();agent=config.CarryBoxWalled5PPORunnerCfg()
    cfg.scene.num_envs=1;cfg.seed=42;cfg.sim.device=args.device
    cfg.viewer.eye=(2.8,-3.2,2.1);cfg.viewer.lookat=(.65,0.,.65);cfg.viewer.resolution=(1280,720)
    cfg.viewer.origin_type='env';cfg.viewer.env_index=0
    for key in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,key,262144)
    assert cfg.events.push_robot.func is task.push_velocity_increment
    assert cfg.sim.physics_material.static_friction==1. and cfg.scene.ground.spawn.physics_material.friction_combine_mode=='multiply'
    env=task.Wall5CarryBoxEnv(cfg=cfg,render_mode='rgb_array')
    try:
        assert env.checkpoint_contract()==checkpoint['environment_contract'],'Current environment contract mismatch'
        wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=wrapped.reset()
        policy_cfg=agent.policy.to_dict();assert policy_cfg.pop('class_name')=='CarryBoxWall5ActorCritic'
        policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**policy_cfg).to(args.device)
        policy.load_state_dict(checkpoint['model_state_dict'],strict=True);policy.eval()
        saved={k:v.clone() for k,v in policy.state_dict().items()}
        env.set_training_iteration(0);env.set_training_iteration(ITERATION);state=common.state(env)
        expected_yaw=float(np.interp(ITERATION,[0,10000,20000,30000],[0.,10.,30.,180.]))
        assert abs(state.curriculum.degrees-expected_yaw)<1e-6
        push_scale=max(0.,min(1.,(ITERATION-cfg.push_warmup_iterations)/cfg.push_ramp_iterations))
        assert abs(env.step_dt-.02)<1e-9
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21)
        small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
        episodes=[];samples=[];active=False;step=0;original_reset=env._reset_idx
        def reset_capture(ids):
            if active and getattr(env,'_carrybox_in_step',False):
                roll,pitch,_=euler_xyz_from_quat(env.scene['robot'].data.root_quat_w)
                episodes.append(dict(end_step=step+1,skill=int(state.skills[0]),steps=int(state.actual_episode_steps[0]),
                    tipped=bool(task.tipped(env)[0]),fell=bool(common.fallen(env)[0]),timeout=bool(env.termination_manager.time_outs[0]),
                    roll=float(wrap_to_pi(roll)[0]),pitch=float(wrap_to_pi(pitch)[0]),success=bool(state.achieved[0])))
            original_reset(ids)
        env._reset_idx=reset_capture
        with torch.inference_mode():
            obs,_=wrapped.reset();initial_skill=int(state.skills[0]);env.render()
            for _ in range(12):env.sim.render()
            preview=env.render();assert preview.shape==(720,1280,3) and preview.std()>5
            imageio.imwrite(OUT/'initial_scene.png',preview)
            active=True
            with imageio.get_writer(VIDEO,fps=25,codec='libx264',quality=8,pixelformat='yuv420p',macro_block_size=16,
                    ffmpeg_params=['-threads','2','-movflags','+faststart']) as writer:
                frame_count=0
                for step in range(1000):
                    actions=policy.act_inference(obs);assert torch.isfinite(actions).all()
                    obs,reward,done,_=wrapped.step(actions)
                    assert torch.isfinite(reward).all() and all(torch.isfinite(x).all() for x in obs.values())
                    robot=env.scene['robot'].data;box=env.scene['box'].data
                    samples.append(dict(step=step+1,skill=int(state.skills[0]),episode_steps=int(state.actual_episode_steps[0]),
                        robot=robot.root_pos_w[0].tolist(),box=box.root_pos_w[0].tolist(),success=bool(state.achieved[0])))
                    if (step+1)%2==0:
                        # Keep robot and box in view as they move; camera never feeds the actor.
                        rp=robot.root_pos_w[0].cpu().numpy();bp=box.root_pos_w[0].cpu().numpy()
                        target=(rp+bp)*.5;target[2]=.65
                        scale=max(1.,float(np.linalg.norm(rp[:2]-bp[:2]))/3.5)
                        wp=env.scene['wall'].data.root_pos_w[0].cpu().numpy()
                        away=target[:2]-wp[:2];away=away/max(float(np.linalg.norm(away)),1.e-6)
                        eye=target+np.array([away[0]*3.8,away[1]*3.8,3.2])*scale
                        env.sim.set_camera_view(eye=eye.tolist(),target=target.tolist())
                        raw=env.render();assert raw.shape==(720,1280,3) and raw.std()>5
                        frame=Image.fromarray(raw).convert('RGB');draw=ImageDraw.Draw(frame)
                        draw.rectangle((0,0,920,88),fill=(13,20,27))
                        draw.text((15,9),f'G1 Wall5 rev19 | model_{ITERATION} | mean-action play | t={(step+1)*.02:05.2f}s',font=font,fill='white')
                        skill=('loco','pickup','hold')[int(state.skills[0])]
                        draw.text((15,43),f'RSI initialization: {skill} | episode {len(episodes)+1} | resets {len(episodes)} | push scale {push_scale:.2f}',font=small,fill=(215,226,236))
                        if episodes and step+1-episodes[-1]['end_step']<30:
                            event=episodes[-1];reason='timeout' if event['timeout'] else ('tipped' if event['tipped'] else 'fell')
                            draw.rectangle((0,90,640,124),fill=(85,20,20));draw.text((15,95),f'RESET: {reason} after {event["steps"]} steps',font=small,fill='white')
                        depth=obs['perception'][0,-1].cpu().numpy();gray=np.uint8(np.clip(1.-depth,0,1)*255)
                        inset=Image.fromarray(gray).resize((240,135),Image.Resampling.NEAREST).convert('RGB')
                        frame.paste(inset,(1024,565));draw.rectangle((1010,532,1279,562),fill=(13,20,27))
                        draw.text((1019,538),'Actor depth (latest frame)',font=small,fill='white')
                        writer.append_data(np.asarray(frame));frame_count+=1
                        if frame_count in (1,25,50,125,250,375,499,500):frame.save(OUT/f'frame_{frame_count:04d}.png')
                    if (step+1)%100==0:print('RECORD_PROGRESS',step+1,'frames',frame_count,'resets',len(episodes),flush=True)
        assert int(state.skills[0])==0
        assert frame_count==500 and all(torch.equal(v,saved[k]) for k,v in policy.state_dict().items())
        assert hashlib.sha256(CKPT.read_bytes()).hexdigest()==digest
        result=dict(status='PASS',checkpoint=str(CKPT),checkpoint_sha256=digest,checkpoint_iteration=ITERATION,
            environment_contract=env.checkpoint_contract(),source_sha256=SELECTION['source_sha256'],
            strict_load=True,weights_unchanged=True,num_envs=1,seed=42,policy_mode='deterministic_mean',steps=1000,control_hz=50,
            fps=25,frames=frame_count,duration_seconds=20,video=str(VIDEO),initial_skill=initial_skill,episodes=episodes,
            final_censored=dict(skill=int(state.skills[0]),steps=int(state.actual_episode_steps[0]),success=bool(state.achieved[0])),
            yaw_degrees=state.curriculum.degrees,push_scale=push_scale,viewer_eye=cfg.viewer.eye,viewer_lookat=cfg.viewer.lookat,
            video_note='Continuous mean-action play; fixed 1-env midpoint quota is loco; includes every reset; camera tracks robot/box midpoint from opposite side of wall; depth inset is actor latest history frame',training_process_modified=False)
        (DOC/'recording.json').write_text(json.dumps(result,indent=2)+'\n');(DOC/'trajectory.json').write_text(json.dumps(samples)+'\n')
        print('RECORD_PASS',json.dumps(dict(frames=frame_count,resets=len(episodes),video=str(VIDEO))),flush=True)
    finally:env.close()
try:main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:app.close(wait_for_replicator=False)
