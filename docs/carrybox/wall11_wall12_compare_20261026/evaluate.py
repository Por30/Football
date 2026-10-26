"""First-episode snapshot comparison. No training, overrides or selected replays."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument('--variant', type=int, choices=(11,12), required=True)
parser.add_argument('--eval_seed', type=int, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

from pathlib import Path
import json
import hashlib
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab.utils.math import matrix_from_quat
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import CarryBoxWall10OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.carrybox_wall12 import CarryBoxWall12OnPolicyRunner
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox import hand_contacts

OUT = Path(__file__).resolve().parent
N, STEPS = 64, 1000
PREFIX = f'wall{args.variant}_seed{args.eval_seed}'


def main():
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    record = json.loads((OUT/'training.json').read_text())['runs'][str(args.variant)]
    checkpoint = Path(record['checkpoint'])
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == record['checkpoint_sha256']
    task = f'Template-Perceptual-Ball-CarryBox-Walled{args.variant}-v0'
    cfg = load_cfg_from_registry(task, 'env_cfg_entry_point')
    agent = load_cfg_from_registry(task, 'rsl_rl_cfg_entry_point')
    cfg.scene.num_envs = N
    cfg.seed = args.eval_seed
    cfg.sim.device = args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = gym.make(task, cfg=cfg)
    try:
        b = env.unwrapped
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = wrapped.reset()
        cls = CarryBoxWall10OnPolicyRunner if args.variant == 11 else CarryBoxWall12OnPolicyRunner
        runner = cls(wrapped, agent.to_dict(), log_dir=None, device=args.device)
        runner.load(str(checkpoint), load_optimizer=False)
        policy = runner.alg.policy
        policy.eval()
        # load() restores the training RNG. Override it with the evaluation seed
        # before the paired initial reset; preserve all task randomization.
        b.seed(args.eval_seed)
        obs, _ = wrapped.reset()
        s = b._walled
        robot, box = b.scene['robot'], b.scene['box']
        camera = b.scene['depth_camera']
        initial = dict(robot_root=robot.data.root_state_w.clone(), joints=robot.data.joint_pos.clone(),
            joint_vel=robot.data.joint_vel.clone(), box=box.data.root_state_w.clone(),
            sizes=camera.box_sizes.clone(), source=torch.where(s.default_reset,0,s.skills+1).clone(),
            ground=s.from_ground.clone(), proprio=obs['proprio'].clone(), depth=obs['perception'].clone(),
            masses=robot.root_physx_view.get_masses().clone(), materials=robot.root_physx_view.get_material_properties().clone(),
            inertias=robot.root_physx_view.get_inertias().clone(), coms=robot.root_physx_view.get_coms().clone(),
            box_masses=box.root_physx_view.get_masses().clone(), cpu_rng=torch.get_rng_state(),
            cuda_rng=torch.cuda.get_rng_state(args.device))
        for name in ('wall','platform','cylinder0','cylinder1','cylinder2'):
            initial[name] = b.scene[name].data.root_state_w.clone()
        torch.save({k:v.cpu() for k,v in initial.items()}, OUT/f'{PREFIX}_initial.pt')
        active = torch.ones(N, device=args.device, dtype=torch.bool)
        rows = dict(ground=s.from_ground.clone(), source=initial['source'].clone(),
            success=torch.zeros_like(active), steps=torch.zeros(N,device=args.device,dtype=torch.long),
            held_steps=torch.zeros(N,device=args.device,dtype=torch.long),
            max_held_steps=torch.zeros(N,device=args.device,dtype=torch.long),
            max_strict_steps=torch.zeros(N,device=args.device,dtype=torch.long),
            held_frames=torch.zeros(N,device=args.device,dtype=torch.long),
            max_clearance=torch.zeros(N,device=args.device),
            terminated=torch.zeros_like(active),timeout=torch.zeros_like(active),tipped=torch.zeros_like(active))

        def measure(ids):
            if not len(ids):
                return
            r = matrix_from_quat(box.data.root_quat_w)
            clearance = box.data.root_pos_w[:,2] - b.scene.env_origins[:,2] - (r[:,2].abs()*camera.box_sizes/2).sum(-1)
            held = hand_contacts(b).all(-1) & (clearance>.10) & (r[:,2,2]>.8)
            rows['steps'][ids] += 1
            rows['held_steps'][ids] = torch.where(held[ids],rows['held_steps'][ids]+1,0)
            rows['max_held_steps'][ids] = torch.maximum(rows['max_held_steps'][ids],rows['held_steps'][ids])
            rows['held_frames'][ids] += held[ids]
            rows['max_strict_steps'][ids] = torch.maximum(rows['max_strict_steps'][ids],s.hold_steps[ids])
            rows['success'][ids] |= s.achieved[ids]
            rows['max_clearance'][ids] = torch.maximum(rows['max_clearance'][ids],clearance[ids])

        original_reset = b._reset_idx
        def capture_before_reset(ids):
            selected = ids[active[ids]]
            if getattr(b, '_carrybox_in_step',False) and len(selected):
                measure(selected)
                rows['terminated'][selected] = b.termination_manager.terminated[selected]
                rows['timeout'][selected] = b.termination_manager.time_outs[selected]
                rows['tipped'][selected] = b.termination_manager.get_term('tipped')[selected]
                active[selected] = False
            original_reset(ids)
        b._reset_idx = capture_before_reset
        with torch.inference_mode():
            for step in range(STEPS):
                action = policy.act_inference(obs)
                assert torch.isfinite(action).all()
                obs, reward, done, extra = wrapped.step(action)
                assert torch.isfinite(reward).all()
                measure(active.nonzero().flatten())
                if step % 200 == 0:
                    print(f'{PREFIX} step={step} first_episodes_active={int(active.sum())}',flush=True)
                if not active.any():
                    break
        assert not active.any(), 'Not all first episodes completed in the declared horizon'
        assert (rows['steps']>0).all() and (rows['steps']<=1000).all()
        assert torch.equal(rows['success'],rows['max_strict_steps']>=100)
        result = dict(status='PASS',variant=args.variant,seed=args.eval_seed,num_envs=N,
            checkpoint=record['checkpoint'],checkpoint_sha256=record['checkpoint_sha256'],
            action_mode='deterministic_mean',dt=b.step_dt,
            metrics='first episode only; bilateral contact >1N, clearance >0.1m, box upright >0.8; held >=25 steps; strict success >=100 steps with original task checks',
            rows={k:v.cpu().tolist() for k,v in rows.items()},optimizer_updated=False)
        (OUT/f'{PREFIX}.json').write_text(json.dumps(result,indent=2)+'\n')
        print('PAIR_EVAL_PASS',flush=True)
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
