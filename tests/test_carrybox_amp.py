"""FindBox real-data, timing, non-privileged AMP and full training/checkpoint contracts."""
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import torch
import test_carrybox as base
from perceptual_ball.carrybox_amp import (FindBoxMotionLibrary, SOURCE_JOINT_NAMES,
    DEFAULT_DATASET_PATH, resolve_dataset_path, joint_mapping, pack_frame)
from perceptual_ball.rsl_rl_extensions.carrybox import CarryBoxPPO, CarryBoxOnPolicyRunner
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox import amp_frame

ROOT = Path(__file__).resolve().parents[1]


def synthetic_dataset(root):
    n = 60
    t = torch.arange(n) / 60.
    # Rotation about local x at 1 rad/s; deliberately alternate quaternion signs.
    q = torch.stack((torch.sin(t / 2), torch.zeros(n), torch.zeros(n), torch.cos(t / 2)), -1)
    q[::2] *= -1
    data = dict(joint_position=t[:, None].expand(n, 29).clone(), base_quat=q)
    manifest = json.loads((ROOT / 'findbox/amp_manifest.json').read_text())
    manifest['clips'] = []
    for group in manifest['groups']:
        p = root / group / 'sample.pt'; p.parent.mkdir(parents=True, exist_ok=True)
        torch.save(data, p)
        manifest['clips'].append(dict(file=f'{group}/sample.pt', frames=n,
            sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (root / 'amp_manifest.json').write_text(json.dumps(manifest))


def amp_algorithm(steps=12):
    obs = base.observations()
    obs['amp'] = torch.zeros(4, 640)
    alg = CarryBoxPPO(base.policy(obs), device='cpu', schedule='fixed', num_learning_epochs=1,
                      num_mini_batches=1, amp_coef=.25)
    alg.init_storage('rl', 4, steps, obs, [29])
    return alg, obs


class FindBoxTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)

    def test_real_data_mapping_weights_and_boundaries(self):
        library = FindBoxMotionLibrary()
        self.assertEqual(library.num_clips, 15)
        self.assertEqual({group: library.clip_groups.count(group) for group in set(library.clip_groups)},
                         {'loco_direction': 11, 'pickUp': 3, 'carryWith': 1})
        self.assertEqual(library.fps, 60.)
        sample, ids = library.sample_expert_amp_obs(300, return_clip_ids=True)
        self.assertEqual(sample.shape, (300, 640))
        self.assertTrue(torch.isfinite(sample).all())
        for group, weight in [('loco_direction', .4), ('pickUp', .4), ('carryWith', .2)]:
            mass = sum(float(library.weights[i]) for i, value in enumerate(library.clip_groups) if value == group)
            self.assertAlmostEqual(mass, weight, places=6)
        robot_names = list(reversed(SOURCE_JOINT_NAMES))
        ids = joint_mapping(robot_names)
        self.assertEqual([robot_names[i] for i in ids], list(SOURCE_JOINT_NAMES))
        with self.assertRaises(ValueError): joint_mapping(robot_names[:-1] + [robot_names[0]])
        with self.assertRaisesRegex(ValueError, 'boundary'):
            library.windows(torch.tensor([0]), torch.tensor([float(library.lengths[0] - 1)]))
        # Last legal start remains inside the selected clip, even at a fractional 60/50 rate.
        starts = library.lengths.float() - 1 - 9 * 60 / 50
        self.assertTrue(torch.isfinite(library.windows(torch.arange(library.num_clips), starts)).all())

    def test_carrywith1_hold_revision_and_original_snapshot(self):
        record_dir = ROOT / 'docs/carrybox/amp_hold_20261014'
        original = record_dir / 'original_dataset'
        recipe = json.loads((record_dir / 'edit_record.json').read_text())
        old_library = FindBoxMotionLibrary(original)
        library = FindBoxMotionLibrary(ROOT / 'findbox')  # Preserve the revision-2 content audit.
        self.assertEqual(old_library.num_clips, 17)
        self.assertEqual(old_library.metadata['manifest_sha256'], recipe['previous_manifest_sha256'])
        self.assertEqual(library.metadata['manifest_sha256'], recipe['new_manifest_sha256'])
        self.assertNotEqual(old_library.metadata, library.metadata)
        self.assertEqual(library.metadata['total_frames'], 4155)
        self.assertEqual(library.clip_names.count('carryWith/carrywith1.pt'), 1)
        for name in recipe['excluded_clips']:
            self.assertNotIn(name, library.clip_names)
            self.assertFalse((ROOT / 'findbox' / name).exists())
            self.assertEqual(hashlib.sha256((record_dir/'excluded_from_active'/name).read_bytes()).hexdigest(),
                             hashlib.sha256((original/name).read_bytes()).hexdigest())
        for name in library.clip_names:
            if name != 'carryWith/carrywith1.pt':
                self.assertEqual((ROOT/'findbox'/name).read_bytes(), (original/name).read_bytes())
        source = torch.load(original/'carryWith/carrywith1.pt', weights_only=True)
        data = torch.load(ROOT/'findbox/carryWith/carrywith1.pt', weights_only=True)
        self.assertEqual(set(source), set(data))
        indices = torch.tensor(recipe['source_frame_indices'])
        self.assertEqual(indices.tolist(), list(range(21)) + [20]*279)
        for name in source:
            expected = source[name][indices].clone()
            if name in recipe['zeroed_velocity_fields']:
                expected[20:] = 0
            torch.testing.assert_close(data[name], expected, atol=0, rtol=0)
            self.assertTrue(torch.isfinite(data[name]).all())
        for positions, velocities in [('base_position', 'base_linear_velocity'),
                                      ('joint_position', 'joint_velocity')]:
            torch.testing.assert_close(torch.diff(data[positions], dim=0)*60, data[velocities][:-1],
                                       atol=1.e-5, rtol=1.e-5)
        slot = library.clip_names.index('carryWith/carrywith1.pt')
        joints, velocity, quaternion, angular = library.clips[slot]
        self.assertEqual(torch.count_nonzero(velocity[20:]).item(), 0)
        torch.testing.assert_close(angular[20:], torch.zeros_like(angular[20:]), atol=1.e-5, rtol=0)
        window = library.windows(torch.tensor([slot]), torch.tensor([20.])).reshape(10,64)
        torch.testing.assert_close(window[:,29:58], torch.zeros(10,29), atol=0, rtol=0)
        torch.testing.assert_close(window[:,61:], torch.zeros(10,3), atol=1.e-5, rtol=0)

    def test_named_asset_migration_defaults_and_exact_motion_equivalence(self):
        record = json.loads((ROOT/'docs/carrybox/amp_layout_20261014/migration.json').read_text())
        canonical = ROOT / record['new_dataset']
        previous = FindBoxMotionLibrary('findbox')
        current = FindBoxMotionLibrary()
        self.assertEqual(Path(DEFAULT_DATASET_PATH), canonical)
        self.assertEqual(current.root, canonical)
        self.assertTrue((canonical.parent/'kick/kick_left.pt').is_file())
        self.assertEqual(current.metadata['manifest_sha256'], record['new_manifest_sha256'])
        self.assertEqual(previous.metadata['manifest_sha256'], record['previous_manifest_sha256'])
        self.assertEqual(current.clip_groups, previous.clip_groups)
        torch.testing.assert_close(current.weights, previous.weights, atol=0, rtol=0)
        self.assertEqual(current.clip_names, [record['mapping'][name] for name in previous.clip_names])
        for old, new in record['mapping'].items():
            self.assertRegex(new, r'^(locomotion|pick_up|hold)/[a-z][a-z0-9_]*\.pt$')
            self.assertEqual((ROOT/'findbox'/old).read_bytes(), (canonical/new).read_bytes())
        for path, digest in record['protected_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest)
        starts = torch.zeros(current.num_clips)
        ids = torch.arange(current.num_clips)
        torch.testing.assert_close(current.windows(ids, starts), previous.windows(ids, starts), atol=0, rtol=0)
        starts = current.lengths.float()-1-9*60/50
        torch.testing.assert_close(current.windows(ids, starts), previous.windows(ids, starts), atol=0, rtol=0)
        original_cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                self.assertEqual(resolve_dataset_path(), canonical)
                self.assertEqual(FindBoxMotionLibrary().metadata, current.metadata)
                self.assertEqual(FindBoxMotionLibrary('findbox').metadata, previous.metadata)
        finally:
            os.chdir(original_cwd)
        alg, _ = amp_algorithm()
        self.assertEqual(Path(alg.amp_data_dir), canonical)
        alg.motion_metadata = previous.metadata
        with self.assertRaisesRegex(ValueError, 'dataset/schema'):
            alg._ensure_motion_library()

    def test_mismatched_named_group_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            manifest = json.loads((Path(DEFAULT_DATASET_PATH)/'amp_manifest.json').read_text())
            manifest['clips'][0]['group'] = 'pickUp'  # hold directory cannot become a pickup skill.
            (path/'amp_manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'group/directory'):
                FindBoxMotionLibrary(path)

    def test_known_motion_gravity_sign_quaternion_and_live_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); synthetic_dataset(root)
            library = FindBoxMotionLibrary(root)
            window = library.windows(torch.tensor([0]), torch.tensor([0.])).reshape(10, 64)
            t = torch.arange(10) / 50.
            torch.testing.assert_close(window[:, :29], t[:, None].expand(-1, 29), atol=1.e-6, rtol=1.e-6)
            torch.testing.assert_close(window[:, 29:58], torch.ones(10, 29), atol=1.e-5, rtol=1.e-5)
            gravity = torch.stack((t * 0, -t.sin(), -t.cos()), -1)
            angular = torch.tensor([1., 0., 0.]).expand(10, -1)
            torch.testing.assert_close(window[:, 58:61], gravity, atol=2.e-6, rtol=1.e-5)
            torch.testing.assert_close(window[:, 61:], angular, atol=1.e-5, rtol=1.e-5)
            # Live joint order is deliberately reversed and values differ across joints.
            source_pos = torch.arange(29.)[None]
            source_vel = source_pos * 2
            data = NS(joint_pos=source_pos.flip(-1), joint_vel=source_vel.flip(-1),
                      projected_gravity_b=gravity[:1], root_ang_vel_b=angular[:1])
            env = NS(scene={'robot': NS(joint_names=list(reversed(SOURCE_JOINT_NAMES)), data=data)})
            torch.testing.assert_close(amp_frame(env), pack_frame(source_pos, source_vel, gravity[:1], angular[:1]))
            manifest = json.loads((root / 'amp_manifest.json').read_text()); manifest['fps'] = 30
            (root / 'amp_manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'schema'): FindBoxMotionLibrary(root)

    def test_bad_clip_hash_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); synthetic_dataset(root)
            path = root / 'pickUp/sample.pt'
            data = torch.load(path, weights_only=True); data['joint_position'][0, 0] = torch.nan
            torch.save(data, path)
            with self.assertRaisesRegex(ValueError, 'hash mismatch'): FindBoxMotionLibrary(root)
            manifest = json.loads((root / 'amp_manifest.json').read_text())
            for clip in manifest['clips']:
                if clip['file'] == 'pickUp/sample.pt': clip['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            (root / 'amp_manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'joint_position'): FindBoxMotionLibrary(root)

    def test_terminal_reward_training_buffer_and_cold_start(self):
        alg, obs = amp_algorithm(steps=12)
        original_actor = alg.policy.act_inference(obs).detach()
        altered = obs.clone(); altered['amp'][:] = 1.e4
        torch.testing.assert_close(alg.policy.act_inference(altered), original_actor, rtol=0, atol=0)
        torch.testing.assert_close(alg.policy.evaluate(altered), alg.policy.evaluate(obs), rtol=0, atol=0)
        amp_before = copy.deepcopy(alg.amp.state_dict())
        with torch.inference_mode():
            for step in range(12):
                alg.act(obs)
                next_obs = obs.clone(); next_obs['amp'][:] = .1 * step
                done = torch.zeros(4, dtype=torch.bool)
                extra = {}
                if step == 9:
                    done[0] = True
                    next_obs['amp'][0] = -9.  # would be the wrong post-reset reward/training state
                    extra['terminal_observations'] = {'env_ids': torch.tensor([0]), 'obs': {'amp': torch.full((1, 640), .9)}}
                alg.process_env_step(next_obs, torch.ones(4), done, extra)
                if step < 8:
                    torch.testing.assert_close(alg.storage.rewards[step], torch.ones(4, 1))
                    self.assertFalse(alg.amp_valid[step].any())
                if step == 9:
                    torch.testing.assert_close(alg.amp_rollout[step, 0], torch.full((640,), .9))
                    style = alg.amp.predict_reward(torch.full((1, 640), .9)).item()
                    self.assertAlmostEqual(float(alg.storage.rewards[step, 0]), .75 + .25 * .02 * 2 * style, places=6)
                if step > 9: self.assertFalse(alg.amp_valid[step, 0])
                obs = next_obs
            alg.compute_returns(obs)
        loss = alg.update()
        self.assertEqual(loss['amp_valid_samples'], 14.)
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in loss.values()))
        self.assertFalse(torch.equal(alg.amp.amp_linear.weight, amp_before['amp_linear.weight']))
        self.assertTrue(alg.amp_optimizer.state)
        runner = CarryBoxOnPolicyRunner.__new__(CarryBoxOnPolicyRunner)
        runner.alg = alg; runner.device = 'cpu'; runner.current_learning_iteration = 1
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'model.pt'); runner.save(path)
            saved = torch.load(path, weights_only=False)
            original_disc = copy.deepcopy(alg.amp.state_dict())
            with torch.no_grad(): alg.amp.amp_linear.weight.add_(10.)
            # Both resume and inference construction/load can succeed without reading files.
            alg.amp_data_dir = '/missing/dataset'
            with patch.object(sys.modules['perceptual_ball.rsl_rl_extensions.carrybox'], 'FindBoxMotionLibrary',
                              side_effect=AssertionError('dataset touched')):
                runner.load(path)
                runner.load(path, load_optimizer=False)
                with torch.inference_mode():
                    torch.testing.assert_close(alg.policy.act_inference(obs), alg.policy.act_inference({'proprio': obs['proprio'], 'perception': obs['perception']}))
            for key, value in alg.amp.state_dict().items(): torch.testing.assert_close(value, original_disc[key])
            current_opt = alg.amp_optimizer.state_dict()
            for key, value in saved['amp']['optimizer']['state'].items():
                for name, tensor in value.items(): torch.testing.assert_close(current_opt['state'][key][name], tensor)
            self.assertIsNone(alg.motion_library)
            self.assertEqual(alg.amp_age.sum().item(), 0)
            alg.amp_data_dir = DEFAULT_DATASET_PATH
            alg.motion_metadata = dict(alg.motion_metadata, manifest_sha256='changed')
            with self.assertRaisesRegex(ValueError, 'dataset/schema'):
                alg._ensure_motion_library()
            del saved['amp']['model']; torch.save(saved, path)
            with self.assertRaisesRegex(ValueError, 'AMP state'): runner.load(path)


if __name__ == '__main__': unittest.main()
