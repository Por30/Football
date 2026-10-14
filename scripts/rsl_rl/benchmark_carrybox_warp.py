"""RTX/Warp correctness, then complete 4096-environment performance acceptance."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument('--num-envs', type=int, required=True)
parser.add_argument('--output', required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app
import cProfile
import json
import pstats
from pathlib import Path
import traceback
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply, quat_mul, matrix_from_quat
from isaaclab.utils.math import convert_camera_frame_orientation_convention as convert
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg, CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox as base
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner


def main():
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    cfg, agent = CarryBoxWalled4EnvCfg(), CarryBoxWalled4PPORunnerCfg()
    cfg.scene.num_envs, cfg.sim.device, cfg.seed = args.num_envs, args.device, 42
    if args.num_envs == 4:
        reference = CarryBoxWalled4EnvCfg(depth_backend='rtx')
        cfg.scene.depth_reference = reference.scene.depth_camera
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0', cfg=cfg)
    b = env.unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    camera = b.scene['depth_camera']
    report = dict(num_envs=args.num_envs, backend=type(camera).__name__,
                  rtx_enabled=b.sim.has_rtx_sensors(), contract=b.checkpoint_contract(),
                  mesh_manifest=camera.mesh_manifest, geometry_free_links=camera.geometry_free_links)
    (out/'initial.json').write_text(json.dumps(report, indent=2)+'\n')
    try:
        with torch.inference_mode():
            wrapped.reset()
            if args.num_envs == 4:
                ref = b.scene['depth_reference']
                ids = torch.arange(4, device=args.device)
                comparisons = []
                def compare(name):
                    # Identical perturbed mounts for independent sensors.
                    ref.set_mount_poses(camera._offset_pos,
                        convert(camera._offset_quat, origin='world', target='opengl'), ids)
                    b.scene.write_data_to_sim(); b.sim.forward(); b.sim.render(); b.scene.update(.02)
                    camera._is_outdated[:] = True; ref._is_outdated[:] = True
                    actual = camera.data.output['distance_to_image_plane'][..., 0].clone()
                    expected = ref.data.output['distance_to_image_plane'][..., 0].nan_to_num(nan=3., posinf=3.).clamp(.1, 3.)
                    error = (actual-expected).abs()
                    # Discontinuities may select adjacent triangles at raster
                    # boundaries; require strict agreement on interior surfaces.
                    interior = torch.ones_like(expected, dtype=torch.bool)
                    for dim in (1, 2):
                        for shift in (-1, 1):
                            interior &= (expected-expected.roll(shift, dim)).abs() < .1
                    interior[:, [0, -1], :] = False; interior[:, :, [0, -1]] = False
                    row = dict(name=name, max_m=error.max().item(), mean_m=error.mean().item(),
                        interior_max_m=error[interior].max().item(), fraction_over_2cm=(error>.02).float().mean().item())
                    comparisons.append(row)
                    (out/'comparisons.json').write_text(json.dumps(comparisons, indent=2)+'\n')
                    torch.save(dict(warp=actual.cpu(), rtx=expected.cpu()), out/(name+'.pt'))
                    assert row['interior_max_m'] < .002, row
                    assert row['fraction_over_2cm'] < .01, row
                    torso = task.state(b).torso
                    robot = b.scene['robot'].data
                    p = robot.body_pos_w[:, torso]+quat_apply(robot.body_quat_w[:, torso], camera._offset_pos)
                    q = quat_mul(robot.body_quat_w[:, torso], camera._offset_quat)
                    torch.testing.assert_close(camera.data.pos_w, p, atol=2e-4, rtol=0)
                    torch.testing.assert_close(matrix_from_quat(camera.data.quat_w_world), matrix_from_quat(q), atol=2e-5, rtol=0)
                    torch.testing.assert_close(camera.data.pos_w, ref.data.pos_w, atol=2e-4, rtol=0)
                    return actual
                compare('reset')
                action = torch.zeros(4, 29, device=args.device)
                for i in range(16):
                    obs, reward, done, info = wrapped.step(action)
                    assert all(torch.isfinite(v).all() for v in obs.values())
                    compare(f'motion_{i}')
                    if i == 7:
                        b._reset_idx(torch.tensor([3, 1], device=args.device))
                        compare('partial_reset')
                cfg.reference_init=False; cfg.search_prob=0.; wrapped.reset()
                q = torch.tensor([1., 0., 0., 0.], device=args.device).expand(4,4)
                def put(name, xyz):
                    pose = torch.cat((b.scene.env_origins+torch.tensor(xyz,device=args.device),q),-1)
                    if name=='box':
                        b.scene[name].write_root_state_to_sim(torch.cat((pose,torch.zeros(4,6,device=args.device)),-1))
                    else: task.write_obstacle_pose(b,name,pose)
                for name in ('wall','cylinder0','cylinder1','cylinder2','platform'):put(name,[10.,0.,-5.])
                camera.set_world_poses(b.scene.env_origins+torch.tensor([0.,0.,1.],device=args.device),q,convention='world')
                put('box',[2.2,0.,1.]);visible=compare('visible_box')
                for name,z in [('wall',1.5),('cylinder0',.9)]:
                    put(name,[1.5,0.,z]);blocked=compare(name)
                    assert ((blocked[:,13,24]>1.2)&(blocked[:,13,24]<1.6)).all()
                    assert (visible[:,13,24]-blocked[:,13,24]>.3).all()
                    put('box',[2.7,0.,1.]);moved=compare(name+'_hidden_move')
                    torch.testing.assert_close(blocked[:,13,24],moved[:,13,24],atol=1e-4,rtol=0)
                    put(name,[10.,0.,-5.]);put('box',[2.2,0.,1.])
                # View back toward the robot: complete body mesh self-occlusion.
                put('box',[10.,0.,-5.])
                back = torch.tensor([0.,0.,0.,1.],device=args.device).expand(4,4)
                camera.set_world_poses(b.scene.env_origins+torch.tensor([.8,0.,.8],device=args.device),back,convention='world')
                body = compare('self_occlusion')
                assert ((body<1.2).float().mean((1,2))>.05).all()
                report['comparisons']=comparisons
        if args.num_envs == 4096:
            assert not b.sim.has_rtx_sensors(), 'Formal Warp path must not enable RTX'
            runner = CarryBoxOnPolicyRunner(wrapped,agent.to_dict(),log_dir=str(out/'train'),device=args.device)
            old=json.loads(Path('docs/carrybox/warp_20261014/stopped_run.json').read_text())
            try: runner.load(old['checkpoint'])
            except ValueError as error:
                assert 'environment' in str(error)
            else: raise AssertionError('Old RTX contract was accepted as exact resume')
            runner.warm_start(old['checkpoint'])
            times=[]
            log=runner.log
            def capture(locs,*a,**kw):
                times.append(dict(collection=locs['collection_time'],learning=locs['learn_time'],
                                  total=locs['collection_time']+locs['learn_time']))
                return log(locs,*a,**kw)
            runner.log=capture
            runner.learn(6,init_at_random_ep_len=True)
            runner.save(str(out/'verification_model.pt'));runner.load(str(out/'verification_model.pt'))
            runner.learn(6)
            for model in (runner.alg.policy,runner.alg.amp):
                assert all(torch.isfinite(v).all() for v in model.state_dict().values())
            report['timings']=times;report['warmup_iterations']=2
            report['target_met']=max(x['total'] for x in times[2:])<=6.
            report['resume']=True
            profile=cProfile.Profile()
            with torch.inference_mode():
                action=torch.zeros(4096,29,device=args.device);profile.enable()
                for _ in range(4):wrapped.step(action);torch.cuda.synchronize()
                profile.disable()
            profile.dump_stats(str(out/'sample.prof'))
            with (out/'profile.txt').open('w') as f:pstats.Stats(profile,stream=f).sort_stats('cumtime').print_stats(45)
            (out/'timing.json').write_text(json.dumps(report,indent=2)+'\n')
            assert report['target_met'], times
        report['status']='PASS'
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print('CARRYBOX_WARP_PASS',flush=True)
    except BaseException:
        traceback.print_exc();raise
    finally:env.close()


try:main()
except BaseException:
    traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
