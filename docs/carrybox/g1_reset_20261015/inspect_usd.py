from isaaclab.app import AppLauncher
app=AppLauncher(headless=True).app
from pxr import Usd
s=Usd.Stage.Open('source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/g1_29dof.usd')
for p in Usd.PrimRange(s.GetDefaultPrim(),Usd.TraverseInstanceProxies()):
 if 'left_ankle_roll_link' in str(p.GetPath()):print('FOOT_PRIM',p.GetPath(),p.GetTypeName(),p.GetAppliedSchemas(),flush=True)
app.close(wait_for_replicator=False)
