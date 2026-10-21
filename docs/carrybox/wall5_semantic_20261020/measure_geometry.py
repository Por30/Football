"""Read back G1 reference-pose geometry in PhysX; no policy training or dynamics claim."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import hashlib
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab.utils.math import quat_apply, quat_mul, quat_conjugate, yaw_quat
from perceptual_ball.carrybox_amp import joint_mapping
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task

OUT = Path(__file__).resolve().parent


def distribution(values):
    x = torch.tensor(values, dtype=torch.float64)
    return dict(n=len(values), mean=x.mean().item(), min=x.min().item(),
                p05=x.quantile(.05).item(), median=x.quantile(.5).item(),
                p95=x.quantile(.95).item(), max=x.max().item())


def main():
    torch.set_num_threads(2)
    cfg = CarryBoxWalled5EnvCfg()
    cfg.scene.num_envs = 4
    cfg.seed = 42
    cfg.sim.device = args.device
    for key in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity',
                'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, key, 262144)
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0', cfg=cfg)
    try:
        b = env.unwrapped
        env.reset()
        robot = b.scene['robot']
        s = task.state(b)
        mapping = torch.argsort(torch.tensor(joint_mapping(robot.joint_names), device=b.device))
        ids = torch.arange(4, device=b.device)
        records = []
        specs = []
        for clip, (name, group, data) in enumerate(zip(s.library.clip_names, s.library.clip_groups, s.references)):
            n = len(data['joint_position'])
            count = 32 if group == 'carryWith' else 64
            frames = set(torch.linspace(0, n-2, count).long().tolist())
            if group == 'pickUp':
                frames.update(range(32))
                frames.update(torch.linspace(0, n-2, 96).long().tolist())
            specs.extend((clip, f) for f in sorted(frames))

        def refresh():
            b.sim.forward()
            # Advance data-cache time only. There is no physics integration here.
            b.scene.update(b.physics_dt)

        def feet_points():
            values = []
            for foot, points in zip(s.feet, s.foot_support_points):
                q = robot.data.body_link_quat_w[:, foot, None].expand(-1, len(points), -1)
                rotated = quat_apply(q.reshape(-1, 4), points[None].expand(4, -1, -1).reshape(-1, 3))
                values.append(rotated.reshape(4, -1, 3) + robot.data.body_link_pos_w[:, foot, None])
            return torch.cat(values, 1)

        with torch.inference_mode():
            # One nominal default pose, followed by stratified source frames.
            for start in range(-4, len(specs), 4):
                batch = specs[start:start+4] if start >= 0 else [None] * 4
                valid = len(batch)
                batch += [batch[-1]] * (4-valid)
                root = robot.data.default_root_state.clone()
                root[:, :3] = b.scene.env_origins
                root[:, 3:7] = root.new_tensor([1., 0., 0., 0.])
                root[:, 7:] = 0.
                joints = robot.data.default_joint_pos.clone()
                box_delta = torch.zeros(4, 3, device=b.device)
                for i, spec in enumerate(batch):
                    if spec is None:
                        root[i, 2] += .8
                    else:
                        clip, frame = spec
                        data = s.references[clip]
                        q = s.library.clips[clip][2][frame:frame+1]
                        unyaw = quat_conjugate(yaw_quat(q))
                        root[i, 2] += data['base_height'][frame] + .05
                        root[i, 3:7] = quat_mul(unyaw, q)[0]
                        joints[i] = s.library.clips[clip][0][frame, mapping]
                        box_delta[i] = quat_apply(unyaw, data['box_pos_local'][frame:frame+1])[0]
                robot.write_root_link_state_to_sim(root)
                robot.write_joint_state_to_sim(joints, torch.zeros_like(joints))
                refresh()
                correction = task.reference_ground_correction(b, ids)
                training_root_height = root[:, 2] - b.scene.env_origins[:, 2] + correction
                points = feet_points()
                # Place the lowest actual foot convex-hull point on the ground.
                # This removes the RSI spawn clearance from physical height scaling.
                lowest = points[:, :, 2].amin(-1) - b.scene.env_origins[:, 2]
                root[:, 2] -= lowest
                robot.write_root_link_state_to_sim(root)
                refresh()
                points = feet_points()
                ground = b.scene.env_origins[:, 2]
                torch.testing.assert_close(points[:, :, 2].amin(-1)-ground, torch.zeros_like(ground),
                                           atol=2e-5, rtol=0)
                head = task.head_height(b)
                pelvis = robot.data.root_link_pos_w[:, 2] - ground
                hand = robot.data.body_link_pos_w[:, s.hands].mean(1)
                box = robot.data.root_link_pos_w + box_delta
                gravity = robot.data.projected_gravity_b
                for i, spec in enumerate(batch[:valid]):
                    name, group, frame = ('default_pose', 'default', 0) if spec is None else (
                        s.library.clip_names[spec[0]], s.library.clip_groups[spec[0]], spec[1])
                    records.append(dict(clip=name, group=group, frame=frame,
                        training_reset_pelvis_m=float(training_root_height[i]),
                        grounded_pelvis_m=float(pelvis[i]), grounded_head_com_m=float(head[i]),
                        reference_box_center_m=float(box[i, 2]-ground[i]) if spec is not None else None,
                        hand_to_reference_box_m=float((hand[i]-box[i]).norm()) if spec is not None else None,
                        projected_gravity_xy=float(gravity[i, :2].norm()),
                        foot_front_from_pelvis_m=float(points[i, :, 0].amax()-root[i, 0]),
                        foot_back_from_pelvis_m=float(points[i, :, 0].amin()-root[i, 0])))
                if start < 0:
                    records = records[:1]  # One default pose; no duplicated denominator.
        summaries = {}
        for group in ('default', 'loco_direction', 'pickUp', 'carryWith'):
            rows = [r for r in records if r['group'] == group]
            summaries[group] = {key: distribution([r[key] for r in rows])
                for key in ('grounded_pelvis_m', 'grounded_head_com_m', 'training_reset_pelvis_m',
                            'projected_gravity_xy', 'foot_front_from_pelvis_m')}
            if group != 'default':
                for key in ('reference_box_center_m', 'hand_to_reference_box_m'):
                    summaries[group][key] = distribution([r[key] for r in rows])
        # Equal numbers per walking clip; standing-compatible reference frames.
        upright = [r for r in records if r['group']=='loco_direction' and r['projected_gravity_xy'] < .2]
        held = [r for r in records if r['group']=='carryWith' and r['projected_gravity_xy'] < .2]
        (OUT/'geometry_raw.json').write_text(json.dumps(dict(groups=summaries, records=records,
            counts=dict(loco_upright=len(upright), held_upright=len(held))), indent=2)+'\n')
        assert len(upright) >= 150, (len(upright), len(held))
        assert len(held) >= 20
        clips = sorted({r['clip'] for r in upright})
        assert len(clips) == 11
        per_clip = {name: {key: distribution([r[key] for r in upright if r['clip'] == name])
                          for key in ('grounded_pelvis_m', 'grounded_head_com_m')} for name in clips}
        anchors = dict(pelvis=distribution([r['grounded_pelvis_m']['median'] for r in per_clip.values()])['median'],
                       head=distribution([r['grounded_head_com_m']['median'] for r in per_clip.values()])['median'],
                       box=distribution([r['reference_box_center_m'] for r in held])['median'])
        result = dict(status='PASS', method='PhysX reference-pose FK, minimum foot convex hull grounded; no dynamics or success claim',
            num_envs=4, seed=42, sampling='64 uniform frames per loco clip; 32 hold; pickup 96 plus 64 plus 0..31 prefix',
            source_manifest_sha256=s.library.metadata['manifest_sha256'],
            asset_sha256=hashlib.sha256(Path(cfg.scene.robot.spawn.usd_path).read_bytes()).hexdigest(),
            anchors=anchors, anchor_estimator='median of per-clip medians; gravity XY < 0.2',
            per_clip_upright=per_clip, anchor_counts=dict(loco_upright=len(upright),held_upright=len(held)),
            groups=summaries, records=records, training_updates=0, production_changed=False)
        (OUT/'geometry.json').write_text(json.dumps(result, indent=2)+'\n')
        print('GEOMETRY_PASS', json.dumps(dict(anchors=anchors, groups=summaries)), flush=True)
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
