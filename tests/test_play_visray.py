"""Camera-frame geometry and read-only drawing using production perception math."""
import argparse
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch
import test_soccer_v3 as fixtures
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.perception import synthetic_ball_depth_image

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
visual=load('depth_ray_visualizer',ROOT/'scripts/rsl_rl/depth_ray_visualizer.py')
cli=load('visray_cli',ROOT/'scripts/rsl_rl/cli_args.py')

class Draw:
    def __init__(self):self.lines=[];self.points=[]
    def clear_lines(self):self.lines=[]
    def clear_points(self):self.points=[]
    def draw_lines(self,starts,ends,colors,widths):self.lines=list(zip(starts,ends,colors,widths))
    def draw_points(self,points,colors,sizes):self.points=list(zip(points,colors,sizes))

class VisrayTests(unittest.TestCase):
    def scene(self,n=2):
        env,_=fixtures.state_fixture(n);q=env.scene['robot'].data
        q.body_link_pos_w.zero_();q.body_link_quat_w=torch.zeros(n,2,4);q.body_link_quat_w[:,:,0]=1.
        env.scene['ball'].data.root_pos_w[:]=torch.tensor([0.,0.,1.])
        params=dict(robot_cfg=NS(name='robot',body_ids=[0]),ball_cfg=NS(name='ball'),width=6,height=4,
                    near=.1,far=3.,ball_radius=.11,offset_pos=(0.,0.,0.),offset_quat=(1.,0.,0.,0.),vertical_fov_deg=58.)
        term=synthetic_ball_depth_image(NS(params=params),env)
        env.observation_manager=NS(active_terms={'perception':['depth_image']},
                                  _group_obs_term_cfgs={'perception':[NS(func=term)]})
        return env,term,params

    def test_flag_default_off_and_enabled_with_ballspeed(self):
        parser=argparse.ArgumentParser();cli.add_visray_arg(parser);cli.add_ball_speed_arg(parser)
        self.assertFalse(parser.parse_args([]).visray)
        args=parser.parse_args(['--ballspeed','.4','3','--visray'])
        self.assertTrue(args.visray);self.assertEqual(args.ballspeed,(.4,3.))

    def test_pixel_endpoints_match_actual_sphere_depth(self):
        env,t,p=self.scene();depth=t(env,**p)
        origin,points,valid,hits=visual.depth_ray_geometry(t,depth)
        self.assertTrue(valid.all());self.assertTrue(hits[:,2*6+3].all())
        torch.testing.assert_close(points[:,2*6+3,2],torch.full((2,),.89),atol=1.e-6,rtol=1.e-6)
        distances=(points-env.scene['ball'].data.root_pos_w[:,None]).norm(dim=-1)
        torch.testing.assert_close(distances[hits],torch.full_like(distances[hits],.11),atol=2.e-6,rtol=2.e-6)
        # Off-axis range is Euclidean, so its optical z must be shorter than range.
        self.assertLess(points[0,0,2],3.)
        torch.testing.assert_close((points-origin[:,None]).norm(dim=-1),depth.flatten(1))

    def test_body_and_mount_transforms_and_environment_origins(self):
        env,t,_=self.scene();q=env.scene['robot'].data
        q.body_link_pos_w[:,0]=torch.tensor([[2.,3.,4.],[-2.,0.,1.]])
        q.body_link_quat_w[:,0]=torch.tensor([2**-.5,0.,2**-.5,0.])
        t.offset_pos[:]=torch.tensor([0.,0.,.5])
        # Body rotates optical +z to world +x. Mount translation follows the body.
        origin,points,_,_=visual.depth_ray_geometry(t,torch.ones(2,4,6))
        torch.testing.assert_close(origin,q.body_link_pos_w[:,0]+torch.tensor([.5,0.,0.]),atol=1.e-6,rtol=1.e-6)
        torch.testing.assert_close(points[:,15],origin+torch.tensor([1.,0.,0.]),atol=1.e-6,rtol=1.e-6)
        t.offset_quat[:]=torch.tensor([0.,0.,1.,0.])  # additional 180 deg local y
        _,points,_,_=visual.depth_ray_geometry(t,torch.ones(2,4,6))
        torch.testing.assert_close(points[:,15],origin-torch.tensor([1.,0.,0.]),atol=1.e-6,rtol=1.e-6)

    def test_latest_frame_rng_history_colors_and_cleanup(self):
        env,t,p=self.scene();depth=t(env,**p);history=torch.stack([torch.full_like(depth,3.),depth],1)
        draw=Draw();vis=visual.DepthRayVisualizer(env,draw=draw)
        saved=history.clone();rng=torch.get_rng_state().clone()
        vis.update({'perception':history});first_points=list(draw.points)
        self.assertEqual(len(draw.points),48)
        self.assertEqual(draw.points[15][2],5.)
        self.assertAlmostEqual(draw.points[15][0][2],.89,places=5)
        self.assertIn(0,vis.line_ids.tolist());self.assertIn(23,vis.line_ids.tolist())
        self.assertTrue(all(c[1]==1. and c[0]==c[2]==0. for _,c,_ in draw.points))
        vis.update({'perception':history});self.assertEqual(draw.points,first_points)
        torch.testing.assert_close(history,saved);torch.testing.assert_close(torch.get_rng_state(),rng)
        vis.close();self.assertEqual(draw.points,[]);self.assertEqual(draw.lines,[])

    def test_invalid_shape_and_nonfinite_pixels(self):
        env,t,p=self.scene();depth=t(env,**p)
        with self.assertRaises(ValueError):visual.depth_ray_geometry(t,depth[0])
        depth[0,0,0]=float('nan');draw=Draw();vis=visual.DepthRayVisualizer(env,draw=draw)
        vis.update({'perception':depth[:,None]});self.assertEqual(len(draw.points),47)
        self.assertTrue(torch.isfinite(torch.tensor([x[0] for x in draw.points])).all())
        with self.assertRaises(ValueError):vis.update({'perception':depth})
        env.observation_manager._group_obs_term_cfgs['perception'][0].func=NS()
        with self.assertRaisesRegex(ValueError,'capture-time pose'):visual.DepthRayVisualizer(env,draw=draw)

if __name__=='__main__':unittest.main()
