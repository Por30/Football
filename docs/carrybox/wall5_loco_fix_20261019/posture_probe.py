"""Check the real standing reset and first-episode physics, without a learned controller."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import json,traceback
from pathlib import Path
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from isaaclab.utils.math import euler_xyz_from_quat,wrap_to_pi
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task,carrybox_walled as parent
DOC=Path(__file__).resolve().parent

def main():
    torch.set_num_threads(2);cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    cfg.scene.num_envs=20;cfg.seed=42;cfg.sim.device=args.device
    for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
    env=task.Wall5CarryBoxEnv(cfg=cfg)
    try:
        w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);obs,_=w.reset();robot=env.scene['robot'];r=robot.data;s=parent.state(env)
        masses=robot.root_physx_view.get_masses().to(env.device);term=env.action_manager.get_term('joint_pos')
        ids=torch.arange(20,device=env.device);q=r.default_joint_pos.clone()
        # Bounded posture probe: four hip/ankle shifts; same knee/PD/noise/materials.
        hips=robot.find_joints(['left_hip_pitch_joint','right_hip_pitch_joint'],preserve_order=True)[0]
        ankles=robot.find_joints(['left_ankle_pitch_joint','right_ankle_pitch_joint'],preserve_order=True)[0]
        shift=torch.tensor([0.,-.05,-.10,-.15],device=env.device).repeat_interleave(5)
        q[:,hips]+=shift[:,None];q[:,ankles]-=shift[:,None]
        root=r.default_root_state.clone();root[:,:3]+=env.scene.env_origins;root[:,3:7]=root.new_tensor([1.,0.,0.,0.]);root[:,7:]=0
        robot.write_root_link_state_to_sim(root);robot.write_joint_state_to_sim(q,torch.zeros_like(q));env.sim.forward()
        root[:,2]+=parent.reference_ground_correction(env,ids,allow_lowering=True)
        robot.write_root_link_state_to_sim(root);env.sim.forward()
        foot_sensor=env.scene['body_contacts'].find_bodies(['left_ankle_roll_link','right_ankle_roll_link'],preserve_order=True)[0]
        def snap():
            roll,pitch,_=euler_xyz_from_quat(r.root_quat_w)
            com=(r.body_com_pos_w*masses[:,:,None]).sum(1)/masses.sum(1)[:,None]
            return dict(pitch=wrap_to_pi(pitch).tolist(),roll=wrap_to_pi(roll).tolist(),root=r.root_link_state_w.tolist(),q=r.joint_pos.tolist(),dq=r.joint_vel.tolist(),torque=r.applied_torque.tolist(),com=(com-env.scene.env_origins).tolist(),feet=(r.body_link_pos_w[:,s.feet]-env.scene.env_origins[:,None]).tolist(),force=env.scene['body_contacts'].data.net_forces_w[:,foot_sensor].tolist())
        initial=snap();frames=[];first=[None]*20;action=(q-term._offset)/term._scale
        # Collect pre-reset state in reward compute, just as the previous diagnosis.
        compute=env.reward_manager.compute
        def capture(dt):
            value=compute(dt);frames.append(snap());return value
        env.reward_manager.compute=capture
        with torch.inference_mode():
            for step in range(250):
                obs,reward,done,extra=w.step(action)
                for i in done.nonzero().flatten().tolist():
                    if first[i] is None:first[i]=step+1
        result=dict(shifts=shift.tolist(),initial=initial,frames=frames,first_end=first,joint_names=robot.joint_names)
        (DOC/'posture_probe.json').write_text(json.dumps(result)+'\n');print('POSTURE_PROBE',first,flush=True)
    finally:env.close()

try:main()
except BaseException:
    traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
