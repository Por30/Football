"""Serial launch gates and motionless-obstacle API contracts; no GPU/process launch."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import torch
import test_carrybox
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as mdp

spec = importlib.util.spec_from_file_location('queue_wall4', Path(__file__).parents[1]/'scripts/rsl_rl/queue_wall4.py')
queue = importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)


class QueueTests(unittest.TestCase):
    def test_locked_obstacle_reset_clears_velocity(self):
        class Scene(dict): pass
        class Object:
            def __init__(self, dynamic=False):
                p=torch.zeros(2,13);p[:,3]=1
                self.data=NS(root_state_w=p.clone(),default_root_state=p.clone())
                self.dynamic=dynamic;self.poses=[]
            def write_root_state_to_sim(self,p,env_ids=None):
                self.poses.append(p.clone())
                self.data.root_state_w[env_ids]=p
            def set_local_poses(self,position,orientation,indices=None):
                p=torch.cat((position,orientation),-1)
                self.poses.append(p.clone());self.data.root_state_w[indices,:7]=p
        scene=Scene({n:Object(n=='box') for n in ['box','platform','wall','cylinder0','cylinder1','cylinder2']})
        scene.env_origins=torch.zeros(2,3)
        scene['robot']=NS(data=NS(root_pos_w=torch.zeros(2,3),root_quat_w=torch.tensor([[1.,0.,0.,0.]]).repeat(2,1)))
        state=NS(skills=torch.zeros(2,dtype=torch.long),search=torch.zeros(2,dtype=torch.bool),
                 achieved=torch.zeros(2,dtype=torch.bool),curriculum=NS(degrees=10.),paired=None)
        env=NS(scene=scene,device='cpu',_walled=state,cfg=NS(reset_skill_probabilities=(.8,.15,.05),reference_init=False,search_prob=.02))
        with patch.object(mdp.base,'reset_box'),patch.object(mdp,'reset_camera'):
            mdp.reset_scene(env,torch.arange(2))
        for name in ['platform','wall','cylinder0','cylinder1','cylinder2']:
            self.assertEqual(scene[name].poses[0].shape,(2,13))
            self.assertEqual(float(scene[name].poses[0][:,7:].abs().max()),0.)

    def test_pid_identity_uses_starttime_boot_and_argv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/'123';d.mkdir();(root/'sys/kernel/random').mkdir(parents=True)
            (root/'sys/kernel/random/boot_id').write_text('boot-a')
            (d/'cwd').symlink_to(root,target_is_directory=True)
            # Include spaces/parentheses in comm: starttime is field22 (tail index19).
            fields=['S']+['0']*18+['100']+['0']*4
            (d/'stat').write_text('123 (a (name)) '+' '.join(fields))
            (d/'cmdline').write_bytes(b'python\0train.py\0--task\0football\0')
            first=queue.identity(123,root);self.assertEqual(first['start_ticks'],100)
            fields[19]='101';(d/'stat').write_text('123 (a (name)) '+' '.join(fields))
            self.assertNotEqual(queue.identity(123,root),first)
            (d/'stat').unlink();self.assertIsNone(queue.identity(123,root))

    def test_completion_rejects_crash_wrong_iteration_truncation_nonfinite(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'train.log';model=Path(tmp)/'model_49999.pt'
            log.write_text('Learning iteration 49999/50000\n')
            state={'iter':49999,'soccer_schema_version':3,'model_state_dict':{'x':torch.ones(2)},
                   'optimizer_state_dict':{'state':{},'param_groups':[{}]},
                   'agile_v4_return_curriculum':{'config':{'revision':'return_to_sender_20261012'}}}
            def save():
                torch.save(state,model);os.utime(model,(time.time()-30,)*2)
            save();self.assertEqual(queue.verify_completion(log,model,49999,50000)['iteration'],49999)
            log.write_text('Learning iteration 49999/50000\nTraceback (most recent call last)\n')
            with self.assertRaisesRegex(ValueError,'Fatal'):queue.verify_completion(log,model,49999,50000)
            log.write_text('Learning iteration 49800/50000\n')
            with self.assertRaisesRegex(ValueError,'Final learning'):queue.verify_completion(log,model,49999,50000)
            log.write_text('Learning iteration 49999/50000\n');state['iter']=100;save()
            with self.assertRaisesRegex(ValueError,'iteration'):queue.verify_completion(log,model,49999,50000)
            state['iter']=49999;state['model_state_dict']['x'][0]=float('nan');save()
            with self.assertRaisesRegex(ValueError,'Nonfinite'):queue.verify_completion(log,model,49999,50000)
            model.write_bytes(b'truncated');os.utime(model,(time.time()-30,)*2)
            with self.assertRaises(Exception):queue.verify_completion(log,model,49999,50000)

    def test_source_receipt_and_resource_gates(self):
        with patch.object(queue,'source_hashes',return_value={'a':'new'}):
            with self.assertRaisesRegex(ValueError,'changed'):queue.verify_hashes({'a':'old'})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for variant in (3,4):
                d=root/f'docs/carrybox/wall4_repair/walled{variant}';d.mkdir(parents=True)
                (d/'smoke.json').write_text(json.dumps(dict(status='PASS',iterations=20,num_envs=4,resumed_iterations=2,resets=10)))
                (d/'smoke.log').write_text('CARRYBOX_WALLED_SMOKE_PASS')
                (d/'geometry.json').write_text(json.dumps(dict(status='PASS',collision_checks={'wall':True},depth_changes={'wall':True})))
                (d/'geometry.log').write_text('CARRYBOX_WALLED_SMOKE_PASS')
            with patch.object(queue,'ROOT',root):
                self.assertEqual(len(queue.verify_smokes()),2)
                (d/'smoke.log').write_text('CUDA error: illegal memory access\nCARRYBOX_WALLED_SMOKE_PASS')
                with self.assertRaisesRegex(ValueError,'not ready'):queue.verify_smokes()
        obj=queue.Queue.__new__(queue.Queue);obj.config={'gpu_uuid':'gpu'};obj.record=lambda *a,**kw:None
        with patch.object(queue,'gpu_status',return_value=dict(uuid='gpu',free_mib=100)),patch.object(queue,'training_processes',return_value=[]):
            self.assertFalse(obj.resources(1000))
        with patch.object(queue,'gpu_status',return_value=dict(uuid='gpu',free_mib=10000)),patch.object(queue,'training_processes',return_value=[{'pid':3}]):
            self.assertFalse(obj.resources(1000))

    def test_duplicate_lock_and_launch_intent_prevent_relaunch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'lock'
            with queue.acquire_lock(path):
                with self.assertRaises(BlockingIOError):queue.acquire_lock(path)
            obj=queue.Queue.__new__(queue.Queue);obj.directory=Path(tmp)
            (Path(tmp)/'launch_intent.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'automatic relaunch'):obj.run()

if __name__=='__main__':unittest.main()
