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
    cfg=CarryBoxWalled5EnvCfg();cfg.scene.num_envs=4;cfg.sim.device=args.device;cfg.seed=42
    for k in ('gpu_found_lost_pairs_capacity','gpu_found_lost_aggregate_pairs_capacity','gpu_total_aggregate_pairs_capacity'):setattr(cfg.sim.physx,k,262144)
    env=task.Wall5CarryBoxEnv(cfg=cfg)
    try:
        r=env.scene['robot'];ids=r.find_joints(['.*ankle_pitch_joint','.*ankle_roll_joint'])[0]
        v=r.root_physx_view
        result=dict(joints=[r.joint_names[i] for i in ids],data_effort=r.data.joint_effort_limits[:,ids].tolist(),data_velocity=r.data.joint_vel_limits[:,ids].tolist(),physx_effort=v.get_dof_max_forces()[:,ids].tolist(),physx_velocity=v.get_dof_max_velocities()[:,ids].tolist(),stiffness=v.get_dof_stiffnesses()[:,ids].tolist(),damping=v.get_dof_dampings()[:,ids].tolist())
        (DOC/'actual_limits.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    finally:env.close()

try:main()
except BaseException:
    traceback.print_exc();raise
finally:app.close(wait_for_replicator=False)
