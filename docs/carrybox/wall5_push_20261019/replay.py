"""Same rev13 policy, three push semantics, no training or production mutation."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser);args=parser.parse_args();app=AppLauncher(args).app
import importlib.util,sys,json,statistics as st,hashlib
from pathlib import Path
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxActorCritic
from materials import inspect_materials
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2];N=16;STEPS=1200
CHECKPOINT=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_13-10-42_wall5_v13_perf_fresh_20261018_131037/model_10600.pt'
BEFORE=ROOT/'docs/carrybox/wall5_asymmetric_20261019/before/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
    torch.set_num_threads(2)
    package='perceptual_ball.tasks.manager_based.perceptual_ball'
    legacy_cfg=load(package+'.wall5_rev13_diagnostic_cfg',BEFORE/'carrybox_wall5_env_cfg.py')
    legacy_mdp=load(package+'.mdp.wall5_rev13_diagnostic_mdp',BEFORE/'mdp/carrybox_wall5.py')
    cfg=legacy_cfg.CarryBoxWalled5EnvCfg();cfg.scene.num_envs=N;cfg.seed=42;cfg.sim.device=args.device
    assert cfg.sim.physics_material.static_friction==.5 and cfg.scene.ground.spawn.physics_material.static_friction==.5
    for key in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,key,262144)
    b=legacy_mdp.Wall5CarryBoxEnv(cfg=cfg)
    try:
        w=RslRlVecEnvWrapper(b,clip_actions=9.);checkpoint=torch.load(CHECKPOINT,map_location=args.device,weights_only=False)
        assert checkpoint['environment_contract']==b.checkpoint_contract()
        assert checkpoint['environment_contract']['migration_revision']==13 and checkpoint['iter']==10600
        obs,_=w.reset();p=CarryBoxActorCritic(obs,{'policy':['proprio','perception'],'critic':['proprio','perception']},29,
             actor_hidden_dims=(512,256,256),critic_hidden_dims=(512,256,256),init_noise_std=1.).to(args.device)
        p.load_state_dict(checkpoint['model_state_dict'],strict=True);p.eval();before={k:v.clone() for k,v in p.state_dict().items()}
        b.set_training_iteration(0);b.set_training_iteration(10600);state=task.state(b)
        assert abs(state.curriculum.degrees-11.2)<1e-6
        material=inspect_materials(b);(DOC/'materials_before.json').write_text(json.dumps(material,indent=2)+'\n')
        robot=b.scene['robot'];active=None;case_name=None;step_index=0
        ages=torch.zeros(N,dtype=torch.long,device=b.device);pushes=torch.zeros_like(ages);first_push=torch.full_like(ages,-1)
        action_gen=torch.Generator(device=b.device);push_gen=torch.Generator(device=b.device).manual_seed(772)
        draws=torch.rand(STEPS,N,6,device=b.device,generator=push_gen)
        event=b.event_manager.get_term_cfg('push_robot')
        ranges=torch.tensor([event.params['velocity_range'][k] for k in ('x','y','z','roll','pitch','yaw')],device=b.device)
        samples=ranges[:,0]+draws*(ranges[:,1]-ranges[:,0])
        def push_capture(env,ids,**kw):
            current=robot.data.root_vel_w[ids].clone();sample=samples[step_index,ids]
            desired=sample if case_name=='set' else (current+sample if case_name=='increment' else current)
            if case_name!='none':robot.write_root_velocity_to_sim(desired,env_ids=ids)
            if active is not None:
                for j,i in enumerate(ids.tolist()):active['push_events'].append(dict(env=i,skill=int(state.skills[i]),age=int(ages[i]),
                    before=current[j].tolist(),sample=sample[j].tolist(),after=robot.data.root_vel_w[i].tolist(),applied=case_name!='none'))
                if case_name!='none':
                    first_push[ids]=torch.where(first_push[ids]<0,ages[ids],first_push[ids]);pushes[ids]+=1
        event.func=push_capture;b.event_manager.set_term_cfg('push_robot',event)
        def snapshot(i):
            roll,pitch,_=euler_xyz_from_quat(robot.data.root_quat_w[i:i+1])
            return dict(skill=int(state.skills[i]),steps=int(ages[i]),actual_steps=int(state.actual_episode_steps[i]),
                roll=float(wrap_to_pi(roll)[0]),pitch=float(wrap_to_pi(pitch)[0]),
                tipped=bool(legacy_mdp.tipped(b)[i]),fell=bool(task.fallen(b)[i]),timeout=bool(b.termination_manager.time_outs[i]),
                success=bool(state.achieved[i]),push_count=int(pushes[i]),first_push_age=int(first_push[i]))
        original_reset=b._reset_idx
        def reset_capture(ids):
            if active is not None and getattr(b,'_carrybox_in_step',False):
                ended=[snapshot(i) for i in ids.tolist()];assert all(e['steps']==e['actual_steps'] and e['steps']>0 for e in ended)
                active['episodes'].extend(ended)
            original_reset(ids);ages[ids]=0;pushes[ids]=0;first_push[ids]=-1
        b._reset_idx=reset_capture
        result=dict(status='RUNNING',checkpoint=str(CHECKPOINT),checkpoint_sha256=hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest(),
                    migration_revision=13,strict_model_state=True,environment_contract_matched=True,num_envs=N,steps=STEPS,
                    seed=42,action_mode='sample',action_seed=771,push_seed=772,effective_iteration=10600,push_scale=1.,yaw_deg=11.2,
                    training_updates=0,cases={},caveats=['Initial states and per-step action/push draws match; trajectories/resets subsequently diverge',
                    'Completed episode means exclude censored episodes; report both, not unbiased lifetime','Small-scene replay does not establish training causality or task success'])
        initial=None
        with torch.inference_mode():
            for name in ('set','increment','none'):
                active=None;case_name=name;torch.manual_seed(42);action_gen.manual_seed(771);obs,_=w.reset()
                ages.zero_();pushes.zero_();first_push.fill_(-1)
                initial_state=torch.cat((robot.data.root_state_w,robot.data.joint_pos,b.scene['box'].data.root_state_w),-1).clone()
                if initial is None:initial=initial_state
                else:torch.testing.assert_close(initial_state,initial,atol=1e-5,rtol=1e-5)
                active=dict(episodes=[],push_events=[],initial_skills=state.skills.tolist());done_count=0
                for step_index in range(STEPS):
                    mean=p.act_inference(obs);action=mean+p.log_std.exp()*torch.randn(N,29,device=b.device,generator=action_gen)
                    assert torch.isfinite(action).all() and all(torch.isfinite(v).all() for v in obs.values());ages+=1
                    obs,reward,done,_=w.step(action);assert torch.isfinite(reward).all();done_count+=int(done.sum())
                    if (step_index+1)%400==0:print('REPLAY_PROGRESS',name,step_index+1,done_count,flush=True)
                censored=[snapshot(i) for i in range(N)]
                assert done_count==len(active['episodes'])
                assert sum(e['steps'] for e in active['episodes'])+sum(e['steps'] for e in censored)==N*STEPS
                summary={}
                for skill,label in enumerate(('loco','pickup','hold')):
                    es=[e for e in active['episodes'] if e['skill']==skill]
                    summary[label]=dict(completed=len(es),mean_completed_steps=st.mean(e['steps'] for e in es) if es else None,
                        median_completed_steps=st.median(e['steps'] for e in es) if es else None,
                        before_first_push=sum(e['push_count']==0 for e in es),under_50_steps=sum(e['steps']<50 for e in es),
                        tipped=sum(e['tipped'] for e in es),fell=sum(e['fell'] for e in es),timeouts=sum(e['timeout'] for e in es),
                        successes=sum(e['success'] for e in es),censored_ages=[e['steps'] for e in censored if e['skill']==skill])
                active.update(by_skill=summary,censored=censored,done_count=done_count,
                    mean_completed_steps=st.mean(e['steps'] for e in active['episodes']))
                result['cases'][name]=active;print('CASE_SUMMARY',name,json.dumps(summary),flush=True)
                (DOC/'replay_result.json').write_text(json.dumps(result,indent=2)+'\n');active=None
        assert all(torch.equal(v,before[k]) for k,v in p.state_dict().items())
        result.update(status='PASS',parameters_unchanged=True,initial_states_match=True)
        (DOC/'replay_result.json').write_text(json.dumps(result,indent=2)+'\n');print('PUSH_REPLAY_PASS',flush=True)
    finally:b.close()
try:main()
finally:app.close(wait_for_replicator=False)
