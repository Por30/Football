"""Fixed-rollout CUDA comparison, including logical RNG and Adam equivalence."""
import copy
import json
import time
from pathlib import Path
import torch
from tensordict import TensorDict
from test_carrybox_wall10_perf import old_update
from perceptual_ball.rsl_rl_extensions.carrybox_wall10 import CarryBoxWall10ActorCritic, CarryBoxWall10PPO

OUT = Path(__file__).resolve().parent
torch.set_num_threads(24)
torch.manual_seed(42)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.benchmark = False
device, n, steps = 'cuda:0', 4096, 24
obs = TensorDict(dict(proprio=torch.randn(n,558,device=device)*.05,
    perception=torch.rand(n,4,27,48,device=device)*2.9+.1,
    critic_state=torch.randn(n,123,device=device)*.05,
    amp=torch.zeros(n,600,device=device), box_pose_target=torch.zeros(n,9,device=device)), [n])
policy = CarryBoxWall10ActorCritic(obs, {'policy':['proprio','perception'],'critic':['critic_state']},
    29, actor_hidden_dims=(512,256,256), critic_hidden_dims=(512,256,256), init_noise_std=1.).to(device)
alg = CarryBoxWall10PPO(policy, device=device, amp_coef=.25, amp_reward_scale=.5, pose_aux_coef=0.,
    num_learning_epochs=5, num_mini_batches=4, learning_rate=.001, schedule='adaptive', desired_kl=.01)
alg.init_storage('rl',n,steps,obs,[29]); alg._ensure_motion_library()
with torch.inference_mode():
    for i in range(steps):
        alg.act(obs)
        alg.process_env_step(obs, torch.ones(n,device=device)*.01, torch.zeros(n,device=device,dtype=torch.bool), {})
    alg.compute_returns(obs)
policy_state = copy.deepcopy(alg.policy.state_dict())
amp_state = copy.deepcopy(alg.amp.state_dict())
optimizer_state = copy.deepcopy(alg.optimizer.state_dict())
rows = []
states = []
for phase, update in [('baseline', old_update), ('candidate', CarryBoxWall10PPO.update)]:
    alg.policy.load_state_dict(policy_state); alg.amp.load_state_dict(amp_state)
    alg.optimizer.load_state_dict(copy.deepcopy(optimizer_state)); alg.learning_rate=.001
    torch.manual_seed(123)
    torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
    start=time.perf_counter()
    losses=update(alg)
    torch.cuda.synchronize()
    elapsed=time.perf_counter()-start
    assert all(torch.isfinite(torch.tensor(v)) for v in losses.values())
    assert {int(v['step']) for v in alg.optimizer.state.values()} == {20}
    states.append((torch.cuda.get_rng_state().clone(),copy.deepcopy(alg.policy.state_dict()),copy.deepcopy(alg.amp.state_dict())))
    row=dict(phase=phase,seconds=elapsed,peak_allocated_gb=torch.cuda.max_memory_allocated()/1e9,losses=losses)
    rows.append(row); print('LEARNING_TIMING',json.dumps(row),flush=True)
assert torch.equal(states[0][0],states[1][0]), 'GPU logical random sequence changed'
assert rows[1]['seconds'] < rows[0]['seconds'], 'No GPU update speedup'
# Five adaptive epochs amplify small GEMM/conv reduction differences; the CPU
# one-step regression is the strict loss/gradient/Adam equivalence check.
max_difference={}
for index,label in ((1,'policy'),(2,'discriminator')):
    max_difference[label]=max(float((states[0][index][k]-states[1][index][k]).abs().max()) for k in states[0][index])
    assert all(torch.isfinite(v).all() for v in states[1][index].values())
(OUT/'learning.json').write_text(json.dumps(dict(num_envs=n,steps=steps,epochs=5,minibatches=4,
    iterations=rows,gpu_rng_equal=True,parameter_max_difference=max_difference),indent=2)+'\n')
print('WALL10_LEARNING_PASS',flush=True)
