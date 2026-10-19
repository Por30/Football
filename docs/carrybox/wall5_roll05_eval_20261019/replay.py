"""Bounded first-episode loco inference of the pinned current wall5 checkpoint."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument('--mode', required=True, choices=('mean', 'sample'))
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

from pathlib import Path
import hashlib
import json
import traceback
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat, wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg, CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5 import Wall5CarryBoxEnv
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as common
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic

DOC = Path(__file__).resolve().parent
N, HORIZON = 32, 1000

def main():
    torch.set_num_threads(2)
    selection = json.loads((DOC/'selection.json').read_text())
    checkpoint_path = Path(selection['checkpoint'])
    assert hashlib.sha256(checkpoint_path.read_bytes()).hexdigest() == selection['checkpoint_sha256']
    cfg, agent = CarryBoxWalled5EnvCfg(), CarryBoxWalled5PPORunnerCfg()
    cfg.scene.num_envs, cfg.seed, cfg.sim.device = N, 42, args.device
    capacities = ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity', 'gpu_total_aggregate_pairs_capacity')
    for name in capacities:
        setattr(cfg.sim.physx, name, 262144)
    env = Wall5CarryBoxEnv(cfg=cfg)
    try:
        checkpoint = torch.load(checkpoint_path, map_location=args.device, weights_only=False)
        original_contract = env.checkpoint_contract()
        assert original_contract == checkpoint['environment_contract']
        w = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = w.reset()
        pc = agent.policy.to_dict(); pc.pop('class_name')
        policy = CarryBoxWall5ActorCritic(obs, agent.obs_groups, 29, **pc).to(env.device)
        policy.load_state_dict(checkpoint['model_state_dict'], strict=True)
        policy.eval()
        saved = {k:v.clone() for k,v in policy.state_dict().items()}
        env.set_training_iteration(0); env.set_training_iteration(selection['checkpoint_iteration'])
        s = common.state(env)
        effective = s.curriculum.iteration-s.curriculum.anchor
        assert effective == 5200 and abs(s.curriculum.degrees-5.2) < 1.e-6
        scale = max(0., min(1., (effective-cfg.push_warmup_iterations)/cfg.push_ramp_iterations))
        assert scale == 1.
        cfg.reset_skill_probabilities = (1., 0., 0.)  # only this diagnostic instance, AFTER strict contract comparison
        robot = env.scene['robot']; data = robot.data
        term = env.action_manager.get_term('joint_pos')
        contact = env.scene['body_contacts']
        feet = contact.find_bodies(['left_ankle_roll_link','right_ankle_roll_link'], preserve_order=True)[0]
        alive = torch.ones(N, dtype=torch.bool, device=env.device)
        ends = [None]*N; trajectories = [[] for _ in range(N)]
        pushes = torch.zeros(N, dtype=torch.long, device=env.device)
        active, step = False, 0
        initial_root = initial_box = None

        def snapshot():
            roll, pitch, _ = euler_xyz_from_quat(data.root_quat_w)
            return dict(root=data.root_link_pos_w-env.scene.env_origins,
                box=env.scene['box'].data.root_pos_w-env.scene.env_origins,
                roll=wrap_to_pi(roll), pitch=wrap_to_pi(pitch), head_z=common.head_height(env),
                feet=data.body_link_pos_w[:,s.feet]-env.scene.env_origins[:,None],
                foot_force=contact.data.net_forces_w[:,feet].norm(dim=-1))

        def episode(i, frame, censored):
            origin = initial_root[i]
            delta = frame['root'][i,:2]-origin[:2]
            target = initial_box[i,:2]-origin[:2]
            labels = {name:bool(env.termination_manager.get_term(name)[i])
                      for name in ('tipped','fell','invalid','time_out')} if not censored else {name:False for name in ('tipped','fell','invalid','time_out')}
            return dict(env=i, steps=step+1, seconds=(step+1)*.02, censored=censored,
                **labels, failure=bool(env.termination_manager.terminated[i]) if not censored else False,
                roll=float(frame['roll'][i]), pitch=float(frame['pitch'][i]),
                root_z=float(frame['root'][i,2]), head_z=float(frame['head_z'][i]),
                root_xyz=frame['root'][i].tolist(), box_xyz=frame['box'][i].tolist(),
                displacement_xy=float(delta.norm()), towards_initial_box=float((delta*target/target.norm().clamp_min(1.e-6)).sum()),
                box_distance_start=float(target.norm()),
                box_distance_end=float((frame['box'][i,:2]-frame['root'][i,:2]).norm()),
                push_count=int(pushes[i]), success=bool(s.achieved[i]))

        original_compute = env.reward_manager.compute
        def reward_capture(dt):
            reward = original_compute(dt)
            if active:
                frame = snapshot()
                cpu = {k:v.detach().cpu().tolist() for k,v in frame.items()}
                saturation = term.target_saturation.float().mean(-1).tolist()
                for i in alive.nonzero().flatten().tolist():
                    trajectories[i].append(dict(step=step+1, **{k:v[i] for k,v in cpu.items()}, target_clipped_fraction=saturation[i]))
            return reward
        env.reward_manager.compute = reward_capture
        original_reset = env._reset_idx
        def reset_capture(ids):
            if active and getattr(env, '_carrybox_in_step', False):
                frame = snapshot()
                for i in ids.tolist():
                    if alive[i]:
                        assert int(s.actual_episode_steps[i]) == step+1
                        assert int(s.skills[i]) == 0
                        ends[i] = episode(i, frame, False)
                        alive[i] = False
            original_reset(ids)
        env._reset_idx = reset_capture
        event = env.event_manager.get_term_cfg('push_robot')
        original_push = event.func
        def push_capture(e, ids, **kwargs):
            if active:
                first_ids = ids[alive[ids]]
                pushes[first_ids] += 1
            original_push(e, ids, **kwargs)
        event.func = push_capture; env.event_manager.set_term_cfg('push_robot', event)
        action_generator = torch.Generator(device=env.device).manual_seed(771)
        with torch.inference_mode():
            torch.manual_seed(123); obs, _ = w.reset()
            assert (s.skills == 0).all() and (s.actual_episode_steps == 0).all()
            initial = snapshot()
            initial_root, initial_box = initial['root'].clone(), initial['box'].clone()
            physics = dict(root=data.root_link_state_w.clone(), q=data.joint_pos.clone(), dq=data.joint_vel.clone(),
                velocity=data.root_vel_w.clone(), offset=term._offset.clone(), box=env.scene['box'].data.root_state_w.clone())
            for name in ('wall','cylinder0','cylinder1','cylinder2'):
                physics[name] = env.scene[name].data.root_state_w.clone()
            fixture = dict(physics=physics, obs={k:obs[k].clone() for k in ('proprio','perception')})
            if args.mode == 'mean':
                torch.save(fixture, DOC/'initial_fixture.pt')
            else:
                expected = torch.load(DOC/'initial_fixture.pt', map_location=env.device, weights_only=False)
                for group in ('physics','obs'):
                    for name,value in fixture[group].items():
                        torch.testing.assert_close(value, expected[group][name], atol=1.e-5, rtol=1.e-5, msg=lambda m:group+'/'+name+': '+m)
            active = True
            for step in range(HORIZON):
                assert all(torch.isfinite(v).all() for v in obs.values())
                action = policy.act_inference(obs)
                if args.mode == 'sample':
                    action = action+policy.log_std.exp()*torch.randn(N,29,device=env.device,generator=action_generator)
                assert torch.isfinite(action).all()
                obs, reward, done, _ = w.step(action)
                assert torch.isfinite(reward).all()
                if (step+1) % 250 == 0:
                    print('REPLAY_PROGRESS', args.mode, step+1, 'first_alive', int(alive.sum()), flush=True)
                # Every first episode has ended: further automatic resets add no evidence.
                if not alive.any():
                    break
            active = False
            final = snapshot()
            for i in alive.nonzero().flatten().tolist():
                assert step+1 == HORIZON and int(s.actual_episode_steps[i]) == HORIZON
                ends[i] = episode(i, final, True)
        assert all(e is not None and 0 < e['steps'] <= HORIZON for e in ends)
        assert all(len(trajectories[i]) == ends[i]['steps'] for i in range(N))
        assert all(torch.equal(v,saved[k]) for k,v in policy.state_dict().items())
        result = dict(status='PASS', mode=args.mode, checkpoint=str(checkpoint_path),
            checkpoint_sha256=selection['checkpoint_sha256'], original_contract=original_contract,
            strict_model_state=True, environment_contract_matched=True, num_envs=N, horizon_steps=HORIZON,
            executed_steps=step+1, control_dt=.02, construction_seed=42, reset_seed=123, action_seed=771,
            effective_iteration=effective, yaw_deg=s.curriculum.degrees, push_scale=scale,
            diagnostic_overrides=dict(reset_skill_probabilities=[1.,0.,0.], num_envs=N, **{k:262144 for k in capacities}),
            initial={k:v.tolist() for k,v in initial.items()}, first_episodes=ends, trajectories=trajectories,
            policy_parameters_unchanged=True, training_updates=0, initial_states_checked=(args.mode=='sample'),
            limits=['Only first episodes; stop early once all first episodes end',
                    'Sample action uses independent RNG; scene draws can diverge after different resets',
                    'No policy discriminator update; survival alone does not establish walking or task success'])
        (DOC/f'{args.mode}.json').write_text(json.dumps(result)+'\n')
        print('LOCO_EVAL_PASS', args.mode, json.dumps(ends), flush=True)
    finally:
        env.close()

try:
    main()
except BaseException:
    (DOC/f'exception_{args.mode}.txt').write_text(traceback.format_exc())
    traceback.print_exc()
    raise
finally:
    app.close(wait_for_replicator=False)
