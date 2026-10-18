"""Four-env RSI reset only; no training or checkpoint writes."""
import argparse
from isaaclab.app import AppLauncher
parser=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args();app=AppLauncher(args).app
import json
from pathlib import Path
from unittest.mock import patch
import torch,gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg,CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_walled_env_cfg import CarryBoxWalled4EnvCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as task
OUT=Path(__file__).resolve().parent

def main():
    torch.set_num_threads(2)
    cfg=CarryBoxWalled5EnvCfg();agent=CarryBoxWalled5PPORunnerCfg()
    assert cfg.reset_skill_probabilities==(.8,0.,.2) and cfg.reference_init and cfg.held_box_reference_reset
    assert CarryBoxWalled4EnvCfg().reset_skill_probabilities==(.6,.3,.1)
    cfg.scene.num_envs=4;cfg.seed=42;cfg.sim.device=args.device
    for name in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,name,262144)
    env=gym.make('Template-Perceptual-Ball-CarryBox-Walled5-v0',cfg=cfg)
    try:
        b=env.unwrapped;w=RslRlVecEnvWrapper(env,clip_actions=agent.clip_actions);robot=b.scene['robot'];box=b.scene['box']
        records=[];counts=[0,0,0]
        with torch.inference_mode():
            for _ in range(12):
                obs,_=w.reset();s=task.state(b)
                assert all(torch.isfinite(v).all() for v in obs.values())
                bottom=task.base.lift_geometry(b)[0];loco=s.skills==0;hold=s.skills==2
                assert not (s.skills==1).any()
                torch.testing.assert_close(bottom[loco],torch.full_like(bottom[loco],.005),atol=2e-5,rtol=0)
                assert (bottom[hold]>.12).all()
                counts[0]+=int(loco.sum());counts[2]+=int(hold.sum())
                records.append(dict(skills=s.skills.tolist(),box_bottom_m=bottom.tolist()))
            assert counts[0]>0 and counts[2]>0
            # Force each native hold frame (the remaining frames repeat the stable pose).
            s=task.state(b);slot=s.library.clip_names.index('hold/hold_box_01.pt')
            hand_distance=[];box_speeds=[]
            cfg.reset_skill_probabilities=(0.,0.,1.)
            original_randint=torch.randint
            for frame in list(range(21))+[298]:
                def randint(high,size,*a,**kw):
                    if high==int(s.library.lengths[slot])-1:
                        return torch.full(size,frame,device=kw.get('device'),dtype=torch.long)
                    return original_randint(high,size,*a,**kw)
                with patch.object(task.torch,'randint',side_effect=randint):obs,_=w.reset()
                assert (s.skills==2).all() and (task.base.lift_geometry(b)[0]>.12).all()
                hands=robot.data.body_pos_w[:,s.hands].mean(1)
                distance=(hands-box.data.root_pos_w).norm(dim=-1)
                hand_distance.append(float(distance.max()));assert distance.max()<.2
                robot.set_joint_position_target(robot.data.joint_pos.clone());b.scene.write_data_to_sim()
                peak=0.
                for _ in range(4):
                    b.sim.step(render=False);b.scene.update(b.physics_dt)
                    assert torch.isfinite(robot.data.root_state_w).all() and torch.isfinite(box.data.root_state_w).all()
                    peak=max(peak,float(box.data.root_lin_vel_w.norm(dim=-1).max()))
                box_speeds.append(peak)
            cfg.reset_skill_probabilities=(.8,0.,.2)
            obs,_=w.reset();before=robot.data.root_state_w[1:].clone();before_box=box.data.root_state_w[1:].clone()
            b._reset_idx(torch.tensor([0],device=b.device));torch.testing.assert_close(robot.data.root_state_w[1:],before);torch.testing.assert_close(box.data.root_state_w[1:],before_box)
            obs,_=w.reset();b.episode_length_buf[0]=b.max_episode_length-1
            obs,_,done,_=w.step(torch.zeros(4,29,device=b.device));assert done[0]
            assert all(torch.isfinite(v).all() for v in obs.values())
        contract=b.checkpoint_contract();assert contract['migration_revision']==13 and contract['held_box_reference_reset']
        assert contract['reset_probs']==[.8,0.,.2] and contract['amp_shape']==[10,60]
        (OUT/'smoke.json').write_text(json.dumps(dict(status='PASS',num_envs=4,random_reset_counts=counts,random_resets=records,
            hold_frames=list(range(21))+[298],max_hand_center_distance_m=max(hand_distance),first20ms_box_speed_m_s=box_speeds,
            contract=contract,partial_reset=True,auto_reset=True,training_started=False),indent=2)+'\n')
        print('HOLD_RSI_SMOKE_PASS',flush=True)
    finally:env.close()
try:main()
except BaseException:
    import traceback;traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
