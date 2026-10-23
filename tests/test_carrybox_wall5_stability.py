"""Regression coverage for source quotas and terminal-transition attribution."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'source/perceptual_ball/perceptual_ball/carrybox_physhsi.py'
spec=importlib.util.spec_from_file_location('wall5_reset_quota',p)
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)

class QuotaTests(unittest.TestCase):
    def test_standard_survival_failure_timeout_boundaries(self):
        path=Path('/home/cao/IsaacLab/source/isaaclab/isaaclab/envs/mdp/rewards.py')
        tree=ast.parse(path.read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='is_alive')
        ns={'torch':torch,'ManagerBasedRLEnv':object}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'isaaclab-is-alive','exec'),ns)
        # Normal, failure, timeout, and simultaneous timeout + failure.
        env=NS(termination_manager=NS(terminated=torch.tensor([False,True,False,True]),
                                     time_outs=torch.tensor([False,False,True,True])))
        for weight in (1.,3.):
            raw=ns['is_alive'](env)*.02*weight
            torch.testing.assert_close(raw,weight*torch.tensor([.02,0.,.02,0.]))
            torch.testing.assert_close(.75*raw,weight*torch.tensor([.015,0.,.015,0.]))

    def assign(self,ids,n=4096,reference=.8,probabilities=(2/3,1/6,1/6)):
        skills,default=helpers.fixed_hybrid(ids,n,reference,probabilities)
        return torch.where(default,0,skills+1)

    def test_counts_and_partial_reset_survival_bias(self):
        ids=torch.arange(4096);labels=self.assign(ids)
        self.assertEqual(torch.bincount(labels,minlength=4).tolist(),[819,2185,546,546])
        original=labels.clone()
        # Empty-hand slots end 100 times while the held slots never end.
        for _ in range(100):
            reset=ids[labels<2];reset=reset[torch.randperm(len(reset))]
            labels[reset]=self.assign(reset)
        torch.testing.assert_close(labels,original)
        torch.testing.assert_close(self.assign(torch.tensor([4095,12,3000,0,3500])),original[[4095,12,3000,0,3500]])

    def test_small_batches_empty_batch_and_overrides(self):
        for n in (1,2,4,16,64):
            labels=self.assign(torch.arange(n),n)
            self.assertEqual(len(labels),n)
            self.assertTrue(((labels>=0)&(labels<4)).all())
        self.assertEqual(self.assign(torch.empty(0,dtype=torch.long)).numel(),0)
        self.assertEqual(self.assign(torch.arange(4),4,1.,(0.,0.,1.)).tolist(),[3]*4)
        self.assertEqual(self.assign(torch.arange(4),4,0.).tolist(),[0]*4)
        for r,p in ((-1.,(1.,0.,0.)),(float('nan'),(1.,0.,0.)),(.8,(.5,.5)),(.8,(1.,1.,0.)),(.8,(-1.,1.,1.))):
            with self.assertRaises(ValueError):self.assign(torch.arange(4),4,r,p)
        with self.assertRaises(ValueError):self.assign(torch.arange(1),0)

    def test_terminal_default_stat_uses_old_episode(self):
        source=ROOT/'source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py'
        tree=ast.parse(source.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Wall5CarryBoxEnv')
        step=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='step')
        # Execute the production attribution block against a parent that resets
        # all slots. The rest of step is unrelated reward/kinematic diagnostics.
        stop=next(i for i,n in enumerate(step.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets))
        step.body=step.body[:stop]+[ast.Return(value=ast.Name(id='result',ctx=ast.Load()))]
        cls.body=[step];cls.bases=[ast.Name(id='Parent',ctx=ast.Load())]
        class Parent:
            def step(self,action):
                self.s.default_reset.zero_();self.s.skills.fill_(2)
                return [None,None,None,None,{}]
        ns={'Parent':Parent,'state':lambda e:e.s}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),'production-step','exec'),ns)
        env=ns['Wall5CarryBoxEnv']();env.s=NS(skills=torch.tensor([0,2]),default_reset=torch.tensor([True,False]),reset_counts=torch.ones(4))
        result=env.step(None)
        self.assertEqual(float(result[-1]['log']['Sampling/default_transition_fraction']),.5)
        self.assertFalse(env.s.default_reset.any())

if __name__=='__main__':unittest.main()
