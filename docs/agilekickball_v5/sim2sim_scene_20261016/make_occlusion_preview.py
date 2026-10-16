"""Reproduce scene-depth snapshots without training, rendering or real hardware."""
import json
from pathlib import Path
import sys
import tempfile

import mujoco
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts/sim2sim'))
import kickball_mujoco as s2s

OUT = Path(__file__).resolve().parent


def snapshot(sim):
    sim.camera.reset()
    frame = sim.observe()[1][0, -1].copy()
    ids = sim.camera.hit_geoms.reshape(27, 48)
    owner = np.zeros((27, 48), dtype=np.uint8)
    valid = ids >= 0
    owner[valid] = 4
    owner[ids == sim.floor_geom] = 1
    owner[ids == sim.ball_geom] = 3
    body = sim.model.geom_bodyid[np.maximum(ids, 0)]
    owner[valid & np.isin(body, list(sim.camera.robot_bodies))] = 2
    return frame, owner


sim = s2s.KickballSim(physics_dt=.005)
frames, owners = [], []
a, b = snapshot(sim)
frames.append(a); owners.append(b)
names = sim.manifest['metadata']['joint_names']
for name, value in dict(left_shoulder_pitch_joint=-1., left_elbow_joint=.1).items():
    sim.data.qpos[sim.qadr[names.index(name)]] = value
mujoco.mj_forward(sim.model, sim.data)
a, b = snapshot(sim)
frames.append(a); owners.append(b)
# Move the ball along a ray behind the actual arm; body-owned pixels must stay
# unchanged. Geometry ownership is diagnostic only, never an actor input.
pixel = np.flatnonzero(b.ravel() == 2)[len(np.flatnonzero(b.ravel() == 2))//2]
position, rotation = sim.camera.pose(sim.data)
direction = rotation@sim.camera.rays[pixel]
hidden = []
for distance in (1.6, 1.9):
    sim.data.qpos[sim.bq:sim.bq+3] = position+distance*direction
    mujoco.mj_forward(sim.model, sim.data)
    hidden.append(snapshot(sim)[0])
error = float(np.abs(hidden[0][b == 2]-hidden[1][b == 2]).max())
assert error == 0.

with tempfile.TemporaryDirectory() as directory:
    tree = s2s.ET.parse(s2s.ROBOT_XML)
    tree.getroot().find('compiler').set('meshdir', str(s2s.ROBOT_XML.parent/'meshes'))
    s2s.ET.SubElement(tree.getroot().find('worldbody'), 'geom', name='depth_test_wall',
        type='box', pos='1 .15 .45', size='.05 .35 .45', rgba='.4 .6 .8 1')
    path = Path(directory)/'scene.xml'
    tree.write(path)
    obstacle = s2s.KickballSim(robot_xml=path, physics_dt=.005)
    a, b = snapshot(obstacle)
    frames.append(a); owners.append(b)

fig = Figure(figsize=(12, 6.3), dpi=120, facecolor='white')
FigureCanvasAgg(fig)
titles = ['Standing: ground + ball', 'Raised arm: actual robot meshes', 'Added wall: environment occlusion']
for column, (frame, owner, title) in enumerate(zip(frames, owners, titles)):
    ax = fig.add_subplot(2, 3, column+1)
    im = ax.imshow(frame, vmin=.1, vmax=3., cmap='turbo_r', interpolation='nearest')
    ax.set_title(title, fontsize=10)
    ax.set_xlabel('pixel u'); ax.set_ylabel('pixel v')
    ax = fig.add_subplot(2, 3, column+4)
    ax.imshow(owner, vmin=0, vmax=4, cmap=ListedColormap(['#dce3eb','#4e9e57','#cf4d4d','#e7b124','#496acb']), interpolation='nearest')
    ax.set_title('Surface owner (diagnostic only)', fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
fig.suptitle('Kickball scene depth | optical Z [m] | nominal G1 camera', fontsize=14)
fig.text(.5, .025, 'Grey: far/no return   Green: ground   Red: robot   Yellow: ball   Blue: environment', ha='center', fontsize=10)
fig.subplots_adjust(left=.05, right=.88, top=.87, bottom=.08, wspace=.35, hspace=.32)
cax = fig.add_axes([.91, .54, .015, .3])
fig.colorbar(im, cax=cax, label='optical Z [m]')
fig.savefig(OUT/'occlusion_preview.png')
np.savez_compressed(OUT/'occlusion_samples.npz', depth_m=np.stack(frames), surface_owner=np.stack(owners))
result = dict(shape=[3,27,48], camera_calibration='nominal_unverified',
    owner_codes={'0':'far','1':'ground','2':'robot','3':'ball','4':'environment'},
    pixel_counts=[{name:int((o == code).sum()) for code,name in enumerate(['far','ground','robot','ball','environment'])} for o in owners],
    hidden_ball_test=dict(actual_robot_occluded_pixels=int((owners[1] == 2).sum()), max_depth_difference_m=error),
    limitation='Static snapshots, not task success or real-camera calibration evidence')
(OUT/'occlusion_samples.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
