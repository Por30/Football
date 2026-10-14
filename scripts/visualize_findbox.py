"""Record all FindBox references on the project's G1 asset; no policy or physics rollout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def verify(output):
    import imageio.v2 as imageio
    import numpy as np
    report = json.loads((output / 'recording.json').read_text())
    if report.get('mode') == 'individual':
        verify_individual(output, report)
        return
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'findbox/amp_manifest.json').read_text())
    assert len(report['clips']) == len(manifest['clips']) == 17
    assert {c['file'] for c in report['clips']} == {c['file'] for c in manifest['clips']}
    for clip in manifest['clips']:
        assert hashlib.sha256((root / 'findbox' / clip['file']).read_bytes()).hexdigest() == clip['sha256']
    reader = imageio.get_reader(output / 'findbox_dataset.mp4')
    metadata = reader.get_meta_data()
    assert metadata['size'] == (960, 720) and abs(metadata['fps'] - 30.) < 1.e-4
    count = 0
    for frame in reader:
        assert frame.shape == (720, 960, 3)
        if count % 30 == 0:
            assert float(np.std(frame[60:680])) > 10., 'Blank rendered frame'
        count += 1
    reader.close()
    assert count == report['video_frames'] == sum(c['video_frames'] for c in report['clips'])
    expected = sum((c['frames'] + 1) // 2 for c in manifest['clips'])
    assert count == expected, 'Not all native 60Hz motion durations are represented at 30fps'
    result = dict(status='PASS', clips=17, decoded_frames=count, fps=30,
                  duration_seconds=count/30, resolution=[960,720], all_source_hashes_unchanged=True)
    (output / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


def verify_individual(output, report):
    import imageio.v2 as imageio
    import numpy as np
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / 'findbox/amp_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == report['dataset']['manifest_sha256']
    rows = {c['file']: c for c in manifest['clips']}
    expected = {report['selected_clip']} if report['selected_clip'] else set(rows)
    assert {c['file'] for c in report['clips']} == expected
    assert len(report['clips']) == len(expected)
    assert report['fps'] == report['source_fps'] == 60 and report['source_frame_step'] == 1
    assert {p.relative_to(output).as_posix() for p in output.rglob('*.mp4')} == {
        c['video'] for c in report['clips']}
    total = 0
    for clip in report['clips']:
        row = rows[clip['file']]
        assert hashlib.sha256((root / 'findbox' / clip['file']).read_bytes()).hexdigest() == row['sha256'] == clip['source_sha256']
        assert clip['source_frames'] == clip['video_frames'] == row['frames']
        assert clip['source_frame_first'] == 0 and clip['source_frame_last'] == row['frames'] - 1
        assert json.loads((output / Path(clip['video']).with_suffix('.json')).read_text()) == clip
        count = 0
        with imageio.get_reader(output / clip['video'], input_params=['-threads', '2']) as reader:
            meta = reader.get_meta_data()
            assert meta['size'] == (960, 720) and abs(meta['fps'] - 60.) < 1.e-4
            for frame in reader:
                assert frame.shape == (720, 960, 3)
                if count % 60 == 0:
                    assert float(np.std(frame[64:686])) > 10., 'Blank rendered frame'
                count += 1
        assert count == row['frames'], clip['file']
        total += count
    assert total == report['video_frames']
    result = dict(status='PASS', clips=len(expected), decoded_frames=total, fps=60,
                  duration_seconds=total/60, resolution=[960,720],
                  all_source_hashes_unchanged=True, source_frame_step=1)
    (output / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--individual', action='store_true', help='Record each PT directly as a separate native 60fps MP4')
    parser.add_argument('--clip', help='Select one relative PT path, e.g. pickUp/pickup1.pt; requires --individual')
    def configure(args):
        if args.clip and not args.individual:
            parser.error('--clip requires --individual')
        if args.output is None:
            args.output = Path('outputs/carrybox/findbox_individual' if args.individual else 'outputs/carrybox/findbox_dataset')
        return args
    if '--verify-only' in sys.argv:
        args = configure(parser.parse_args())
        verify(args.output)
        return
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(parser)
    args = configure(parser.parse_args())
    app = AppLauncher(args).app
    try:
        record(args)
    except BaseException:
        import traceback
        traceback.print_exc()
        sys.stdout.flush(); sys.stderr.flush()
        raise
    finally:
        app.close(wait_for_replicator=False)


def record(args):
    import math
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw, ImageFont
    import omni.replicator.core as rep
    from pxr import Gf, UsdGeom
    import isaaclab.sim as sim_utils
    from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
    from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
    from isaaclab.utils import configclass
    from isaaclab.utils.math import quat_apply, quat_mul, yaw_quat
    from perceptual_ball.assets import G1_29DOF_CFG
    from perceptual_ball.carrybox_amp import FindBoxMotionLibrary, joint_mapping

    torch.set_num_threads(2)
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    library = FindBoxMotionLibrary(root / 'findbox', device='cpu')  # validates actual AMP dataset
    manifest = json.loads((root / 'findbox/amp_manifest.json').read_text())
    priority = {'pickUp': 0, 'carryWith': 1, 'loco_direction': 2}
    rows = sorted(manifest['clips'], key=lambda c: (priority[c['file'].split('/')[0]], c['file']))
    if args.clip:
        rows = [row for row in rows if row['file'] == args.clip]
        if not rows:
            raise ValueError(f'Clip not in manifest: {args.clip}')
    fps, stride = (60, 1) if args.individual else (30, 2)
    if args.individual:
        targets = [out / Path(row['file']).with_suffix('.mp4') for row in rows]
        if (out / 'recording.json').exists() or any(p.exists() for p in targets):
            raise FileExistsError('Individual recording output exists; choose a new --output directory')

    @configclass
    class SceneCfg(InteractiveSceneCfg):
        ground = AssetBaseCfg(prim_path='/World/Ground', spawn=sim_utils.GroundPlaneCfg(size=(100.,100.), color=(.30,.34,.39)))
        light = AssetBaseCfg(prim_path='/World/Light', spawn=sim_utils.DomeLightCfg(intensity=1800.))
        robot: ArticulationCfg = G1_29DOF_CFG.replace(prim_path='{ENV_REGEX_NS}/Robot')
        box = RigidObjectCfg(prim_path='{ENV_REGEX_NS}/Box',
            spawn=sim_utils.CuboidCfg(size=(.30,.30,.25),
                rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True, disable_gravity=True),
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.70,.35,.10))),
            init_state=RigidObjectCfg.InitialStateCfg(pos=(.6,0.,.5)))

    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(device=args.device, dt=1/60))
    scene = InteractiveScene(SceneCfg(num_envs=1, env_spacing=5.))
    stage = sim.get_initial_stage()
    platform = UsdGeom.Cube.Define(stage, '/World/ReferenceSupport')
    platform.CreateSizeAttr(1.)
    platform.CreateDisplayColorAttr([Gf.Vec3f(.21,.27,.34)])
    platform_translate = platform.AddTranslateOp()
    platform_scale = platform.AddScaleOp()
    sim.reset()
    robot, box = scene['robot'], scene['box']
    mapping = joint_mapping(robot.joint_names)
    inverse = torch.argsort(torch.tensor(mapping, device=args.device))
    product = rep.create.render_product('/OmniverseKit_Persp', (960, 624))
    annotator = rep.AnnotatorRegistry.get_annotator('rgb', device='cpu')
    annotator.attach([product])
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font = ImageFont.truetype(font_path, 22)
    small = ImageFont.truetype(font_path, 16)
    def open_writer(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        return imageio.get_writer(path, fps=fps, codec='libx264', quality=8,
                                  pixelformat='yuv420p', macro_block_size=16,
                                  ffmpeg_params=['-threads', '2', '-movflags', '+faststart'])
    writer = None if args.individual else open_writer(out/'findbox_dataset.mp4')
    total = 0; entries=[]
    try:
        for clip_number, row in enumerate(rows, 1):
            video_path = out / Path(row['file']).with_suffix('.mp4')
            if args.individual:
                writer = open_writer(video_path)
            data = torch.load(root/'findbox'/row['file'], map_location=args.device, weights_only=True)
            n = row['frames']
            for field in ('base_position','base_quat','joint_position','box_pos_local'):
                assert torch.isfinite(data[field]).all(), (row['file'], field)
            q = torch.nn.functional.normalize(data['base_quat'][:, [3,0,1,2]].float(), dim=-1)
            first_yaw = yaw_quat(q[:1])
            turn = first_yaw.clone(); turn[:, 1:] *= -1
            turn = turn.expand(n,-1)
            origin = data['base_position'][0].clone(); origin[2]=0.
            pos = quat_apply(turn, (data['base_position'] - origin).float())
            rotation = quat_mul(turn,q)
            box_pos = quat_apply(turn, (data['base_position'] + data['box_pos_local'] - origin).float())
            box_rotation = yaw_quat(rotation)  # box rotation was not recorded
            group = row['file'].split('/')[0]
            if group == 'pickUp':
                contact = int(data['contact_index'])
                center = box_pos[contact].cpu().tolist()
                height = max(.005, center[2] - .125)
                platform_translate.Set(Gf.Vec3d(center[0],center[1],height/2))
                platform_scale.Set(Gf.Vec3d(.4,.4,height))
                platform.MakeVisible()
            else:
                platform.MakeInvisible()
            first = total
            preview_index = (n//2)//stride*stride
            for native in range(0,n,stride):
                pose = torch.cat((pos[native],rotation[native]))[None]
                joints = data['joint_position'][native:native+1, inverse].float()
                robot.write_root_pose_to_sim(pose)
                robot.write_root_velocity_to_sim(torch.zeros((1,6),device=args.device))
                robot.write_joint_state_to_sim(joints,torch.zeros_like(joints))
                box.write_root_pose_to_sim(torch.cat((box_pos[native],box_rotation[native]))[None])
                sim.forward()  # forward kinematics only: no policy actions or physics integration
                focus = pos[native].cpu().numpy().copy(); focus[2]=.70
                eye = focus + np.array([2.7,-3.2,1.75])
                sim.set_camera_view(eye.tolist(), focus.tolist())
                for _ in range(8 if native == 0 else 1):
                    sim.render()
                rgba=np.asarray(annotator.get_data())
                assert rgba.shape[:2] == (624,960), rgba.shape
                canvas=Image.new('RGB',(960,720),(18,24,33))
                canvas.paste(Image.fromarray(rgba[:,:,:3]),(0,64))
                draw=ImageDraw.Draw(canvas)
                label=f"{clip_number:02d}/{len(rows)}  {row['file']}"
                draw.text((20,9),label,font=font,fill=(240,244,250))
                timing = f"G1 reference motion   |   {native/60:.3f} / {(n-1)/60:.3f} s   |   1x speed"
                if args.individual:
                    timing = f"Source frame {native}/{n-1} (0-based)   |   t={native/60:.3f}s   |   60 fps / 1x"
                draw.text((20,39),timing,font=small,fill=(155,189,216))
                note='Kinematic dataset replay - not a trained policy'
                if group != 'loco_direction': note += '  |  Box yaw/support are illustrative'
                draw.text((18,694),note,font=small,fill=(201,210,224))
                draw.rectangle((0,686,int(960*(native+1)/n),689),fill=(74,180,200))
                frame=np.asarray(canvas)
                writer.append_data(frame)
                if native == preview_index:
                    canvas.save(video_path.with_suffix('.png') if args.individual else out/f'preview_{clip_number:02d}.png')
                if native == 0:
                    canvas.save(out/'latest_preview.png')
                total+=1
            entry = dict(file=row['file'],source_frames=n,video_frames=total-first,
                         start_seconds=0. if args.individual else first/fps,
                         end_seconds=(total-first)/fps if args.individual else total/fps,
                         source_sha256=row['sha256'])
            if args.individual:
                writer.close()
                writer = None
                entry.update(video=video_path.relative_to(out).as_posix(), source_frame_first=0,
                             source_frame_last=n-1, source_frame_step=1, fps=fps,
                             source_timestamp_last_seconds=(n-1)/60)
                video_path.with_suffix('.json').write_text(json.dumps(entry,indent=2)+'\n')
            entries.append(entry)
            print(f'RECORDED {clip_number}/{len(rows)} {row["file"]} ({total} frames total)',flush=True)
    finally:
        if writer is not None:
            writer.close()
        annotator.detach()
    report=dict(video=None if args.individual else 'findbox_dataset.mp4',video_frames=total,fps=fps,resolution=[960,720],
                source_fps=60,speed=1.,dataset=library.metadata,clips=entries,
                replay='G1 direct root/joint kinematics; not policy execution',
                display_transform='subtract initial XY and rotate initial yaw to +X; camera follows root XY',
                box_display='recorded base_position + box_pos_local; robot yaw proxy; .30x.30x.25m fixed geometry',
                support_display='pickUp only: illustrative support top inferred at contact_index; not measured geometry')
    if args.individual:
        report.update(mode='individual', selected_clip=args.clip, source_frame_step=1)
    (out/'recording.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FINDBOX_RECORDING_COMPLETE',str(out if args.individual else out/'findbox_dataset.mp4'),flush=True)


if __name__=='__main__':main()
