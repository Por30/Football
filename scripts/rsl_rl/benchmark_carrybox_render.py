"""Stage-isolated RTX depth equivalence and full-iteration performance probe."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument('--num-envs', type=int, required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--baseline', action='store_true')
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import json
import os
from pathlib import Path
import time
import cProfile
import pstats
import torch
import carb
import gymnasium as gym
from pxr import UsdGeom
import perceptual_ball.tasks
from isaaclab.sim import RenderCfg
from isaaclab.utils.math import quat_apply, quat_mul, matrix_from_quat
from isaaclab.utils.math import convert_camera_frame_orientation_convention as convert
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg, CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox as base
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner

KEYS = ['/app/useFabricSceneDelegate', '/rtx/hydra/readTransformsFromFabricInRenderDelegate',
        '/rtx/directLighting/enabled', '/rtx/directLighting/sampledLighting/enabled',
        '/rtx/shadows/enabled', '/rtx-transient/dldenoiser/enabled', '/rtx/post/aa/op',
        '/rtx/raytracing/cached/enabled', '/app/renderer/waitIdle', '/app/hydraEngine/waitIdle',
        '/app/updateOrder/checkForHydraRenderComplete', '/omni/replicator/asyncRendering',
        '/plugins/carb.tasking.plugin/threadCount', '/app/runLoops/main/rateLimitEnabled']


def main():
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    cfg, agent = CarryBoxWalled4EnvCfg(), CarryBoxWalled4PPORunnerCfg()
    if args.baseline:
        cfg.sim.render = RenderCfg()
    cfg.scene.num_envs, cfg.sim.device, cfg.seed = args.num_envs, args.device, 42
    env = gym.make('Template-Perceptual-Ball-CarryBox-Walled4-v0', cfg=cfg)
    b = env.unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    camera = b.scene['depth_camera']
    settings = carb.settings.get_settings()
    report = dict(num_envs=args.num_envs, settings={k: settings.get(k) for k in KEYS},
                  torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                  affinity=sorted(os.sched_getaffinity(0)), thread_env={k: os.getenv(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','PXR_WORK_THREAD_LIMIT']})
    (out / 'runtime.json').write_text(json.dumps(report, indent=2) + '\n')
    print('RUNTIME', json.dumps(report), flush=True)
    assert settings.get('/app/useFabricSceneDelegate') is False
    assert settings.get('/rtx/hydra/readTransformsFromFabricInRenderDelegate') is False
    assert settings.get('/app/renderer/waitIdle') is True
    assert settings.get('/app/hydraEngine/waitIdle') is True
    frames = {}

    def render():
        b.scene.write_data_to_sim()
        b.sim.forward()
        b.sim.render()
        b.scene.update(.02)
        return base.depth_image(b).clone()

    def poses():
        data = camera.data
        matrices = [UsdGeom.Xformable(camera.stage.GetPrimAtPath(p)).GetLocalTransformation() for p in camera._view.prim_paths]
        local_p = torch.tensor([list(m.ExtractTranslation()) for m in matrices], device=args.device)
        local_q = torch.tensor([[m.ExtractRotationQuat().GetReal(), *m.ExtractRotationQuat().GetImaginary()] for m in matrices], device=args.device)
        torso = task.state(b).torso
        rp, rq = b.scene['robot'].data.body_pos_w[:, torso], b.scene['robot'].data.body_quat_w[:, torso]
        torch.testing.assert_close(data.pos_w, rp+quat_apply(rq,local_p), atol=2e-4, rtol=0)
        expected_q = convert(quat_mul(rq,local_q), origin='opengl', target='world')
        torch.testing.assert_close(matrix_from_quat(data.quat_w_world),matrix_from_quat(expected_q),atol=2e-5,rtol=0)

    def put(name, xyz):
        q = torch.tensor([1.,0.,0.,0.], device=args.device).expand(args.num_envs,4)
        pose = torch.cat((b.scene.env_origins+torch.tensor(xyz,device=args.device),q),-1)
        if name == 'box':
            b.scene[name].write_root_state_to_sim(torch.cat((pose,torch.zeros(args.num_envs,6,device=args.device)),-1))
        else:
            task.write_obstacle_pose(b,name,pose)

    try:
        with torch.inference_mode():
            wrapped.reset()
            if args.num_envs == 4:
                render()
                poses()
                action = torch.zeros(4,29,device=args.device)
                for i in range(16):
                    obs, rew, done, info = wrapped.step(action)
                    assert all(torch.isfinite(v).all() for v in obs.values())
                    poses()
                    if i == 7:
                        b._reset_idx(torch.tensor([3,1],device=args.device))
                        render()
                        poses()
                # Canonical depth rays, identical geometry in independent stages.
                # Return the moving/fallen RSI robot to the same default pose;
                # otherwise its body can itself obstruct the canonical ray.
                cfg.reference_init = False
                cfg.search_prob = 0.
                wrapped.reset()
                for name in ['platform','wall','cylinder0','cylinder1','cylinder2']:
                    put(name,[10.,0.,-5.])
                q = torch.tensor([1.,0.,0.,0.],device=args.device).expand(4,4)
                camera.set_world_poses(b.scene.env_origins+torch.tensor([0.,0.,1.],device=args.device),q,convention='world')
                put('box',[2.2,0.,1.])
                for _ in range(3):render()
                frames['visible'] = render().cpu()
                for name,z in [('wall',1.5),('cylinder0',.9)]:
                    put(name,[1.5,0.,z])
                    for _ in range(3):render()
                    blocked=render()
                    center=blocked[:,13,24]*3
                    assert ((center>1.2)&(center<1.6)).all(),(name,center)
                    assert ((frames['visible'][:,13,24].to(args.device)-blocked[:,13,24])>.1).all()
                    put('box',[2.7,0.,1.])
                    moved=render()
                    torch.testing.assert_close(blocked[:,13,24],moved[:,13,24],atol=1e-4,rtol=0)
                    frames[name]=blocked.cpu()
                    put(name,[10.,0.,-5.]);put('box',[2.2,0.,1.]);render()
                torch.save(frames,out/'depth_frames.pt')
                if not args.baseline:
                    gold=torch.load(out.parent/'baseline4/depth_frames.pt',weights_only=True)
                    report['depth_max_error']={k:float((frames[k]-gold[k]).abs().max()) for k in frames}
                    for k in frames:torch.testing.assert_close(frames[k],gold[k],atol=1e-3/3,rtol=0)
                report['pose_reset_occlusion']=True
        if args.num_envs == 4096:
            # Separate non-profiler timing; preserve rollout length/epochs/batches.
            runner=CarryBoxOnPolicyRunner(wrapped,agent.to_dict(),log_dir=str(out/'train'),device=args.device)
            old=json.loads(Path('docs/carrybox/render6s_20261014/before_launch.json').read_text())
            runner.load(old['checkpoint'])
            runner.learn(4,init_at_random_ep_len=True)
            runner.save(str(out/'verification_model.pt'))
            runner.load(str(out/'verification_model.pt'))
            runner.learn(4)
            assert all(torch.isfinite(v).all() for v in runner.alg.policy.state_dict().values())
            report['updates']=8;report['resume']=True
            profile=cProfile.Profile()
            with torch.inference_mode():
                action=torch.zeros(4096,29,device=args.device)
                profile.enable()
                for _ in range(4):wrapped.step(action);torch.cuda.synchronize()
                profile.disable()
            profile.dump_stats(str(out/'sample.prof'))
            with (out/'profile.txt').open('w') as f:pstats.Stats(profile,stream=f).sort_stats('cumtime').print_stats(40)
        report['status']='PASS'
        (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
        print('CARRYBOX_RENDER_PROBE_PASS',flush=True)
    except BaseException:
        import traceback
        traceback.print_exc()
        raise
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
