"""Four simultaneous wall11 environments, higher spectator cameras, no training."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import hashlib
import json
from pathlib import Path
import numpy as np
import torch
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont
from pxr import UsdGeom
import omni.usd
import omni.replicator.core as rep
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat, wrap_to_pi, matrix_from_quat
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import CarryBoxWall10ActorCritic
from perceptual_ball.tasks.manager_based.perceptual_ball import carrybox_wall11_env_cfg as config
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall11 as task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall10 as state_task
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox as base_task

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
OUT = ROOT/'outputs/carrybox/wall11_play4_20261024_2326'
SELECTION = json.loads((DOC/'selection.json').read_text())
CKPT, VIDEO = Path(SELECTION['checkpoint']), Path(SELECTION['video'])
ITERATION = SELECTION['checkpoint_iteration']
WIDTH, HEIGHT = 960, 540


def main():
    torch.set_num_threads(2)
    assert not VIDEO.exists(), 'Preserve prior outputs'
    digest = hashlib.sha256(CKPT.read_bytes()).hexdigest()
    assert digest == SELECTION['checkpoint_sha256']
    checkpoint = torch.load(CKPT, map_location=args.device, weights_only=False)
    assert checkpoint['iter'] == ITERATION
    assert checkpoint['environment_contract']['variant'] == 'walled11'
    assert checkpoint['environment_contract']['migration_revision'] == 1
    assert checkpoint['amp']['config']['rollout_steps'] == 24
    assert checkpoint['environment_contract']['critic'] == 'proprio93_ends15_lin3_box12'
    assert checkpoint['amp']['dataset']['clip_count'] == 15
    assert checkpoint['environment_contract']['depth']['units'] == 'metres'
    for name, expected in SELECTION['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    cfg, agent = config.CarryBoxWalled11EnvCfg(), config.CarryBoxWalled11PPORunnerCfg()
    cfg.scene.num_envs, cfg.seed, cfg.sim.device = 4, 42, args.device
    cfg.sim.render.enable_direct_lighting = True
    cfg.viewer.eye, cfg.viewer.lookat = (3.6, -3.6, 5.8), (0., 0., .6)
    cfg.viewer.resolution = (WIDTH, HEIGHT)
    for key in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity',
                'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, key, 262144)
    env = task.Wall11CarryBoxEnv(cfg=cfg, render_mode='rgb_array')
    annotators, products, camera_paths = [], [], []
    try:
        assert env.checkpoint_contract() == checkpoint['environment_contract']
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = wrapped.reset()
        policy_cfg = agent.policy.to_dict()
        assert policy_cfg.pop('class_name') == 'CarryBoxWall10ActorCritic'
        policy = CarryBoxWall10ActorCritic(obs, agent.obs_groups, 29, **policy_cfg).to(args.device)
        policy.load_state_dict(checkpoint['model_state_dict'], strict=True)
        policy.eval()
        saved = {k: v.clone() for k, v in policy.state_dict().items()}
        state = state_task.state(env)
        assert abs(env.step_dt-.02) < 1e-9

        # Separate render products make every panel refer to its own camera;
        # all four cameras render the same physics state in a single render tick.
        stage = omni.usd.get_context().get_stage()
        for i in range(4):
            camera_path = f'/World/RecordingCamera_{i}'
            camera = UsdGeom.Camera.Define(stage, camera_path)
            camera.GetFocalLengthAttr().Set(20.)
            camera.GetHorizontalApertureAttr().Set(20.955)
            camera.GetVerticalApertureAttr().Set(20.955*HEIGHT/WIDTH)
            camera.GetClippingRangeAttr().Set((.05, 200.))
            product = rep.create.render_product(camera_path, (WIDTH, HEIGHT))
            annotator = rep.AnnotatorRegistry.get_annotator('rgb', device='cpu')
            annotator.attach([product])
            products.append(product)
            annotators.append(annotator)
            camera_paths.append(camera_path)
        assert len(set(camera_paths)) == 4
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
        episodes, samples, camera_records = [], [], []
        reset_counts, latest_events = [0]*4, [None]*4
        active, step = False, 0
        original_reset = env._reset_idx

        def kinds():
            return torch.where(state.default_reset, 0, state.skills+1).tolist()

        def reset_capture(ids):
            if active and getattr(env, '_carrybox_in_step', False):
                roll, pitch, _ = euler_xyz_from_quat(env.scene['robot'].data.root_quat_w)
                for i in ids.tolist():
                    causes = {name: bool(env.termination_manager.get_term(name)[i])
                              for name in env.termination_manager.active_terms}
                    event = dict(env_id=i, end_step=step+1, skill=int(state.skills[i]), kind=kinds()[i],
                        steps=int(env.episode_length_buf[i]), tipped=causes['tipped'], causes=causes,
                        fell=any(causes[name] for name in ('fell_pelvis', 'fell_head', 'fell_hip')),
                        fell_pelvis=causes['fell_pelvis'], fell_head=causes['fell_head'], fell_hip=causes['fell_hip'],
                        box_speed=causes['box_speed'], invalid=causes['invalid'], timeout=causes['time_out'],
                        roll=float(wrap_to_pi(roll)[i]), pitch=float(wrap_to_pi(pitch)[i]),
                        success=bool(state.achieved[i]), from_ground=bool(state.from_ground[i]),
                        box_bottom_clearance=float(geometry()[0][i]), hold_steps=int(state.hold_steps[i]))
                    episodes.append(event)
                    reset_counts[i] += 1
                    latest_events[i] = event
            original_reset(ids)
        env._reset_idx = reset_capture

        def geometry():
            robot, box = env.scene['robot'].data, env.scene['box'].data
            rotation = matrix_from_quat(box.root_quat_w)
            bottom = box.root_pos_w[:, 2] - env.scene.env_origins[:, 2] - (
                rotation[:, 2].abs() * env.scene['depth_camera'].box_sizes / 2).sum(-1)
            ids = state_task.body_ids(env)
            head = robot.body_link_pos_w[:, ids[4], 2] - env.scene.env_origins[:, 2]
            hand_distance = (robot.body_link_pos_w[:, ids[:2]].mean(1)-box.root_pos_w).norm(dim=-1)
            return bottom, head, hand_distance

        def set_views():
            robot = env.scene['robot'].data.root_pos_w.cpu().numpy()
            box = env.scene['box'].data.root_pos_w.cpu().numpy()
            walls = env.scene['wall'].data.root_pos_w.cpu().numpy()
            origins = env.scene.env_origins.cpu().numpy()
            views = []
            for i, path in enumerate(camera_paths):
                target = (robot[i]+box[i])*.5
                target[2] = origins[i, 2]+.6
                scale = max(1., float(np.linalg.norm(robot[i, :2]-box[i, :2]))/3.5)
                away = target[:2]-walls[i, :2]
                away = away/max(float(np.linalg.norm(away)), 1e-6)
                eye = target+np.array([away[0]*3.6, away[1]*3.6, 5.2])*scale
                env.sim.set_camera_view(eye=eye.tolist(), target=target.tolist(), camera_prim_path=path)
                views.append(dict(env_id=i, eye=eye.tolist(), target=target.tolist(),
                                  height_above_ground=float(eye[2]-origins[i, 2])))
            return views

        def read_panels(current_obs, seconds, overlay=True):
            canvas = Image.new('RGB', (WIDTH*2, HEIGHT*2))
            for i, annotator in enumerate(annotators):
                raw = np.array(annotator.get_data(), copy=True)
                assert raw.shape[:2] == (HEIGHT, WIDTH) and raw.shape[2] >= 3, raw.shape
                raw = raw[..., :3]
                assert raw.std() > 5.
                panel = Image.fromarray(raw).convert('RGB')
                if overlay:
                    draw = ImageDraw.Draw(panel)
                    draw.rectangle((0, 0, WIDTH, 65), fill=(13, 20, 27))
                    draw.text((12, 6), f'G1 Wall11 | model_{ITERATION} | Robot {i+1} | t={seconds:05.2f}s',
                              font=font, fill='white')
                    kind = kinds()[i]
                    label = ('DEFAULT: ground box', 'LOCO RSI: ground box',
                             'PICKUP RSI: may start lifted', 'HOLD RSI: starts with box')[kind]
                    color = (220, 232, 242) if kind < 2 else (255, 215, 105)
                    draw.text((12, 35), f'{label} | resets {reset_counts[i]} | hold {int(state.hold_steps[i])*.02:.2f}s',
                              font=small, fill=color)
                    event = latest_events[i]
                    if event and step+1-event['end_step'] < 30:
                        reasons = [k for k in ('timeout', 'tipped', 'fell', 'box_speed', 'invalid') if event[k]]
                        draw.rectangle((0, 68, WIDTH, 98), fill=(85, 20, 20))
                        draw.text((12, 72), f'RESET: {"/".join(reasons)} after {event["steps"]} steps',
                                  font=small, fill='white')
                    depth = current_obs['perception'][i, -1].cpu().numpy()
                    assert depth.min() >= .1 and depth.max() <= 3.
                    # Display only: actor still consumes metres with no division.
                    gray = np.uint8(np.clip(1.-depth/3., 0, 1)*255)
                    panel.paste(Image.fromarray(gray).resize((160, 90), Image.Resampling.NEAREST).convert('RGB'),
                                (WIDTH-170, HEIGHT-100))
                    draw.rectangle((WIDTH-180, HEIGHT-127, WIDTH, HEIGHT-102), fill=(13, 20, 27))
                    draw.text((WIDTH-174, HEIGHT-124), 'Noisy depth (m)', font=small, fill='white')
                    draw.rectangle((0, 0, WIDTH-1, HEIGHT-1), outline=(105, 125, 145), width=2)
                canvas.paste(panel, ((i % 2)*WIDTH, (i // 2)*HEIGHT))
            return canvas

        with torch.inference_mode():
            obs, _ = wrapped.reset()
            initial_skills = state.skills.tolist()
            initial_kinds = kinds()
            initial_states = dict(robot=env.scene['robot'].data.root_pos_w.tolist(),
                box=env.scene['box'].data.root_pos_w.tolist(), from_ground=state.from_ground.tolist(),
                box_bottom_clearance=geometry()[0].tolist(), box_sizes=env.scene['depth_camera'].box_sizes.tolist())
            set_views()
            for _ in range(16):
                env.sim.render()
            read_panels(obs, 0.).save(OUT/'initial_scene.png')
            active = True
            with imageio.get_writer(VIDEO, fps=25, codec='libx264', quality=8,
                    pixelformat='yuv420p', macro_block_size=2,
                    ffmpeg_params=['-threads', '2', '-movflags', '+faststart']) as writer:
                frame_count = 0
                for step in range(1000):
                    actions = policy.act_inference(obs)
                    assert torch.isfinite(actions).all()
                    obs, reward, done, _ = wrapped.step(actions)
                    assert torch.isfinite(reward).all() and all(torch.isfinite(x).all() for x in obs.values())
                    # Compare with the exact cached noisy frame used by wall11 actor.
                    torch.testing.assert_close(obs['perception'][:, -1], task.depth_image(env), atol=0, rtol=0)
                    robot, box = env.scene['robot'].data, env.scene['box'].data
                    samples.append(dict(step=step+1, skills=state.skills.tolist(), kinds=kinds(), reset=done.bool().tolist(),
                        episode_steps=env.episode_length_buf.tolist(), robot=robot.root_pos_w.tolist(),
                        box=box.root_pos_w.tolist(), success=state.achieved.tolist(),
                        head_height=geometry()[1].tolist(),
                        hand_box_distance=geometry()[2].tolist(),
                        hand_contacts=base_task.hand_contacts(env).tolist(),
                        box_bottom_clearance=geometry()[0].tolist(),
                        from_ground=state.from_ground.tolist(), hold_steps=state.hold_steps.tolist()))
                    if (step+1) % 2 == 0:
                        views = set_views()
                        before = robot.root_pos_w.clone()
                        physics_time = env.sim.current_time
                        counter = env.common_step_counter
                        env.sim.render()
                        frame = read_panels(obs, (step+1)*.02)
                        assert env.common_step_counter == counter and env.sim.current_time == physics_time
                        assert torch.equal(before, robot.root_pos_w)
                        writer.append_data(np.asarray(frame))
                        frame_count += 1
                        camera_records.append(dict(frame=frame_count, control_step=step+1, views=views))
                        if frame_count in (1, 25, 50, 125, 250, 375, 499, 500):
                            frame.save(OUT/f'frame_{frame_count:04d}.png')
                    if (step+1) % 100 == 0:
                        print('RECORD_PROGRESS', step+1, 'frames', frame_count, 'resets', reset_counts, flush=True)
        assert frame_count == 500 and all(torch.equal(v, saved[k]) for k, v in policy.state_dict().items())
        assert hashlib.sha256(CKPT.read_bytes()).hexdigest() == digest
        result = dict(status='PASS', checkpoint=str(CKPT), checkpoint_sha256=digest,
            checkpoint_iteration=ITERATION, environment_contract=env.checkpoint_contract(),
            source_sha256=SELECTION['source_sha256'], strict_load=True, weights_unchanged=True,
            num_envs=4, seed=42, policy_mode='deterministic_mean', steps=1000, control_hz=50,
            fps=25, frames=frame_count, duration_seconds=20, resolution=[1920, 1080],
            video=str(VIDEO), initial_skills=initial_skills, initial_kinds=initial_kinds,
            reset_sampling='unmodified_wall11_random_hybrid', initial_states=initial_states, episodes=episodes, reset_counts=reset_counts,
            final_censored=[dict(env_id=i, kind=kinds()[i], skill=int(state.skills[i]), steps=int(env.episode_length_buf[i]),
                                 success=bool(state.achieved[i]), from_ground=bool(state.from_ground[i]),
                        box_bottom_clearance=float(geometry()[0][i]), hold_steps=int(state.hold_steps[i])) for i in range(4)],
            disturbance=checkpoint['environment_contract']['disturbance'],
            env_origins=env.scene.env_origins.tolist(), spectator_cameras=camera_paths,
            camera_base_height_m=5.8, previous_camera_base_height_m=5.8,
            spectator_focal_length_mm=20., spectator_direct_lighting=True,
            synchronized_physics_steps=True, rendering_advances_physics=False,
            video_note='2x2 synchronized views; unmodified random source selection; current episode kind labeled; all resets retained; actor depth unchanged',
            actor_depth_units='metres', depth_display_mapping='uint8(255*(1-depth_m/3))_display_only',
            training_process_modified=False)
        for name, expected in SELECTION['source_sha256'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
        (DOC/'recording.json').write_text(json.dumps(result, indent=2)+'\n')
        (DOC/'trajectory.json').write_text(json.dumps(samples)+'\n')
        (DOC/'camera_trajectory.json').write_text(json.dumps(camera_records)+'\n')
        print('RECORD_PASS', json.dumps(dict(frames=frame_count, resets=reset_counts, video=str(VIDEO))), flush=True)
    finally:
        try:
            # This installed Replicator version does not normalize a list of
            # HydraTexture objects in detach(); use its stored string paths.
            for annotator in annotators:
                annotator.detach()
            for product in products:
                product.destroy()
        finally:
            env.close()


try:
    main()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    app.close(wait_for_replicator=False)
