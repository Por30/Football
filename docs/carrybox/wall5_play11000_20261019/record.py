"""Strict rev14 inference video; archived physical contract, current training untouched."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import importlib.util,sys,json,hashlib
from pathlib import Path
import torch,numpy as np,imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as common
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];OUT=ROOT/'outputs/carrybox/wall5_play11000_20261019'
CKPT=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/model_11000.pt'
BEFORE=ROOT/'docs/carrybox/wall5_push_20261019/before/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball'
VIDEO=OUT/'wall5_rev14_model11000_play_20s.mp4'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

def main():
    torch.set_num_threads(2);assert not VIDEO.exists(),'Preserve existing video; archive failed attempts explicitly'
    digest=hashlib.sha256(CKPT.read_bytes()).hexdigest();checkpoint=torch.load(CKPT,map_location=args.device,weights_only=False)
    assert checkpoint['iter']==11000 and checkpoint['environment_contract']['migration_revision']==14
    prefix='perceptual_ball.tasks.manager_based.perceptual_ball'
    config=load(prefix+'.rev14_video_cfg',BEFORE/'carrybox_wall5_env_cfg.py')
    task=load(prefix+'.mdp.rev14_video_mdp',BEFORE/'mdp/carrybox_wall5.py')
    cfg=config.CarryBoxWalled5EnvCfg();agent=config.CarryBoxWalled5PPORunnerCfg()
    cfg.scene.num_envs=1;cfg.seed=42;cfg.sim.device=args.device
    cfg.viewer.eye=(2.8,-3.2,2.1);cfg.viewer.lookat=(.65,0.,.65);cfg.viewer.resolution=(1280,720)
    cfg.viewer.origin_type='env';cfg.viewer.env_index=0
    for key in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,key,262144)
    assert cfg.events.push_robot.func is common.push_velocity
    assert cfg.sim.physics_material.static_friction==.5 and cfg.scene.ground.spawn.physics_material.friction_combine_mode=='average'
    env=task.Wall5CarryBoxEnv(cfg=cfg,render_mode='rgb_array')
    try:
        assert env.checkpoint_contract()==checkpoint['environment_contract'],'Historical environment contract mismatch'
        wrapped=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=wrapped.reset()
        policy_cfg=agent.policy.to_dict();assert policy_cfg.pop('class_name')=='CarryBoxWall5ActorCritic'
        policy=CarryBoxWall5ActorCritic(obs,agent.obs_groups,29,**policy_cfg).to(args.device)
        policy.load_state_dict(checkpoint['model_state_dict'],strict=True);policy.eval()
        saved={k:v.clone() for k,v in policy.state_dict().items()}
        env.set_training_iteration(0);env.set_training_iteration(11000);state=common.state(env)
        assert abs(state.curriculum.degrees-12.)<1e-6
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
                        raw=env.render();assert raw.shape==(720,1280,3) and raw.std()>5
                        frame=Image.fromarray(raw).convert('RGB');draw=ImageDraw.Draw(frame)
                        draw.rectangle((0,0,920,88),fill=(13,20,27))
                        draw.text((15,9),f'G1 Wall5 rev14 | model_11000 | mean-action play | t={(step+1)*.02:05.2f}s',font=font,fill='white')
                        skill=('loco','pickup','hold')[int(state.skills[0])]
                        draw.text((15,43),f'RSI initialization: {skill} | episode {len(episodes)+1} | resets {len(episodes)} | original pushes ON',font=small,fill=(215,226,236))
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
        assert frame_count==500 and all(torch.equal(v,saved[k]) for k,v in policy.state_dict().items())
        assert hashlib.sha256(CKPT.read_bytes()).hexdigest()==digest
        result=dict(status='PASS',checkpoint=str(CKPT),checkpoint_sha256=digest,checkpoint_iteration=11000,
            environment_contract=env.checkpoint_contract(),archived_sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BEFORE/'carrybox_wall5_env_cfg.py',BEFORE/'mdp/carrybox_wall5.py']},
            strict_load=True,weights_unchanged=True,num_envs=1,seed=42,policy_mode='deterministic_mean',steps=1000,control_hz=50,
            fps=25,frames=frame_count,duration_seconds=20,video=str(VIDEO),initial_skill=initial_skill,episodes=episodes,
            final_censored=dict(skill=int(state.skills[0]),steps=int(state.actual_episode_steps[0]),success=bool(state.achieved[0])),
            yaw_degrees=state.curriculum.degrees,push_scale=1.,viewer_eye=cfg.viewer.eye,viewer_lookat=cfg.viewer.lookat,
            video_note='Continuous playback including all resets; RSI hold is not pickup from ground; depth inset is actor latest history frame',training_process_modified=False)
        (DOC/'recording.json').write_text(json.dumps(result,indent=2)+'\n');(DOC/'trajectory.json').write_text(json.dumps(samples)+'\n')
        print('RECORD_PASS',json.dumps(dict(frames=frame_count,resets=len(episodes),video=str(VIDEO))),flush=True)
    finally:env.close()
try:main()
finally:app.close(wait_for_replicator=False)
