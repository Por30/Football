"""Finite physical RSI probes and real, unfiltered arm/torso self contact."""
import torch
from pxr import PhysxSchema,UsdPhysics
import omni.physics.tensors as physics
from perceptual_ball.carrybox_fullbody_collision import SELF_COLLISION_FILTER_PAIRS
from perceptual_ball.tasks.manager_based.perceptual_ball.mdp import carrybox_walled as parent

def verify_self_collision(env):
    robot=env.scene['robot'];stage=env.sim.get_initial_stage()
    root=stage.GetPrimAtPath('/World/envs/env_0/Robot')
    assert PhysxSchema.PhysxArticulationAPI(root.GetChild('pelvis')).GetEnabledSelfCollisionsAttr().Get() is True
    for a,b in SELF_COLLISION_FILTER_PAIRS:
        targets=UsdPhysics.FilteredPairsAPI(root.GetChild(a)).GetFilteredPairsRel().GetTargets()
        assert root.GetChild(b).GetPath() in targets
    pv=physics.create_simulation_view('torch');pv.set_subspace_roots('/')
    contact=pv.create_rigid_contact_view(
        '/World/envs/env_0/Robot/*',
        filter_patterns=['/World/envs/env_0/Robot/'+n for n in robot.body_names],max_contact_data_count=4096)
    sources=list(contact.sensor_paths);records={};ids=torch.arange(env.num_envs,device=env.device)
    for skill,name in enumerate(('loco','pickup','hold')):
        peaks=[];velocities=[]
        for _ in range(8):
            parent.reset_scene(env,ids,skill_ids=torch.full_like(ids,skill))
            robot.set_joint_position_target(robot.data.joint_pos.clone())
            env.scene.write_data_to_sim();env.sim.forward()
            peak=0.
            for _ in range(4):
                env.sim.step(render=False);env.scene.update(env.physics_dt)
                force=contact.get_contact_force_matrix(env.physics_dt).norm(dim=-1)
                peak=max(peak,float(force.max()))
                assert torch.isfinite(robot.data.root_state_w).all() and torch.isfinite(robot.data.joint_vel).all()
                assert torch.isfinite(env.scene['box'].data.root_state_w).all()
            peaks.append(peak);velocities.append(float(robot.data.joint_vel.abs().max()))
        # Compare against the unfiltered 20–70 kN structural explosions. This is
        # a bounded initialization check, not a dynamic stability/success test.
        assert max(peaks)<1000.,(name,peaks)
        records[name]=dict(initial_self_contact_peak_n=peaks,joint_velocity_max_rad_s=velocities,
                           envs_per_reset=env.num_envs,resets=8,physics_steps_per_reset=4)
    # Suspended nominal default pose must have no large self contact impulses.
    for mode in ('default','crossed_arms'):
        root_state=robot.data.default_root_state.clone();root_state[:,:3]=env.scene.env_origins
        root_state[:,2]+=3.;root_state[:,7:]=0.
        q=robot.data.default_joint_pos.clone()
        if mode=='crossed_arms':
            for name,value in [('left_shoulder_pitch_joint',-.7),('right_shoulder_pitch_joint',-.7),('left_shoulder_roll_joint',-.7),('right_shoulder_roll_joint',.7),('left_elbow_joint',1.8),('right_elbow_joint',1.8)]:q[:,robot.joint_names.index(name)]=value
        robot.write_root_link_state_to_sim(root_state);robot.write_joint_state_to_sim(q,torch.zeros_like(q))
        robot.set_joint_position_target(q);env.scene.write_data_to_sim();env.sim.forward()
        peak=None
        for _ in range(12):
            env.sim.step(render=False);env.scene.update(env.physics_dt)
            force=contact.get_contact_force_matrix(env.physics_dt).norm(dim=-1)
            peak=force if peak is None else torch.maximum(peak,force)
            assert torch.isfinite(robot.data.root_state_w).all() and torch.isfinite(robot.data.joint_vel).all()
        if mode=='default':assert float(peak.max())<100.,float(peak.max())
        if mode=='crossed_arms':
            a=sources.index('/World/envs/env_0/Robot/left_elbow_link');b=robot.body_names.index('torso_link')
            assert peak[a,b]>.1,peak[a,b]
        records[mode]=dict(peak_n=float(peak.max()),nonadjacent_contact_count=int((peak>.1).sum()))
    return dict(enabled=True,filter_pairs=SELF_COLLISION_FILTER_PAIRS,physical_probes=records)
