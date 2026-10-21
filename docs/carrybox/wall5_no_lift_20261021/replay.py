"""Bounded, inference-only pickup diagnosis with original checkpoint semantics."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

from pathlib import Path
import hashlib, json
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg, CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task, carrybox_walled as common, carrybox as base

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]
N, STEPS = 20, 1000

def main():
    torch.set_num_threads(2)
    selection = json.loads((DOC/'selection.json').read_text())
    ckpt = Path(selection['checkpoint'])
    assert hashlib.sha256(ckpt.read_bytes()).hexdigest() == selection['checkpoint_sha256']
    checkpoint = torch.load(ckpt, map_location=args.device, weights_only=False)
    cfg, agent = CarryBoxWalled5EnvCfg(), CarryBoxWalled5PPORunnerCfg()
    cfg.reset_skill_probabilities = tuple(checkpoint['environment_contract']['reset_skill_probabilities'])
    cfg.scene.num_envs, cfg.seed, cfg.sim.device = N, 42, args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = task.Wall5CarryBoxEnv(cfg=cfg)
    try:
        assert env.checkpoint_contract() == checkpoint['environment_contract']
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        obs, _ = wrapped.reset()
        p = agent.policy.to_dict()
        assert p.pop('class_name') == 'CarryBoxWall5ActorCritic'
        policy = CarryBoxWall5ActorCritic(obs, agent.obs_groups, 29, **p).to(args.device)
        policy.load_state_dict(checkpoint['model_state_dict'], strict=True)
        policy.eval()
        saved = {k:v.clone() for k,v in policy.state_dict().items()}
        env.set_training_iteration(0)
        env.set_training_iteration(checkpoint['iter'])
        s = common.state(env)
        robot, box = env.scene['robot'].data, env.scene['box'].data
        g = cfg.reward_geometry
        active, step, episodes = False, 0, []
        original_reset = env._reset_idx
        def reset_capture(ids):
            if active and getattr(env, '_carrybox_in_step', False):
                for i in ids.tolist():
                    episodes.append(dict(env_id=i, skill=int(s.skills[i]), steps=int(s.actual_episode_steps[i]),
                        end_step=step+1, timeout=bool(env.termination_manager.time_outs[i]),
                        tipped=bool(task.tipped(env)[i]), fell=bool(common.fallen(env)[i]), success=bool(s.achieved[i])))
            original_reset(ids)
        env._reset_idx = reset_capture
        names = ['near','distance3d_m','distance_xy_m','root_z_m','hand_center_error_m',
                 'crouched','any_contact','both_contact','box_bottom_m','clearance12cm','box_z_m',
                 'above_success_height','left_force_N','right_force_N','walk','carry_hand',
                 'carry_contact','carry_height','standup','stable_grasp','raw_task_per_step']
        result = dict(status='RUNNING', checkpoint=str(ckpt), checkpoint_sha256=selection['checkpoint_sha256'],
                      num_envs=N, steps_per_case=STEPS, contract=env.checkpoint_contract(),
                      yaw_degrees=s.curriculum.degrees, policy_updates=0, cases={})
        with torch.inference_mode():
            for mode in ('mean','sample'):
                active=False
                torch.manual_seed(42)
                obs, _ = wrapped.reset()
                skills = s.skills.clone()
                assert torch.bincount(skills, minlength=3).tolist() == [16,0,4]
                episodes=[]
                active=True
                samples, valid = [], []
                for step in range(STEPS):
                    action = policy.act_inference(obs) if mode == 'mean' else policy.act(obs)
                    assert torch.isfinite(action).all()
                    obs, reward, done, _ = wrapped.step(action)
                    # RslRlVecEnvWrapper returns int64 dones for RSL-RL.
                    # Convert before inversion/indexing so reset rows are excluded.
                    done = done.bool()
                    assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
                    delta = box.root_pos_w-robot.root_link_pos_w
                    distance = delta.norm(dim=-1)
                    near = distance <= g['near_distance']
                    height = robot.root_pos_w[:,2]-env.scene.env_origins[:,2]
                    box_z = box.root_pos_w[:,2]-env.scene.env_origins[:,2]
                    hand_sq = (robot.body_pos_w[:,s.hands].mean(1)-box.root_pos_w).square().sum(-1)
                    force = torch.stack([env.scene[f'{side}_box_contact'].data.force_matrix_w.flatten(1,-2).norm(dim=-1).amax(-1) for side in ('left','right')],-1)
                    contact = 1-torch.exp(-.5*force)
                    bottom = base.lift_geometry(env)[0]
                    crouched = near & (height<g['crouch_pelvis']) & (box_z<g['crouch_box'])
                    terms = s.reward_terms
                    carry_hand = .7*torch.exp(-3*hand_sq)*near
                    carry_contact = 1.5*contact.mean(-1)*(hand_sq<=.3)*near
                    carry_height = 1.5*torch.exp(-g['carryup_height_exp']*(g['carryup_box']-box_z).clamp_min(0))*near
                    values = torch.stack([near.float(),distance,delta[:,:2].norm(dim=-1),height,hand_sq.sqrt(),
                        crouched.float(),(force>1).any(-1).float(),(force>1).all(-1).float(),bottom,(bottom>=.12).float(),
                        box_z,(box_z>g['success_box']).float(),force[:,0],force[:,1],task.walk_task(env),
                        carry_hand,carry_contact,carry_height,terms['standup_task'],terms['stable_grasp'],reward],-1)
                    assert torch.isfinite(values).all()
                    if (~done).any():
                        torch.testing.assert_close((carry_hand+carry_contact+carry_height)[~done],terms['carryup_task'][~done],atol=2e-5,rtol=2e-5)
                    samples.append(values.cpu())
                    valid.append((~done).cpu())
                    if (step+1)%250==0:
                        print('REPLAY_PROGRESS',mode,step+1,flush=True)
                active=False
                data=torch.stack(samples);mask=torch.stack(valid)
                torch.save(dict(metrics=names,values=data,valid_survivor=mask,skills=skills.cpu()),DOC/f'{mode}_samples.pt')
                by_skill={}
                for skill,name in ((0,'loco'),(2,'hold')):
                    selected=mask & (skills.cpu()[None]==skill)
                    values=data[selected]
                    near_values=values[values[:,0]>.5]
                    ends=[e for e in episodes if e['skill']==skill]
                    by_skill[name]=dict(samples=len(values),means={n:float(values[:,j].mean()) for j,n in enumerate(names)},
                        near_samples=len(near_values),near_means={n:float(near_values[:,j].mean()) for j,n in enumerate(names)} if len(near_values) else {},
                        hand_distance_quantiles_m=torch.quantile(values[:,4],torch.tensor([.05,.5,.95])).tolist(),
                        max_box_bottom_m=float(values[:,8].max()),completed=len(ends),successes=sum(e['success'] for e in ends),
                        tipped=sum(e['tipped'] for e in ends),fell=sum(e['fell'] for e in ends),timeouts=sum(e['timeout'] for e in ends))
                censored=[dict(env_id=i,skill=int(s.skills[i]),steps=int(s.actual_episode_steps[i]),success=bool(s.achieved[i])) for i in range(N)]
                assert sum(e['steps'] for e in episodes)+sum(e['steps'] for e in censored)==N*STEPS
                result['cases'][mode]=dict(by_skill=by_skill,episodes=episodes,censored=censored)
                print('CASE_SUMMARY',mode,json.dumps(by_skill),flush=True)
        assert all(torch.equal(v,saved[k]) for k,v in policy.state_dict().items())
        assert hashlib.sha256(ckpt.read_bytes()).hexdigest()==selection['checkpoint_sha256']
        for name,h in selection['source_sha256'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
        result.update(status='PASS',weights_unchanged=True,source_unchanged=True,
                      caveats=['One seed and 20 environments; not a population success estimate.',
                               'State statistics exclude reset transitions; completed and censored episodes are separate.',
                               'Mean and sampled actions are separate cases; RNG trajectories are not paired.',
                               'No reward ablation or causal training experiment; hold starts are not ground pickups.'])
        (DOC/'replay.json').write_text(json.dumps(result,indent=2)+'\n')
        print('NO_LIFT_REPLAY_PASS',flush=True)
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
