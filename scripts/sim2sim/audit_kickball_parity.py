"""CPU audit against the saved v4 configuration and actual training depth source.

AST loading removes simulator imports only; the numerical function/class bodies
come from the installed IsaacLab and training files, not a rewritten oracle.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
from pathlib import Path
from types import SimpleNamespace as NS

import mujoco
import numpy as np
import torch
import yaml

import kickball_mujoco as s2s

SOURCE = s2s.ROOT/'source/perceptual_ball/perceptual_ball'
PERCEPTION = s2s.ROOT/'docs/agilekickball_v4/return_to_sender_20261012/source_snapshot/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/perception.py'
ISAAC_MATH = Path('/home/cao/IsaacLab/source/isaaclab/isaaclab/utils/math.py')
ENV_YAML = s2s.RUN/'params/env.yaml'
USD = SOURCE/'assets/robots/g1_29dof/g1_29dof.usd'


def training_config():
    # BaseLoader reads tuples/tags as inert strings and lists, never Python objects.
    return yaml.load(ENV_YAML.read_text(),Loader=yaml.BaseLoader)


def load_training_depth():
    class ManagerTermBase:
        def __init__(self, cfg, env):
            pass

    namespace = dict(torch=torch,math=math,ManagerTermBase=ManagerTermBase)
    for source,names in [(ISAAC_MATH,{'quat_conjugate','quat_inv','quat_mul','quat_apply','subtract_frame_transforms'}),
                         (PERCEPTION,{'synthetic_ball_depth_image'})]:
        nodes = [node for node in ast.parse(source.read_text()).body
                 if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names]
        if {node.name for node in nodes} != names:
            raise RuntimeError(f'Missing training functions in {source}')
        for node in nodes:
            node.decorator_list = []
        module = ast.Module(body=ast.parse('from __future__ import annotations').body+nodes,type_ignores=[])
        exec(compile(ast.fix_missing_locations(module),str(source),'exec'),namespace)
    return namespace


def training_depth(torso_positions, torso_quats, ball_positions):
    api = load_training_depth()
    raw = training_config()['observations']['perception']['depth_image']['params']
    params = {k:float(raw[k]) for k in ('near','far','ball_radius','vertical_fov_deg')}
    params.update({k:int(raw[k]) for k in ('width','height')})
    params.update({k:tuple(map(float,raw[k])) for k in ('offset_pos','offset_quat')})
    for k in ('depth_gaussian_std','depth_edge_dropout_prob','depth_hole_dropout_prob'):
        params[k] = float(raw.get(k,0))
    params.update(robot_cfg=NS(name='robot',body_ids=[0]),ball_cfg=NS(name='ball'))
    tensor = lambda x: torch.as_tensor(np.asarray(x),dtype=torch.float32)
    env = NS(device='cpu',num_envs=len(torso_positions),scene={
        'robot':NS(data=NS(body_link_pos_w=tensor(torso_positions)[:,None],
                           body_link_quat_w=tensor(torso_quats)[:,None])),
        'ball':NS(data=NS(root_pos_w=tensor(ball_positions)))})
    term = api['synthetic_ball_depth_image'](NS(params=params),env)
    return term(env,**params).numpy()


def legacy_depth(position, quaternion, ball):
    rotation = s2s.quat_matrix(quaternion)
    cam_pos = position+rotation@s2s.CAM_POS
    return s2s.ball_depth((rotation@s2s.quat_matrix(s2s.CAM_QUAT)).T@(ball-cam_pos))


def samples(count=384):
    rng = np.random.default_rng(20261015)
    positions = np.column_stack((rng.uniform(-.2,.2,(count,2)),rng.uniform(.75,.95,count)))
    quats = np.column_stack((np.ones(count),rng.uniform(-.15,.15,(count,3))))
    quats /= np.linalg.norm(quats,axis=1,keepdims=True)
    balls = np.column_stack((rng.uniform(.35,3.2,count),rng.uniform(-.65,.65,count),np.full(count,.11)))
    # Also exercise no-hit, behind-camera and near/far scenes.
    balls[-16:,0] = -2
    balls[-32:-16,0] = 5
    return positions,quats,balls


def depth_metrics(reference, candidate):
    a, b = reference<3, candidate<3
    shared = a & b
    error = np.abs(reference-candidate)
    return {'frames':len(reference),'pixels':reference.size,'reference_hit_pixels':int(a.sum()),
            'hit_mask_mismatches':int(np.count_nonzero(a != b)),
            'max_shared_hit_error_m':float(error[shared].max()) if shared.any() else 0.,
            'mean_shared_hit_error_m':float(error[shared].mean()) if shared.any() else 0.,
            'max_all_pixel_error_m':float(error.max())}


def usd_torso_pose(root_pos, root_quat, waist_angles):
    """FK from the actual training USD joint frames, including nonzero waist angles."""
    from pxr import Usd,UsdPhysics
    stage = Usd.Stage.Open(str(USD))
    transform = np.eye(4)
    transform[:3,:3],transform[:3,3] = s2s.quat_matrix(root_quat),root_pos

    def local_frame(position, quaternion):
        frame = np.eye(4)
        frame[:3,3] = position
        frame[:3,:3] = s2s.quat_matrix(np.r_[quaternion.GetReal(),quaternion.GetImaginary()])
        return frame

    for name,angle in zip(('waist_yaw_joint','waist_roll_joint','waist_pitch_joint'),waist_angles):
        joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath('/g1_29dof/joints/'+name))
        before = local_frame(joint.GetLocalPos0Attr().Get(),joint.GetLocalRot0Attr().Get())
        after = local_frame(joint.GetLocalPos1Attr().Get(),joint.GetLocalRot1Attr().Get())
        q = np.zeros(4)
        q[0],q['XYZ'.index(joint.GetAxisAttr().Get())+1] = np.cos(angle/2),np.sin(angle/2)
        rotation = np.eye(4)
        rotation[:3,:3] = s2s.quat_matrix(q)
        transform = transform@before@rotation@np.linalg.inv(after)
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q,transform[:3,:3].flatten())
    return transform[:3,3],q


def geometry_audit(sim):
    cases = []
    names = sim.manifest['metadata']['joint_names']
    for angles in ((0,0,0),(.2,.3,-.2),(-.2,-.3,.2)):
        sim.reset()
        for name,value in zip(('waist_yaw_joint','waist_roll_joint','waist_pitch_joint'),angles):
            sim.data.qpos[sim.qadr[names.index(name)]] = value
        mujoco.mj_forward(sim.model,sim.data)
        train_pos,train_q = usd_torso_pose(sim.data.qpos[:3],sim.data.qpos[3:7],angles)
        mj_pos,mj_q = sim.data.xpos[sim.torso],sim.data.xquat[sim.torso]
        balls = np.array([[x,y,.11] for x in (.5,1,1.5,2,2.5) for y in (-.2,0,.2)])
        reference = training_depth(np.tile(train_pos,(len(balls),1)),np.tile(train_q,(len(balls),1)),balls)
        candidate = training_depth(np.tile(mj_pos,(len(balls),1)),np.tile(mj_q,(len(balls),1)),balls)
        train_cam = train_pos+s2s.quat_matrix(train_q)@s2s.CAM_POS
        mj_cam = mj_pos+s2s.quat_matrix(mj_q)@s2s.CAM_POS
        cases.append(dict(waist_yaw_roll_pitch_rad=angles,
                          camera_position_difference_m=(mj_cam-train_cam).tolist(),
                          camera_distance_m=float(np.linalg.norm(mj_cam-train_cam)),
                          depth=depth_metrics(reference,candidate)))
    sim.reset()
    return cases


def physical_audit(sim):
    from pxr import Usd,UsdGeom,UsdPhysics
    cfg = training_config()
    ball = cfg['scene']['ball']['spawn']
    m,d = sim.model,sim.data
    stage = Usd.Stage.Open(str(USD))
    mass = sum(float(UsdPhysics.MassAPI(p).GetMassAttr().Get() or 0)
               for p in stage.Traverse() if p.HasAPI(UsdPhysics.MassAPI))
    torso = stage.GetPrimAtPath('/g1_29dof/torso_link')
    training_torso = np.asarray(UsdGeom.Xformable(torso).ComputeLocalToWorldTransform(0).ExtractTranslation())
    mujoco_torso = d.xpos[sim.torso]-d.qpos[:3]
    train_material = ball['physics_material']
    floor_material = cfg['scene']['ground']['spawn']['physics_material']
    # Read the actual combined contact parameters in a tiny overlapping contact.
    d.qpos[sim.bq+2] = .109
    mujoco.mj_forward(m,d)
    contact = next(c for c in d.contact if {c.geom1,c.geom2} == {sim.ball_geom,sim.floor_geom})
    contact_values = dict(friction=contact.friction.tolist(),solref=contact.solref.tolist(),dim=contact.dim)
    sim.reset()
    return {
        'ball_mass_kg':{'training':float(ball['mass_props']['mass']),'mujoco':float(m.body_mass[sim.ball_body])},
        'ball_radius_m':{'training':float(ball['radius']),'mujoco':float(m.geom_size[sim.ball_geom,0])},
        'ball_inertia_kg_m2':m.body_inertia[sim.ball_body].tolist(),
        'ball_damping':{'training_linear_rate':float(ball['rigid_props']['linear_damping']),
                        'training_angular_rate':float(ball['rigid_props']['angular_damping']),
                        'mujoco_dof_damping':m.dof_damping[sim.bv:sim.bv+6].tolist(),
                        'note':'PhysX damping rates and MuJoCo force coefficients have different units'},
        'training_ball_material':{k:train_material[k] for k in ('static_friction','dynamic_friction','restitution','friction_combine_mode','restitution_combine_mode')},
        'training_floor_material':{k:floor_material[k] for k in ('static_friction','dynamic_friction','restitution')},
        'mujoco_ball_floor_contact':contact_values,
        'robot_mass_kg':{'training_usd':mass,'mujoco':float(m.body_mass.sum()-m.body_mass[sim.ball_body])},
        'torso_zero_waist_relative_to_root_m':{'training_usd':training_torso.tolist(),
            'mujoco':mujoco_torso.tolist(),'difference':(mujoco_torso-training_torso).tolist()},
        'policy_dt_s':{'training':float(cfg['sim']['dt'])*int(cfg['decimation']),'mujoco':sim.control_dt},
        'physics_dt_s':{'training':float(cfg['sim']['dt']),'mujoco':m.opt.timestep},
    }


def rollout(depth_function, duration=10):
    """Paired CPU diagnostic; everything except the depth arithmetic is held fixed."""
    sim = s2s.KickballSim(physics_dt=.005)
    heights, contacts, falls, visible, resets, displacement = [],0,0,0,0,0.
    for _ in range(round(duration/sim.control_dt)):
        flat,_ = sim.observe()
        frame = depth_function(sim.data.xpos[sim.torso],sim.data.xquat[sim.torso],sim.data.xpos[sim.ball_body])
        sim.history.depth[-1] = frame
        # On the initial frame, simulate the same repeat-first reset history.
        if not heights or sim.history.terms is not history_terms:
            sim.history.depth[:] = frame
        history_terms = sim.history.terms
        depth = sim.history.depth[None].copy()
        visible += int(np.any(frame<3))
        with torch.inference_mode():
            action = sim.policy(torch.from_numpy(flat),torch.from_numpy(depth)).numpy()[0]
        target = sim.target(action)
        touched = False
        for _ in range(sim.substeps):
            sim.data.ctrl[sim.actuators] = sim.torque(target)[0]
            mujoco.mj_step(sim.model,sim.data)
            if not np.isfinite(sim.data.qpos).all() or any(w.number for w in sim.data.warning):
                raise RuntimeError('Nonfinite state or MuJoCo warning in parity rollout')
            heights.append(float(sim.data.qpos[2]))
            touched |= any(sim.ball_geom in (c.geom1,c.geom2) and sim.floor_geom not in (c.geom1,c.geom2)
                           for c in sim.data.contact)
        mujoco.mj_forward(sim.model,sim.data)
        contacts += touched
        displacement = max(displacement,float(np.linalg.norm(sim.data.qpos[:2])))
        if sim.data.qpos[2]<.4:
            falls += 1
            sim.reset()
        elif sim.advance_round() == 'recovery_timeout':
            resets += 1
    return dict(duration_s=duration,steps=len(heights)//sim.substeps,falls=falls,
                recovery_timeouts=resets,ball_robot_contact_steps=contacts,visible_steps=visible,
                min_root_height_m=min(heights),max_root_displacement_m=displacement)


def audit(output):
    sim = s2s.KickballSim(physics_dt=.005)
    positions,quats,balls = samples()
    reference = training_depth(positions,quats,balls)
    legacy = np.stack([legacy_depth(*sample) for sample in zip(positions,quats,balls)])
    current = np.stack([s2s.policy_depth(*sample) for sample in zip(positions,quats,balls)])
    result = dict(physics=physical_audit(sim),geometry=geometry_audit(sim),
        depth_legacy=depth_metrics(reference,legacy),depth_current=depth_metrics(reference,current),
        camera_offset_quaternion_norm_squared=float(s2s.CAM_QUAT@s2s.CAM_QUAT),
        source_sha256={str(p):s2s.sha256(p) for p in (PERCEPTION,ISAAC_MATH,ENV_YAML,USD,s2s.ROBOT_XML,s2s.RUN/'exported/policy.pt')},
        limitations=['CPU replay uses identical poses, not simultaneous PhysX/MuJoCo dynamics',
                     'Contact coefficients are not calibrated across engines; no task success-rate claim'],
        rollout_legacy=rollout(legacy_depth),rollout_current=rollout(s2s.policy_depth))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    assert result['depth_current']['hit_mask_mismatches'] == 0
    assert result['depth_current']['max_shared_hit_error_m'] < 1.e-4


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    audit(parser.parse_args().output)
