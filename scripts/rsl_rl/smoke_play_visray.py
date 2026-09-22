"""Finite real-simulator debug-draw smoke using the user's v0 checkpoint."""
import argparse
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
env=None;vis=None
import json
from pathlib import Path
import torch
import gymnasium as gym
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.agilekickball_env_cfg import AgileKickballEnvCfg,AgileKickballPPORunnerCfg
from perceptual_ball.rsl_rl_extensions.runner import BallRegressionOnPolicyRunner
from depth_ray_visualizer import DepthRayVisualizer

def main():
 global env,vis
 torch.set_num_threads(2);out=Path('docs/play_visray')
 cfg=AgileKickballEnvCfg();cfg.scene.num_envs=4;cfg.sim.device=args.device;cfg.seed=42
 cfg.viewer.eye=(3.5,3.5,2.6);cfg.viewer.lookat=(.7,0.,.8)
 env=gym.make('Template-Perceptual-Ball-AgileKickball-v0',cfg=cfg,render_mode='rgb_array')
 base=env.unwrapped;wrapped=RslRlVecEnvWrapper(env);agent=AgileKickballPPORunnerCfg()
 runner=BallRegressionOnPolicyRunner(wrapped,agent.to_dict(),log_dir=None,device=args.device)
 checkpoint='logs/rsl_rl/agilekickball_v0/2026-09-20_18-02-42_learning_fix/model_25000.pt'
 runner.load(checkpoint,load_optimizer=False);policy=runner.get_inference_policy(device=args.device)
 kb=base._kickball;kb.serve_speed_override=(.4,3.)
 with torch.inference_mode():
  obs,_=wrapped.reset();vis=DepthRayVisualizer(base)
  rng=torch.get_rng_state().clone();saved=obs['perception'].clone()
  vis.update(obs)
  torch.testing.assert_close(rng,torch.get_rng_state());torch.testing.assert_close(saved,obs['perception'])
  initial_points=vis.draw.get_num_points();initial_lines=vis.draw.get_num_lines()
  assert initial_points==4*48*27 and initial_lines==4*len(vis.line_ids)
  for _ in range(20):
   obs,_,_,_=wrapped.step(policy(obs));vis.update(obs)
   assert vis.draw.get_num_points()==initial_points and vis.draw.get_num_lines()==initial_lines
  # Render actual debug-draw primitives with the viewport camera into an artifact.
  env.render()  # lazily attaches the RGB annotator; its first read can be empty
  for _ in range(12):
   base.sim.render()
  frame=base.render()
  import numpy as np
  import imageio.v3 as iio
  iio.imwrite(out/'visray.png',frame)
  assert np.count_nonzero(frame)>1000,'RGB annotator did not produce a rendered scene'
  green=(frame[:,:,1].astype(float)>frame[:,:,0].astype(float)+35)&(frame[:,:,1].astype(float)>frame[:,:,2].astype(float)+35)
  green_pixels=int(green.sum())
  assert green_pixels>100,'No visible green debug rays/points in the rendered image'
  assert frame is not None and frame.shape[-1]==3
  vis.close();assert vis.draw.get_num_points()==vis.draw.get_num_lines()==0
  result=dict(checkpoint=checkpoint,task='Template-Perceptual-Ball-AgileKickball-v0',num_envs=4,
              steps=20,points=initial_points,lines=initial_lines,image_shape=list(frame.shape),green_pixels=green_pixels,
              depth_history_unchanged=True,rng_unchanged=True,cleanup=True,
              ballspeed=list(kb.serve_speed_override),screenshot='docs/play_visray/visray.png')
  (out/'smoke.json').write_text(json.dumps(result,indent=2)+'\n');print('VISRAY_SMOKE_PASS',json.dumps(result),flush=True)
try:main()
except BaseException:
 import traceback,sys,os
 traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
finally:
 if vis is not None:vis.close()
 if env is not None:env.close()
 app.close(wait_for_replicator=False)
