"""Revision23: complete data, bilateral grasp incentives and exploit counterexamples."""
import unittest
import hashlib
import json
from pathlib import Path
import torch
import test_carrybox  # Load the repository's CPU IsaacLab math fixtures.
from isaaclab.utils.math import quat_apply, quat_apply_inverse
from perceptual_ball.carrybox_wall5 import (Wall5MotionLibrary, AMP_DATASET_PATH, GROUND_DATASET_PATH,
    ground_pickup_frame_ids, grasp_components, grasp_reward_geometry)

class GraspDataTests(unittest.TestCase):
    def test_full_three_pickups_hash_lengths_weights_and_last_windows(self):
        lib = Wall5MotionLibrary(AMP_DATASET_PATH)
        self.assertEqual(lib.num_clips, 15)
        self.assertEqual(lib.metadata['total_frames'], 4155)
        manifest = json.loads((Path(AMP_DATASET_PATH)/'amp_manifest.json').read_text())
        for n, frames in enumerate((192, 178, 129), 1):
            name = f'pick_up/pick_up_{n:02}.pt'
            i = lib.clip_names.index(name)
            self.assertEqual(len(lib.clips[i][0]), frames)
            self.assertAlmostEqual(float(lib.weights[i]), .4/3, places=6)
            row = next(r for r in manifest['clips'] if r['file'] == name)
            self.assertEqual(hashlib.sha256((lib.root/name).read_bytes()).hexdigest(), row['sha256'])
            starts = torch.tensor([0., frames-1-9*60/50])
            windows = lib.windows(torch.tensor([i,i]), starts)
            self.assertEqual(tuple(windows.shape), (2,600))
            self.assertTrue(torch.isfinite(windows).all())
            torch.testing.assert_close(windows[1].reshape(10,60)[-1,1:30],lib.clips[i][0][-1])
        self.assertNotEqual(AMP_DATASET_PATH, GROUND_DATASET_PATH)
        ground = json.loads((Path(GROUND_DATASET_PATH)/'amp_manifest.json').read_text())
        self.assertEqual([r['file'] for r in ground['clips'] if r['group']=='pickUp'], ['pick_up/pick_up_03.pt'])
        for n in (1,2):
            d=torch.load(Path(AMP_DATASET_PATH)/f'pick_up/pick_up_{n:02}.pt',weights_only=True)
            self.assertEqual(len(ground_pickup_frame_ids(d)),0)
        d=torch.load(Path(GROUND_DATASET_PATH)/'pick_up/pick_up_03.pt',weights_only=True)
        ids=ground_pickup_frame_ids(d);self.assertEqual(ids[(ids>=0)&(ids<32)].tolist(),list(range(32)))

class GraspRewardTests(unittest.TestCase):
    def evaluate(self, hands, force=(0.,0.), clearance=.005, xy=.52):
        h=torch.tensor(hands,dtype=torch.float32).reshape(-1,2,3);n=len(h)
        d=torch.tensor([xy,0.,-.65]).expand(n,-1)
        return grasp_components(d,torch.zeros(n),torch.zeros(n),h,torch.tensor([.15,.15,.125]),
            torch.tensor(force).float().expand(n,-1),torch.full((n,),clearance),grasp_reward_geometry())

    def test_stand_reach_contact_lift_have_increasing_total_reward(self):
        cases=[self.evaluate([[0,.25,.55],[0,-.25,.55]]),
               self.evaluate([[0,.20,.25],[0,-.20,.25]]),
               self.evaluate([[0,.19,0],[0,-.19,0]]),
               self.evaluate([[0,.19,0],[0,-.19,0]],(5.,0.)),
               self.evaluate([[0,.19,0],[0,-.19,0]],(5.,5.)),
               self.evaluate([[0,.19,0],[0,-.19,0]],(5.,5.),clearance=.13),
               self.evaluate([[0,.19,0],[0,-.19,0]],(5.,5.),clearance=.25)]
        values=[float(x['walk_task']+x['carryup_task']) for x in cases]
        self.assertTrue(all(a<b for a,b in zip(values,values[1:])),values)
        self.assertLess(float(cases[0]['walk_task']),.21)

    def test_stationary_far_heading_cannot_outpay_near_grasp_preparation(self):
        hands=[[0.,.25,.55],[0.,-.25,.55]]
        far=self.evaluate(hands,xy=1.2)
        near=self.evaluate(hands,xy=.52)
        self.assertLess(float(far['walk_task']+far['carryup_task']),
                        float(near['walk_task']+near['carryup_task']))
        delta=torch.tensor([[1.2,0.,-.65]])
        moving=grasp_components(delta,torch.tensor([.85]),torch.zeros(1),torch.tensor([hands]),
            torch.tensor([.15,.15,.125]),torch.zeros(1,2),torch.tensor([.005]),grasp_reward_geometry())
        self.assertGreater(float(moving['walk_task']),1.49)

    def test_no_average_hand_cheat_or_unheld_lift(self):
        close=self.evaluate([[0,.19,0],[0,-.19,0]])
        far=self.evaluate([[0,2.,0],[0,-2.,0]])
        one_far=self.evaluate([[0,.19,0],[0,-2.,0]])
        self.assertLess(float(far['carryup_task']),.001)
        self.assertLess(float(one_far['carryup_task']),float(close['carryup_task'])/10)
        for force in ((0.,0.),(30.,0.)):
            raised=self.evaluate([[0,.19,0],[0,-.19,0]],force,clearance=.5)
            self.assertEqual(float(raised['lift']),0.)
        same_side=self.evaluate([[0,.19,0],[0,.19,0]],(5.,5.),clearance=.5)
        self.assertEqual(float(same_side['lift']),0.)
        self.assertEqual(float(same_side['bilateral']),0.)

    def test_force_saturation_and_standoff(self):
        h=[[0,.19,0],[0,-.19,0]]
        a,b=self.evaluate(h,(5.,5.)),self.evaluate(h,(5000.,5000.))
        torch.testing.assert_close(a['carryup_task'],b['carryup_task'])
        for xy in (.13,.25,.34):
            self.assertLess(float(self.evaluate(h,xy=xy)['walk_task']),float(self.evaluate(h,xy=.52)['walk_task']))
        self.assertEqual(float(self.evaluate(h,(5.,5.),clearance=.3,xy=.25)['crowding']),0.)

    def test_box_yaw_and_tilt_use_local_surface_geometry(self):
        # A rigid world rotation must not change the distance to the oriented box.
        local=torch.tensor([[[0.,.22,.05],[0.,-.21,.02]]])
        for q in ([.70710678,0,0,.70710678],[.96592583,.25881905,0,0]):
            quat=torch.tensor(q).reshape(1,1,4).expand(1,2,4)
            world=quat_apply(quat,local)
            recovered=quat_apply_inverse(quat,world)
            torch.testing.assert_close(self.evaluate(local)['surface_distance'],
                                       self.evaluate(recovered)['surface_distance'],atol=1e-6,rtol=1e-6)
        far=self.evaluate(local,xy=1.2)
        self.assertEqual(float(far['reach']),0.)
        self.assertTrue(all(torch.isfinite(x).all() for x in far.values()))

if __name__=='__main__':unittest.main()
