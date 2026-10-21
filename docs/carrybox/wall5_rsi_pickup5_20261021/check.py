"""Check new RSI quotas through real full/partial/automatic resets; no training."""
import argparse
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app = AppLauncher(args).app

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import torch
import perceptual_ball.tasks
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from perceptual_ball.tasks.manager_based.perceptual_ball.carrybox_wall5_env_cfg import CarryBoxWalled5EnvCfg, CarryBoxWalled5PPORunnerCfg
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_wall5 as task
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxOnPolicyRunner

DOC = Path(__file__).resolve().parent
ROOT = DOC.parents[2]

def main():
    torch.set_num_threads(2)
    before = json.loads((DOC/'before.json').read_text())
    cfg, agent = CarryBoxWalled5EnvCfg(), CarryBoxWalled5PPORunnerCfg()
    assert cfg.reset_skill_probabilities == (.75, .05, .2)
    assert cfg.reference_init and cfg.held_box_reference_reset and cfg.scene.platform is None
    assert cfg.ground_pickup_reset_frame_range == (0, 32)
    quota = task.fixed_skill_ids(torch.arange(4096), 4096, cfg.reset_skill_probabilities)
    assert torch.bincount(quota, minlength=3).tolist() == [3072, 205, 819]
    ids = torch.tensor([3071, 3072, 3276, 3277, 4095, 15])
    assert torch.equal(task.fixed_skill_ids(ids, 4096, cfg.reset_skill_probabilities), quota[ids])
    cfg.scene.num_envs, cfg.seed, cfg.sim.device = 20, 42, args.device
    for name in ('gpu_found_lost_pairs_capacity', 'gpu_found_lost_aggregate_pairs_capacity', 'gpu_total_aggregate_pairs_capacity'):
        setattr(cfg.sim.physx, name, 262144)
    env = task.Wall5CarryBoxEnv(cfg=cfg)
    try:
        wrapped = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
        records = []
        expected = [0]*15+[1]+[2]*4
        with torch.inference_mode():
            for _ in range(4):
                obs, _ = wrapped.reset()
                state = parent.state(env)
                assert state.skills.tolist() == expected
                assert all(torch.isfinite(v).all() for v in obs.values())
                bottom = parent.base.lift_geometry(env)[0]
                torch.testing.assert_close(bottom[:16], torch.full_like(bottom[:16], .005), atol=2e-5, rtol=0)
                assert (bottom[16:] > .12).all()
                records.append(dict(skills=state.skills.tolist(), box_bottom_m=bottom.tolist()))
            pools = [f.tolist() for f in state.ground_reference_frames if f is not None and len(f)]
            assert pools == [list(range(32))]
            robot, box = env.scene['robot'], env.scene['box']
            untouched = torch.tensor([i for i in range(20) if i != 15], device=env.device)
            root_before = robot.data.root_state_w[untouched].clone()
            box_before = box.data.root_state_w[untouched].clone()
            joint_before = robot.data.joint_pos[untouched].clone()
            env._reset_idx(torch.tensor([15], device=env.device))
            torch.testing.assert_close(robot.data.root_state_w[untouched], root_before)
            torch.testing.assert_close(robot.data.joint_pos[untouched], joint_before)
            torch.testing.assert_close(box.data.root_state_w[untouched], box_before)
            assert state.skills.tolist() == expected
            env.episode_length_buf[15] = env.max_episode_length-1
            obs, reward, done, _ = wrapped.step(torch.zeros(20, 29, device=env.device))
            assert done[15] and state.skills.tolist() == expected
            assert torch.isfinite(reward).all() and all(torch.isfinite(v).all() for v in obs.values())
        contract = env.checkpoint_contract()
        old = torch.load(before['checkpoint'], map_location='cpu', weights_only=False)['environment_contract']
        changed = sorted(k for k in old.keys() | contract.keys() if old.get(k) != contract.get(k))
        assert changed == ['reset_probs', 'reset_skill_probabilities'], changed
        for key in changed:
            assert old[key] == [.8, 0., .2] and contract[key] == [.75, .05, .2]
        probe = SimpleNamespace(device='cpu', environment_contract=lambda: contract)
        try:
            CarryBoxOnPolicyRunner.load(probe, before['checkpoint'])
        except ValueError as exc:
            assert 'environment variant/contract' in str(exc)
        else:
            raise AssertionError('Old reset contract must be rejected')
        for path, digest in before['source_sha256'].items():
            if path not in before['allowed_source_changes']:
                assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
        result = dict(status='PASS', quota_4096=[3072, 205, 819], quota_20=[15, 1, 4],
                      reset_records=records, pickup_frame_pool=pools[0], partial_reset=True,
                      automatic_reset=True, old_contract_rejected=True, contract_changed_keys=changed,
                      contract=contract, training_started=False)
        (DOC/'check.json').write_text(json.dumps(result, indent=2)+'\n')
        print('PICKUP5_CHECK_PASS', flush=True)
    finally:
        env.close()

try:
    main()
finally:
    app.close(wait_for_replicator=False)
