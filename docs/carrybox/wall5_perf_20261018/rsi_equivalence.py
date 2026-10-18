"""Compare former per-clip RSI writes against current batched writes in real PhysX."""
import ast,torch
from pathlib import Path
from unittest.mock import patch

@torch.inference_mode()
def check(env,task):
    path=Path(__file__).parent/'baseline_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py'
    fn=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='initialize_reference')
    scope=dict(vars(task));exec(compile(ast.Module(body=[fn],type_ignores=[]),'<baseline RSI>','exec'),scope)
    old=scope['initialize_reference'];new=task.initialize_reference
    robot=env.scene['robot'];ids=torch.arange(min(512,env.num_envs//2),device=env.device)
    objects=['box','wall','cylinder0','cylinder1','cylinder2']
    def snapshot():
        return dict(root=robot.data.root_state_w.clone(),link_velocity=robot.data.root_link_lin_vel_w.clone(),
            link_angular=robot.data.root_link_ang_vel_w.clone(),joint=robot.data.joint_pos.clone(),
            joint_velocity=robot.data.joint_vel.clone(),ends=robot.data.body_link_pos_w.clone(),
            **{name:env.scene[name].data.root_state_w.clone() for name in objects})
    initial=snapshot();rng=torch.cuda.get_rng_state()
    outputs=[]
    for function in (old,new):
        robot.write_root_state_to_sim(initial['root']);robot.write_joint_state_to_sim(initial['joint'],initial['joint_velocity'])
        for name in objects:env.scene[name].write_root_state_to_sim(initial[name])
        env.sim.forward();torch.cuda.set_rng_state(rng)
        with patch.object(task,'initialize_reference',function):task.reset_scene(env,ids)
        env.sim.forward();outputs.append(snapshot());after_rng=torch.cuda.get_rng_state()
        if function is old:expected_rng=after_rng
        else:assert torch.equal(expected_rng,after_rng),'RSI RNG differs'
        assert (task.reference_ground_correction(env,ids)<2e-5).all(),'feet penetrate'
        for name,value in outputs[-1].items():
            torch.testing.assert_close(value[len(ids):],initial[name][len(ids):],atol=3e-5,rtol=1e-5,msg=lambda msg:name+' untouched: '+msg)
    errors={}
    for name,a in outputs[0].items():
        b=outputs[1][name];torch.testing.assert_close(a,b,atol=3e-5,rtol=1e-5,msg=lambda msg:name+': '+msg)
        errors[name]=float((a-b).abs().max())
    skills=task.state(env).skills[ids];assert (skills==2).any() and (skills==0).any()
    ground=skills==0
    bottom=task.base.lift_geometry(env)[0][ids]
    torch.testing.assert_close(bottom[ground],torch.full_like(bottom[ground],.005),atol=3e-5,rtol=0)
    return dict(max_abs_errors=errors,rng_equal=True,partial_reset_unchanged=True,feet_clear=True,
                loco_count=int(ground.sum()),hold_count=int((skills==2).sum()),hold_min_box_bottom=float(bottom[~ground].min()))
