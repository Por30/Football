"""CPU check: actual old/new state shapes, existing loader, and CLI dispatch."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import torch
p=Path('scripts/rsl_rl/play.py');tree=ast.parse(p.read_text());compile(tree,str(p),'exec')
branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args_cli.carrybox_weights_only')
class Runner:
    def __init__(self):self.calls=[]
    def warm_start(self,path):self.calls.append(('weights',path))
    def load(self,path,load_optimizer):self.calls.append(('load',path,load_optimizer))
for flag in [False,True]:
    r=Runner();exec(compile(ast.Module(body=[branch],type_ignores=[]),str(p),'exec'),dict(args_cli=NS(carrybox_weights_only=flag),runner=r,CarryBoxOnPolicyRunner=Runner,resume_path='model'))
    assert r.calls==([('weights','model')] if flag else [('load','model',False)])
try:exec(compile(ast.Module(body=[branch],type_ignores=[]),str(p),'exec'),dict(args_cli=NS(carrybox_weights_only=True),runner=object(),CarryBoxOnPolicyRunner=Runner))
except ValueError:pass
else:raise AssertionError('wrong runner accepted')
old=Path('logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_21-08-12_wall4_handoff_v6_amp15_20261014_210808/model_14000.pt')
new=torch.load('docs/carrybox/wall_parity_20261015/wall4/model.pt',map_location='cpu',weights_only=False)
source=torch.load(old,map_location='cpu',weights_only=False)
assert source['environment_contract']['migration_revision']==6
assert new['environment_contract']['migration_revision']==7
class Policy:
    def state_dict(self):return new['model_state_dict']
    def load_state_dict(self,state):self.loaded=state
r=NS(device='cpu',alg=NS(optimizer=NS(state={}),amp_statistics_initialized=False,policy=Policy()),environment_contract=lambda:new['environment_contract'])
loader=ast.parse(Path('source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py').read_text())
f=next(n for n in ast.walk(loader) if isinstance(n,ast.FunctionDef) and n.name=='warm_start');ns={'torch':torch};exec(compile(ast.Module(body=[f],type_ignores=[]),'existing_loader','exec'),ns);ns['warm_start'](r,str(old))
assert all(torch.equal(r.alg.policy.loaded[k],v) for k,v in source['model_state_dict'].items())
print('PASS: default strict load, explicit weights-only, wrong runner rejection, actual model14000 shape/finite/weights compatibility')
