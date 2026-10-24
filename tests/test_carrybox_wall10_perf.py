"""Compare optimized wall10 against the frozen production implementation."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import torch
import warp as wp
import test_carrybox_wall10 as fixtures
from perceptual_ball.rsl_rl_extensions import carrybox_wall10 as learning
from isaaclab.utils.math import quat_apply, quat_apply_inverse

ROOT = Path(__file__).resolve().parents[1]
PKG = Path('source/perceptual_ball/perceptual_ball')
BEFORE = ROOT / 'docs/carrybox/wall10_perf_20261023/before_source'
MDP = PKG / 'tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py'


def function(path, name, scope, cls=None, remove_first=False):
    tree = ast.parse(path.read_text())
    nodes = tree.body if cls is None else next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls).body
    node = copy.deepcopy(next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name))
    if remove_first:
        node.body.pop(0)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
    return scope[name]


old_update = function(BEFORE / PKG / 'rsl_rl_extensions/carrybox_wall10.py', 'update', dict(vars(learning)), 'CarryBoxWall10PPO')


def populate(steps=194):
    alg, obs = fixtures.algorithm(steps)
    alg._ensure_motion_library()
    with torch.inference_mode():
        for i in range(steps):
            alg.act(obs)
            following = obs.clone()
            following['perception'] = torch.rand_like(following['perception'])
            following['proprio'] = torch.randn_like(following['proprio']) * .05
            following['critic_state'] = torch.randn_like(following['critic_state']) * .05
            alg.process_env_step(following, torch.ones(4), torch.zeros(4, dtype=torch.bool), {})
            obs = following
        alg.compute_returns(obs)
    # Exercise done smoothing without altering the precomputed return target.
    alg.storage.dones[::3, 1] = True
    return alg


class Wall10PerfTests(unittest.TestCase):
    def test_logical_draws_experts_and_rng_unchanged(self):
        alg, _ = fixtures.algorithm()
        alg._ensure_motion_library()
        torch.manual_seed(711)
        weights, experts = [], []
        for n in (256, 256, 19):
            torch.distributions.Normal(torch.full((n,29), .7), torch.full((n,29), .3)).sample()
            weights.append(2 * torch.rand(n, 1) - 1)
            experts.append(alg.motion_library.sample_expert_amp_obs(n))
        rng = torch.get_rng_state()
        torch.manual_seed(711)
        w, e = alg._sample_update_inputs(531)
        self.assertTrue(torch.equal(rng, torch.get_rng_state()))
        torch.testing.assert_close(w, torch.cat(weights), rtol=0, atol=0)
        torch.testing.assert_close(e, torch.cat(experts), rtol=0, atol=0)

    def test_full_update_loss_gradients_adam_kl_and_rng(self):
        torch.manual_seed(42)
        old = populate()
        # Copy tensors detached from distributions left by rollout collection.
        old.policy.distribution = None
        new = copy.deepcopy(old)
        new.cnn_execution_batch_size = 512
        results = []
        for alg, update in ((old, old_update), (new, learning.CarryBoxWall10PPO.update)):
            torch.manual_seed(91)
            loss = update(alg)
            results.append((loss, torch.get_rng_state()))
        self.assertTrue(torch.equal(results[0][1], results[1][1]))
        self.assertEqual(old.learning_rate, new.learning_rate)
        for key in results[0][0]:
            torch.testing.assert_close(torch.tensor(results[0][0][key]), torch.tensor(results[1][0][key]), rtol=3e-5, atol=2e-5)
        for a, b in zip(list(old.policy.parameters()) + list(old.amp.parameters()),
                        list(new.policy.parameters()) + list(new.amp.parameters())):
            torch.testing.assert_close(a, b, rtol=3e-5, atol=2e-6)
            if a.grad is not None:
                torch.testing.assert_close(a.grad, b.grad, rtol=3e-4, atol=3e-5)
            if a in old.optimizer.state:
                for key in old.optimizer.state[a]:
                    torch.testing.assert_close(old.optimizer.state[a][key], new.optimizer.state[b][key], rtol=3e-4, atol=3e-5)
        self.assertEqual(old.amp_config['cnn_microbatch'], 256)
        self.assertEqual(new.amp_config, old.amp_config)

    def test_nonfinite_loss_stops_before_optimizer(self):
        alg = populate(4)
        before = copy.deepcopy(alg.policy.state_dict())
        alg.storage.returns.fill_(torch.nan)
        with self.assertRaises(FloatingPointError):
            alg.update()
        self.assertFalse(alg.optimizer.state)
        for key, value in before.items():
            torch.testing.assert_close(alg.policy.state_dict()[key], value, rtol=0, atol=0)

    def test_warp_box_matches_original_torch_and_partial_rows(self):
        wp.init()
        kernel = function(ROOT / MDP, 'variable_box_depth', {'wp': wp, '__name__': __name__})
        reference = function(BEFORE / MDP, '_update_buffers_impl',
                             {'torch': torch, 'quat_apply': quat_apply, 'quat_apply_inverse': quat_apply_inverse},
                             'Wall10DepthCamera', remove_first=True)
        torch.manual_seed(4)
        n, pixels = 64, 127
        camera = torch.randn(n, 3) * .2
        quat = torch.randn(n, 4); quat /= quat.norm(dim=-1, keepdim=True)
        box = torch.cat((torch.randn(n, 3) * .5, torch.randn(n, 4)), -1)
        box[:, 3:] /= box[:, 3:].norm(dim=-1, keepdim=True)
        rays = torch.randn(pixels, 3); rays[:, 0].abs_().add_(.2); rays /= rays.norm(dim=-1, keepdim=True)
        sizes = torch.rand(n, 3) * .5 + .1
        # Parallel, inside, before near, beyond far, and an occluder nearer than box.
        rays[0] = torch.tensor([1., 0., 0.])
        camera[:6] = 0.; quat[:6] = torch.tensor([1.,0.,0.,0.])
        box[:6, 3:] = torch.tensor([0.,0.,0.,1.]); box[:6, :3] = 0.
        box[1, 0] = .02; box[2, 0] = 4.; box[3, 1] = 2.; box[4:6,0] = 1.
        sizes[:6] = .3
        depth = torch.full((n,pixels), 3.); depth[5] = .2
        ids = torch.tensor(list(range(6)) + list(range(7,n,2)), dtype=torch.int32)
        scene = NS(_box_view=NS(get_transforms=lambda: box), _data=NS(pos_w=camera, quat_w_world=quat),
                   _rays=rays, box_sizes=sizes, cfg=NS(near=.1, far=3.), _depth=depth.clone())
        reference(scene, ids.long())
        actual = depth.clone()
        wp.launch(kernel, dim=(len(ids),pixels), inputs=[wp.from_torch(ids), wp.from_torch(camera,dtype=wp.vec3),
            wp.from_torch(quat), wp.from_torch(rays,dtype=wp.vec3), wp.from_torch(box,dtype=wp.transform),
            wp.from_torch(sizes,dtype=wp.vec3), .1, 3., wp.from_torch(actual)], device='cpu')
        torch.testing.assert_close(actual, scene._depth, atol=2e-6, rtol=2e-5)
        self.assertTrue(torch.equal(actual[6::2], depth[6::2]))

    def test_force_pulse_clears_on_next_physics_step(self):
        apply = function(ROOT / MDP, 'apply_actions', {'torch': torch}, 'Wall10JointPositionAction')
        previous = function(BEFORE / MDP, 'apply_actions', {'torch': torch}, 'Wall10JointPositionAction')
        def run(method):
            observed, writes = [], []
            active = torch.zeros(2,1,3)
            def set_force(f, torque, **kw):
                active.copy_(f); writes.append(f.clone())
            env = NS(_wall10_zero_force=torch.zeros_like(active), _wall10_torso=[0])
            action = NS(_env=env, _asset=NS(set_joint_position_target=lambda *a, **k: None,
                set_external_force_and_torque=set_force), delay=NS(advance=lambda x:x),
                _processed_actions=torch.zeros(2,29), _joint_ids=list(range(29)), _force_active=False)
            for policy_step in range(18):
                pulse = policy_step > 0 and policy_step % 8 == 0
                env._wall10_force_pending = pulse
                env._wall10_force = torch.full_like(active, 5.) if pulse else env._wall10_zero_force
                for substep in range(4):
                    method(action); observed.append(active.clone())
            return torch.stack(observed), len(writes)
        a, before_writes = run(previous); b, after_writes = run(apply)
        torch.testing.assert_close(a,b,rtol=0,atol=0)
        self.assertEqual((before_writes,after_writes),(72,4))


if __name__ == '__main__':
    unittest.main()
