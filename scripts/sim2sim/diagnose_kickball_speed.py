"""Bounded CPU diagnostics for fast-ball falls; never changes production config."""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
import torch

import kickball_mujoco as s2s


def snapshot(sim):
    d = sim.data
    vertical = d.xmat[sim.pelvis].reshape(3,3)[2,2]
    return dict(time_s=float(d.time),height_m=float(d.qpos[2]),
                tilt_deg=float(np.degrees(np.arccos(np.clip(vertical,-1,1)))),
                root_xy=d.qpos[:2].tolist(),root_velocity=d.qvel[:6].tolist(),
                ball_position=d.xpos[sim.ball_body].tolist(),
                ball_speed_m_s=float(np.linalg.norm(d.qvel[sim.bv:sim.bv+2])),
                joint_velocity_rms=float(np.sqrt(np.mean(d.qvel[sim.vadr]**2))))


def diagnose(speed, directory, mode='policy', duration=20., replay=None):
    sim = s2s.KickballSim(physics_dt=.005,speed=speed,depth_mode='analytic')
    m,d = sim.model,sim.data
    if mode == 'training_hip_roll_limit':
        # Diagnostic only: restore the measured training USD capacity in this process.
        # This is not a deployment recommendation or an edit to the official asset.
        names = sim.manifest['metadata']['joint_names']
        for name in ('left_hip_roll_joint','right_hip_roll_joint'):
            k = names.index(name)
            sim.limits[k] = [-139.,139.]
            m.actuator_ctrlrange[sim.actuators[k]] = sim.limits[k]
            m.jnt_actfrcrange[sim.joints[k]] = sim.limits[k]
    if mode in ('ghost','replay_ghost'):
        # Preserve ball-floor and robot-floor contacts; remove only ball-robot.
        m.geom_contype[sim.ball_geom] = 4
        m.geom_conaffinity[sim.ball_geom] = 2
        def can_collide(a,b):
            return bool((m.geom_contype[a]&m.geom_conaffinity[b]) or (m.geom_contype[b]&m.geom_conaffinity[a]))
        assert can_collide(sim.ball_geom,sim.floor_geom)
        robot_geoms = [g for g in range(m.ngeom) if m.geom_bodyid[g] not in (0,sim.ball_body)
                       and (m.geom_contype[g] or m.geom_conaffinity[g])]
        assert all(not can_collide(g,sim.ball_geom) and can_collide(g,sim.floor_geom) for g in robot_geoms)
    events = [dict(event='initial_serve',round=0,**snapshot(sim))]
    rows, targets, actions, saturations, requested, support, observations = [],[],[],[],[],[],[]
    first_contact = first_fall = first_tilt = first_20 = None
    total_impulse = 0.
    round_index = 0
    had_contact = False
    tilted_round = False
    joint_names = sim.manifest['metadata']['joint_names']
    max_steps = min(round(duration/sim.control_dt),len(replay) if replay is not None else 10**9)
    for i in range(max_steps):
        flat,depth = sim.observe()
        with torch.inference_mode():
            action = sim.policy(torch.from_numpy(flat),torch.from_numpy(depth)).numpy()[0]
        if mode == 'hold':
            action = np.zeros(29,dtype=np.float32)
        elif replay is not None:
            action = replay[i].copy()
        target = sim.target(action)
        actions.append(action.copy())
        targets.append(target.copy())
        observations.append([int(np.count_nonzero(depth[0,-1]<3)),float(np.max(np.abs(action)))])
        saturated = np.zeros(29)
        max_requested = np.zeros(29)
        foot_contact = np.zeros(2,dtype=bool)
        contact = False
        impulse = 0.
        contact_bodies = set()
        incoming_speed = None
        foot_points = []
        for _ in range(sim.substeps):
            raw = sim.kp*(target-d.qpos[sim.qadr])-sim.kd*d.qvel[sim.vadr]
            saturated += (raw<sim.limits[:,0]) | (raw>sim.limits[:,1])
            max_requested = np.maximum(max_requested,np.abs(raw))
            d.ctrl[sim.actuators] = sim.torque(target)[0]
            previous_ball_speed = float(np.linalg.norm(d.qvel[sim.bv:sim.bv+2]))
            mujoco.mj_step(m,d)
            if not np.isfinite(d.qpos).all() or not np.isfinite(d.qvel).all() or any(w.number for w in d.warning):
                raise RuntimeError('Invalid simulator state; stopping diagnostic')
            for ci,c in enumerate(d.contact):
                if sim.ball_geom in (c.geom1,c.geom2) and sim.floor_geom not in (c.geom1,c.geom2):
                    force = np.zeros(6)
                    mujoco.mj_contactForce(m,d,ci,force)
                    if np.linalg.norm(force[:3])<1.e-6:
                        continue
                    if not contact:
                        incoming_speed = previous_ball_speed
                    contact = True
                    other = c.geom2 if c.geom1==sim.ball_geom else c.geom1
                    contact_bodies.add(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[other])))
                    impulse += np.linalg.norm(force[:3])*m.opt.timestep
                if sim.floor_geom in (c.geom1,c.geom2):
                    other = c.geom2 if c.geom1 == sim.floor_geom else c.geom1
                    body = m.geom_bodyid[other]
                    if body in sim.feet:
                        force = np.zeros(6)
                        mujoco.mj_contactForce(m,d,ci,force)
                        if force[0]>1:
                            foot_contact[sim.feet.index(body)] = True
                            foot_points.append(c.pos[:2].copy())
        mujoco.mj_forward(m,d)
        mujoco.mj_subtreeVel(m,d)
        state = snapshot(sim)
        total_impulse += impulse
        sat_fraction = saturated/sim.substeps
        com = d.subtree_com[sim.pelvis]
        # Conservative XY bounding rectangle of loaded foot contact points in this step.
        margin = np.nan
        if foot_points:
            points = np.asarray(foot_points)
            margin = min(np.min(com[:2]-points.min(0)),np.min(points.max(0)-com[:2]))
        rows.append([d.time,state['height_m'],state['tilt_deg'],*d.qpos[:2],
                     state['ball_speed_m_s'],int(contact),impulse,round_index,*d.qvel[:6],
                     *com,*d.subtree_linvel[sim.pelvis],margin])
        saturations.append(sat_fraction)
        requested.append(max_requested)
        support.append(foot_contact)
        if contact and not had_contact:
            event = dict(event='contact_start',round=round_index,incoming_speed_m_s=incoming_speed,
                         contact_bodies=sorted(contact_bodies),control_step_impulse_Ns=float(impulse),**state)
            events.append(event)
            if first_contact is None: first_contact=event
        had_contact = contact
        if state['tilt_deg']>20 and first_20 is None:
            first_20 = dict(event='tilt_above_20deg',round=round_index,**state)
            events.append(first_20)
        if state['tilt_deg']>35 and not tilted_round:
            event = dict(event='tilt_above_35deg',round=round_index,**state)
            events.append(event)
            if first_tilt is None: first_tilt=event
            tilted_round=True
        if state['height_m']<.4:
            first_fall = dict(event='fall',round=round_index,**state)
            events.append(first_fall)
            break
        # Match normal automatic serving. Replay controls only the target sequence.
        event = sim.advance_round()
        if event is not None:
            round_index += 1
            events.append(dict(event=event,round=round_index,**snapshot(sim)))
            tilted_round=False
            had_contact=False
    traces = np.asarray(rows)
    saturation = np.asarray(saturations)
    reference_time = (first_tilt or first_fall or {'time_s':traces[-1,0]})['time_s']
    window = (traces[:,0]>=reference_time-.3) & (traces[:,0]<=reference_time)
    by_joint = saturation[window].mean(0)
    most = np.argsort(by_joint)[::-1][:6]
    label = f'{mode}_{speed:g}mps'
    directory.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(directory/(label+'.npz'),
        trace=traces,targets=np.asarray(targets),raw_actions=np.asarray(actions),saturation=saturation,
        max_requested_torque=np.asarray(requested),feet_support=np.asarray(support),
        depth_hit_pixels_and_max_action=np.asarray(observations))
    result = dict(speed_m_s=speed,mode=mode,steps=len(rows),duration_s=float(d.time),
                  first_contact=first_contact,first_tilt_20deg=first_20,first_tilt=first_tilt,first_fall=first_fall,
                  serves=round_index+1,events=events,ball_robot_impulse_magnitude_sum_Ns=float(total_impulse),
                  min_root_height_m=float(traces[:,1].min()),stop_reason='fall' if first_fall else 'duration_or_replay_end',
                  max_tilt_deg=float(traces[:,2].max()),max_abs_target_offset_rad=float(np.max(np.abs(np.asarray(targets)-sim.default))),
                  saturation_window_s=[float(traces[window,0][0]),float(traces[window,0][-1])],
                  saturated_physics_fraction_by_joint=[dict(joint=joint_names[k],fraction=float(by_joint[k]),
                     torque_limit_Nm=float(sim.limits[k,1])) for k in most],
                  no_feet_support_fraction_in_window=float((~np.any(np.asarray(support)[window],axis=1)).mean()),
                  trace_file=label+'.npz')
    return result,np.asarray(actions)


def main(output):
    checkpoint = torch.load(s2s.RUN/'model_49999.pt',map_location='cpu',weights_only=False)
    course = checkpoint['agile_v4_return_curriculum']
    progress = course['extension_steps']/course['config']['extension_steps']
    upper = course['extension_start_upper']+(6-course['extension_start_upper'])*progress
    baseline, targets = [],{}
    for speed in (1.,2.,3.,4.,6.):
        result,target = diagnose(speed,output.parent)
        baseline.append(result)
        targets[speed]=target
        print(f"baseline {speed:g} m/s: fall={result['first_fall']}, tilt={result['max_tilt_deg']:.1f}",flush=True)
    # Diagnose the first failing fast case above the established 2 m/s default.
    failures = [r for r in baseline if r['first_fall'] and r['speed_m_s']>2.]
    chosen = failures[0]['speed_m_s'] if failures else 6.
    contrasts = []
    for mode in ('ghost','hold','replay_ghost','training_hip_roll_limit'):
        result,_ = diagnose(chosen,output.parent,mode=mode,
                            replay=targets[chosen] if mode=='replay_ghost' else None)
        contrasts.append(result)
        print(f"contrast {mode}: fall={result['first_fall']}, tilt={result['max_tilt_deg']:.1f}",flush=True)
    result = dict(checkpoint=str(s2s.RUN/'model_49999.pt'),policy_sha256=s2s.sha256(s2s.RUN/'exported/policy.pt'),
                  simulator_sha256=s2s.sha256(Path(s2s.__file__)),diagnostic_sha256=s2s.sha256(Path(__file__)),
                  training_speed_upper_m_s=upper,curriculum=course,baseline=baseline,contrasts=contrasts,
                  trace_columns=['time_s','root_height_m','tilt_deg','root_x','root_y','ball_speed_m_s',
                    'ball_contact','ball_impulse_magnitude_Ns','round','root_vx','root_vy','root_vz','root_wx','root_wy','root_wz',
                    'com_x','com_y','com_z','com_vx','com_vy','com_vz','com_margin_to_loaded_foot_aabb_m'],
                  scope='single deterministic scene per speed; stop at first fall; no population failure-rate claim')
    output.write_text(json.dumps(result,indent=2)+'\n')
    assert upper == 6.
    assert all(r['steps']>0 for r in baseline+contrasts)
    assert all(r['first_contact'] is None for r in contrasts if 'ghost' in r['mode'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)
