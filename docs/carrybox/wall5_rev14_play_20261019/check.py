from pathlib import Path
import json,hashlib,importlib.util
import torch
import test_carrybox
from perceptual_ball.rsl_rl_extensions.carrybox_wall5 import CarryBoxWall5ActorCritic
DOC=Path(__file__).resolve().parent;ROOT=DOC.parents[2]
script=DOC/'play.py';compile(script.read_text(),str(script),'exec')
spec=importlib.util.spec_from_file_location('rev14_command_check',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert module.ROOT==ROOT and module.ARCHIVE.is_dir()
checkpoint=ROOT/'logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/model_11200.pt'
x=torch.load(checkpoint,map_location='cpu',weights_only=False)
previous=json.loads((ROOT/'docs/carrybox/wall5_play11000_20261019/recording.json').read_text())
assert x['iter']==11200 and x['carrybox_schema']==2
assert json.loads(json.dumps(x['environment_contract']))==previous['environment_contract']
for path,digest in previous['archived_sources'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
obs={'proprio':torch.zeros(4,372),'perception':torch.ones(4,4,27,48),'critic_state':torch.zeros(4,108)}
p=CarryBoxWall5ActorCritic(obs,{'policy':['proprio','perception'],'critic':['critic_state']},29,actor_hidden_dims=[512,256,256],critic_hidden_dims=[512,256,256])
p.load_state_dict(x['model_state_dict'],strict=True);p.eval()
with torch.inference_mode():
 a=p.act_inference(obs);assert a.shape==(4,29) and torch.isfinite(a).all()
result=dict(status='PASS',checkpoint=str(checkpoint),iteration=11200,revision=14,strict_model_load=True,actor_output_shape=list(a.shape),
 archived_files_hash_matched_to_prior_20s_video=True,checkpoint_contract_matches_prior_20s_video=True,
 syntax=True,gpu_simulation_run=False,gui_run=False)
(DOC/'check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
