"""Four-env integration only: no formal run or convergence claim."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import copy,json,time
from pathlib import Path
from unittest.mock import patch
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import quat_apply
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg,CarryBoxWalled4PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as wall5,carrybox_walled as task
from perceptual_ball.carrybox_wall5 import Wall5MotionLibrary,GROUND_DATASET_PATH
from perceptual_ball.carrybox_amp import joint_mapping
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5OnPolicyRunner
from perceptual_ball.rsl_rl_extensions.export import DepthPolicyExport
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]

def main():
    torch.set_num_threads(2)
    cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    assert cfg.reset_skill_probabilities==(.8,.2,0.) and cfg.ground_pickup_reset_frame_range==(0,32)
    assert cfg.scene.depth_camera.output_mesh_hits and cfg.scene.platform is None
    assert agent.policy.init_noise_std==1. and agent.policy.actor_hidden_dims==[512,256,256]
    assert agent.algorithm.schedule=='adaptive' and agent.algorithm.pose_aux_coef==.1
    old=CarryBoxWalled4EnvCfg();old_agent=CarryBoxWalled4PPORunnerCfg()
    assert old.reset_skill_probabilities==(.6,.3,.1) and not old.scene.depth_camera.output_mesh_hits
    assert old_agent.algorithm.schedule=='fixed' and old_agent.policy.init_noise_std==.2
    cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx,name,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions)
        obs,_=w.reset();robot=b.scene['robot'];box=b.scene['box'];camera=b.scene['depth_camera']
        assert obs['proprio'].shape==(4,372) and obs['perception'].shape==(4,4,27,48)
        assert obs['amp'].shape==(4,600) and obs['box_pose_target'].shape==(4,10)
        torch.testing.assert_close(task.base.lift_geometry(b)[0],torch.full((4,),.005,device=b.device),atol=2e-5,rtol=0)
        assert (task.state(b).skills!=2).all()
        library=Wall5MotionLibrary(GROUND_DATASET_PATH,device=b.device)
        mapping=joint_mapping(robot.joint_names);parity=[]
        with torch.inference_mode():
            for i,name in enumerate(library.clip_names):
                d=torch.load(library.root/name,map_location=b.device,weights_only=True)
                q=library.clips[i][2][0].repeat(4,1)
                root=robot.data.root_state_w.clone();root[:,:3]=b.scene.env_origins+torch.tensor([0.,0.,1.],device=b.device)
                root[:,3:7]=q;root[:,7:10]=library.task_clips[i][1][0]
                root[:,10:]=quat_apply(q,library.clips[i][3][0].repeat(4,1))
                joints=robot.data.joint_pos.clone();joints[:,mapping]=d['joint_position'][0]
                robot.write_joint_state_to_sim(joints,torch.zeros_like(joints));robot.write_root_link_state_to_sim(root)
                pose=box.data.root_state_w.clone();pose[:,:3]=root[:,:3]+d['box_pos_local'][0];pose[:,7:]=0
                box.write_root_state_to_sim(pose)
                b.sim.forward();b.scene.update(b.physics_dt)
                frame=wall5.amp_frame(b)[0]
                reference=library.windows(torch.tensor([i],device=b.device),torch.zeros(1,device=b.device)).reshape(10,60)[0]
                error=(frame-reference).abs()
                # Native data hand/head origins differ <=3.86mm from current G1 skeleton; feet match.
                torch.testing.assert_close(frame[:30],reference[:30],atol=1e-4,rtol=1e-4)
                torch.testing.assert_close(frame[36:42],reference[36:42],atol=1e-4,rtol=1e-4)
                torch.testing.assert_close(frame[45:],reference[45:],atol=1e-4,rtol=1e-4)
                assert error[30:45].max()<.0041,(name,error.tolist())
                parity.append(dict(clip=name,max_end_error_m=float(error[30:45].max()),max_other_error=float(torch.cat((error[:30],error[45:])).max())))
            obs,_=w.reset()
            # Exercise the production RSI sampler/writer (not direct state injection).
            state=task.state(b);rsi_velocity=[];ids=torch.arange(4,device=b.device)
            for skill,group,name,frame_id in [(0,'loco_direction','locomotion/walk_forward_01.pt',80),(1,'pickUp','pick_up/pick_up_03.pt',31)]:
                clip=state.library.clip_names.index(name)
                clips=[i for i,g in enumerate(state.library.clip_groups) if g==group]
                state.skills[:]=skill
                # pickup pool is exactly 0..31, so index 31 selects native frame 31.
                choices=[torch.full((4,),clips.index(clip),device=b.device),torch.full((4,),frame_id,device=b.device)]
                with patch.object(task.torch,'randint',side_effect=choices):
                    task.initialize_reference(b,ids)
                measured=wall5.amp_frame(b)[:,45:48]
                joints,_,q,ang=library.clips[clip];ends,lin,box_delta=library.task_clips[clip]
                from perceptual_ball.carrybox_wall5 import pack_task_frame
                expected=pack_task_frame(joints[frame_id:frame_id+1],q[frame_id:frame_id+1],ends[frame_id:frame_id+1],lin[frame_id:frame_id+1],ang[frame_id:frame_id+1],box_delta[frame_id:frame_id+1])[:,45:48].expand(4,-1)
                torch.testing.assert_close(measured,expected,atol=2e-5,rtol=1e-4)
                rsi_velocity.append(dict(clip=name,frame=frame_id,max_error_m_s=float((measured-expected).abs().max())))
            w.reset()
            # New vertical RSI velocities must preserve the existing safe pickup reset range.
            pickup_slot=state.library.clip_names.index('pick_up/pick_up_03.pt')
            saved_pool=state.ground_reference_frames[pickup_slot].clone()
            saved_probs=cfg.reset_skill_probabilities;cfg.reset_skill_probabilities=(0.,1.,0.)
            ground_velocity_peaks=[]
            for native_frame in range(32):
                state.ground_reference_frames[pickup_slot]=torch.tensor([native_frame],device=b.device)
                w.reset()
                torch.testing.assert_close(task.base.lift_geometry(b)[0],torch.full((4,),.005,device=b.device),atol=2e-5,rtol=0)
                robot.set_joint_position_target(robot.data.joint_pos.clone());b.scene.write_data_to_sim()
                peak=0.
                for _ in range(4):
                    b.sim.step(render=False);b.scene.update(b.physics_dt)
                    peak=max(peak,float(box.data.root_lin_vel_w.norm(dim=-1).max()))
                assert peak<.3,('new RSI caused box contact impulse',native_frame,peak)
                ground_velocity_peaks.append(peak)
            state.ground_reference_frames[pickup_slot]=saved_pool;cfg.reset_skill_probabilities=saved_probs
            w.reset()
            # Contact sensor probe: deliberately put a box against each hand in separate envs.
            force_peaks={}
            for side in ('left','right'):
                hand=robot.find_bodies(f'{side}_rubber_hand')[0][0]
                pose=box.data.root_state_w.clone();pose[:,:3]=robot.data.body_link_pos_w[:,hand]+torch.tensor([.12,0.,0.],device=b.device)
                pose[:,3:7]=torch.tensor([1.,0.,0.,0.],device=b.device);pose[:,7:]=0
                box.write_root_state_to_sim(pose);robot.set_joint_position_target(robot.data.joint_pos.clone());b.scene.write_data_to_sim()
                peak=0.
                for _ in range(8):
                    b.sim.step(render=False);b.scene.update(b.physics_dt)
                    peak=max(peak,float(b.scene[f'{side}_box_contact'].data.force_matrix_w.norm(dim=-1).max()))
                force_peaks[side]=peak;assert peak>0.,(side,'box contact sensor stayed zero')
                w.reset()
            # Observation correspondence after real sensor reads and partial/automatic resets.
            obs,_=w.reset();survivor=robot.data.root_state_w[1:].clone()
            histories={k:b.observation_manager.compute_group(k)[1:].clone() for k in ('amp','perception')}
            b._reset_idx(torch.tensor([0],device=b.device))
            torch.testing.assert_close(robot.data.root_state_w[1:],survivor)
            for k,v in histories.items():torch.testing.assert_close(b.observation_manager.compute_group(k)[1:],v)
            obs,_=w.reset()
            for step in range(4):
                previous=obs['amp'].reshape(4,10,60).clone();b.episode_length_buf[step]=b.max_episode_length-1
                obs,reward,done,info=w.step(torch.zeros(4,29,device=b.device))
                assert done[step] and all(torch.isfinite(x).all() for x in obs.values())
                terminal=info['terminal_observations'];ids=terminal['env_ids']
                torch.testing.assert_close(terminal['obs']['amp'].reshape(-1,10,60)[:,:-1],previous[ids,1:])
                current=obs['amp'].reshape(4,10,60);torch.testing.assert_close(current[ids],current[ids,-1:].expand(-1,10,-1))
            w.reset()
        runner=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'train'),device=b.device)
        for path in (ROOT/'docs/carrybox/wall5_ground_20261017/model.pt',ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-16_13-45-09_wall5_amp_stage_a/model_20600.pt'):
            try:runner.load(str(path),load_optimizer=False)
            except ValueError as e:assert 'environment' in str(e)
            else:raise AssertionError('Old contract accepted')
            try:runner.warm_start(str(path))
            except ValueError as e:assert 'shapes' in str(e)
            else:raise AssertionError('Old architecture accepted')
        before=copy.deepcopy(runner.alg.policy.state_dict());start=time.perf_counter()
        runner.learn(2,init_at_random_ep_len=False)
        elapsed=time.perf_counter()-start
        assert any(not torch.equal(v,before[k]) for k,v in runner.alg.policy.state_dict().items())
        assert runner.alg.motion_library.num_clips==13 and runner.alg.amp_valid.all()
        assert runner.alg.amp.running_count>0 and runner.alg.optimizer.state and runner.alg.amp_optimizer.state
        runner.save(str(OUT/'model.pt'))
        restored=CarryBoxWall5OnPolicyRunner(w,agent.to_dict(),log_dir=str(OUT/'resumed'),device=b.device)
        restored.load(str(OUT/'model.pt'))
        for k,v in runner.alg.amp.state_dict().items():torch.testing.assert_close(restored.alg.amp.state_dict()[k],v,rtol=0,atol=0)
        assert restored.alg.learning_rate==runner.alg.learning_rate
        stats=restored.alg.amp.running_count.clone();restored.alg._ensure_motion_library()
        torch.testing.assert_close(restored.alg.amp.running_count,stats)
        restored.learn(1,init_at_random_ep_len=False)
        for model in (restored.alg.policy,restored.alg.amp):assert all(torch.isfinite(v).all() for v in model.state_dict().values())
        for optimizer in (restored.alg.optimizer,restored.alg.amp_optimizer):
            for state in optimizer.state.values():
                for value in state.values():
                    if isinstance(value,torch.Tensor):assert torch.isfinite(value).all()
        obs=w.get_observations()
        exported=torch.jit.script(DepthPolicyExport(restored.alg.policy,obs));exported.save(str(OUT/'policy.pt'))
        with torch.inference_mode():torch.testing.assert_close(exported(obs['proprio'],obs['perception']),restored.alg.policy.act_inference(obs))
        assert b.checkpoint_contract()['migration_revision']==12
        result=dict(status='PASS',num_envs=4,iterations=2,resumed_iterations=1,two_iterations_elapsed_s=elapsed,
            source_live_parity=parity,ground_reset_first20ms_box_speeds=ground_velocity_peaks,production_rsi_velocity=rsi_velocity,contact_probe_force_n=force_peaks,environment_contract=b.checkpoint_contract(),
            amp_config=restored.alg.amp_config,normalizer_count=restored.alg.amp.running_count.item(),
            restored_learning_rate=restored.alg.learning_rate,observation_shapes={k:list(v.shape) for k,v in obs.items()},
            asset_audit=dict(knee_kp=robot.data.joint_stiffness[0,task.state(b).knees].tolist(),knee_kd=robot.data.joint_damping[0,task.state(b).knees].tolist(),
                effort_limits=robot.data.joint_effort_limits[0].tolist(),velocity_limits=robot.data.joint_vel_limits[0].tolist(),joint_names=robot.joint_names),
            partial_reset_preserved=True,terminal_history=True,old_strict_and_warmstart_rejected=True,export_pass=True,
            formal_training_started=False,convergence='not_evaluated')
        (OUT/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('TRAINING_V12_SMOKE_PASS',flush=True)
    finally:env.close()
try:main()
except BaseException:
    import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
