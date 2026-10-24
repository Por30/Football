# 逐项证据附录

与[完整对照](README.md)配套。配置作者值和实际spawn覆写分开；本轮没有物理仿真。

## 29个关节：原URDF限位与两边名义控制参数

以下顺序为URDF定义顺序，非运行时张量顺序。动作/专家数据必须按名字映射，不能依赖这个表的行号。Kp/Kd为两边当前相同的名义值；PhysHSI另外施加每reset随机因子。

| 关节 | 默认角rad | Kp | Kd | 下限rad | 上限rad | effort Nm | velocity rad/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| left_hip_pitch_joint | -0.1 | 150 | 2 | -2.5307 | 2.8798 | 88 | 32 |
| left_hip_roll_joint | 0.0 | 150 | 2 | -0.5236 | 2.9671 | 139 | 20 |
| left_hip_yaw_joint | 0.0 | 150 | 2 | -2.7576 | 2.7576 | 88 | 32 |
| left_knee_joint | 0.3 | 300 | 4 | -0.087267 | 2.8798 | 139 | 20 |
| left_ankle_pitch_joint | -0.2 | 40 | 1 | -0.87267 | 0.5236 | 35 | 30 |
| left_ankle_roll_joint | 0.0 | 40 | 1 | -0.2618 | 0.2618 | 35 | 30 |
| right_hip_pitch_joint | -0.1 | 150 | 2 | -2.5307 | 2.8798 | 88 | 32 |
| right_hip_roll_joint | 0.0 | 150 | 2 | -2.9671 | 0.5236 | 139 | 20 |
| right_hip_yaw_joint | 0.0 | 150 | 2 | -2.7576 | 2.7576 | 88 | 32 |
| right_knee_joint | 0.3 | 300 | 4 | -0.087267 | 2.8798 | 139 | 20 |
| right_ankle_pitch_joint | -0.2 | 40 | 1 | -0.87267 | 0.5236 | 35 | 30 |
| right_ankle_roll_joint | 0.0 | 40 | 1 | -0.2618 | 0.2618 | 35 | 30 |
| waist_yaw_joint | 0.0 | 300 | 4 | -2.618 | 2.618 | 88 | 32 |
| waist_roll_joint | 0.0 | 300 | 4 | -0.52 | 0.52 | 35 | 30 |
| waist_pitch_joint | 0.0 | 300 | 4 | -0.62 | 0.62 | 35 | 30 |
| left_shoulder_pitch_joint | 0.0 | 200 | 3 | -3.0892 | 2.6704 | 25 | 37 |
| left_shoulder_roll_joint | 0.1 | 200 | 3 | -1.5882 | 2.2515 | 25 | 37 |
| left_shoulder_yaw_joint | 0.0 | 200 | 3 | -2.618 | 2.618 | 25 | 37 |
| left_elbow_joint | 1.2 | 100 | 1 | -1.0472 | 2.0944 | 25 | 37 |
| left_wrist_roll_joint | 0.0 | 20 | 0.5 | -1.972222054 | 1.972222054 | 25 | 37 |
| left_wrist_pitch_joint | 0.0 | 20 | 0.5 | -1.614429558 | 1.614429558 | 5 | 22 |
| left_wrist_yaw_joint | 0.0 | 20 | 0.5 | -1.614429558 | 1.614429558 | 5 | 22 |
| right_shoulder_pitch_joint | 0.0 | 200 | 3 | -3.0892 | 2.6704 | 25 | 37 |
| right_shoulder_roll_joint | -0.1 | 200 | 3 | -2.2515 | 1.5882 | 25 | 37 |
| right_shoulder_yaw_joint | 0.0 | 200 | 3 | -2.618 | 2.618 | 25 | 37 |
| right_elbow_joint | 1.2 | 100 | 1 | -1.0472 | 2.0944 | 25 | 37 |
| right_wrist_roll_joint | 0.0 | 20 | 0.5 | -1.972222054 | 1.972222054 | 25 | 37 |
| right_wrist_pitch_joint | 0.0 | 20 | 0.5 | -1.614429558 | 1.614429558 | 5 | 22 |
| right_wrist_yaw_joint | 0.0 | 20 | 0.5 | -1.614429558 | 1.614429558 | 5 | 22 |

## 所有link：质量、原始碰撞几何与坐标

“无collision”不代表没有visual mesh或不能在深度中遮挡。USD继承原collision；mesh为convexHull，肩部四个cylinder在当前spawn后转换成capsule。几何原点是link局部坐标。

| link | URDF质量kg | USD质量kg | 原URDF collision | 局部origin xyz / rpy |
|---|---:|---:|---|---|
| pelvis | 3.813 | 3.812999963760376 | 无collision | — |
| pelvis_contour_link | 0.001 | 0.0010000000474974513 | mesh filename=../meshes/pelvis_contour_link.STL | 0 0 0 / 0 0 0 |
| pelvis_contact_link | None | 0.0 | 无collision | — |
| left_hip_pitch_link | 1.35 | 1.350000023841858 | mesh filename=../meshes/left_hip_pitch_link.STL | 0 0 0 / 0 0 0 |
| left_hip_roll_link | 1.52 | 1.5199999809265137 | mesh filename=../meshes/left_hip_roll_link.STL | 0 0 0 / 0 0 0 |
| left_hip_yaw_link | 1.702 | 1.7020000219345093 | mesh filename=../meshes/left_hip_yaw_link.STL | 0 0 0 / 0 0 0 |
| left_knee_link | 1.932 | 1.9320000410079956 | box size=0.09 0.07 0.1<br>box size=0.05 0.04 0.1 | 0.01 0.00 -0.105 / 0 0 0<br>0.005 0.00 -0.21 / 0 0 0 |
| left_ankle_pitch_link | 0.074 | 0.07400000095367432 | mesh filename=../meshes/left_ankle_pitch_link.STL | 0 0 0 / 0 0 0 |
| left_ankle_roll_link | 0.608 | 0.6079999804496765 | mesh filename=../meshes/left_ankle_roll_link.STL | 0 0 0 / 0 0 0 |
| right_hip_pitch_link | 1.35 | 1.350000023841858 | mesh filename=../meshes/right_hip_pitch_link.STL | 0 0 0 / 0 0 0 |
| right_hip_roll_link | 1.52 | 1.5199999809265137 | mesh filename=../meshes/right_hip_roll_link.STL | 0 0 0 / 0 0 0 |
| right_hip_yaw_link | 1.702 | 1.7020000219345093 | mesh filename=../meshes/right_hip_yaw_link.STL | 0 0 0 / 0 0 0 |
| right_knee_link | 1.932 | 1.9320000410079956 | box size=0.09 0.07 0.1<br>box size=0.05 0.04 0.1 | 0.01 0.00 -0.105 / 0 0 0<br>0.005 0.00 -0.21 / 0 0 0 |
| right_ankle_pitch_link | 0.074 | 0.07400000095367432 | mesh filename=../meshes/right_ankle_pitch_link.STL | 0 0 0 / 0 0 0 |
| right_ankle_roll_link | 0.608 | 0.6079999804496765 | mesh filename=../meshes/right_ankle_roll_link.STL | 0 0 0 / 0 0 0 |
| waist_yaw_link | 0.214 | 0.21400000154972076 | 无collision | — |
| waist_roll_link | 0.086 | 0.0860000029206276 | 无collision | — |
| torso_link | 6.78 | 6.78000020980835 | mesh filename=../meshes/torso_link_rev_1_0.STL | 0 0 0 / 0 0 0 |
| logo_link | 0.001 | 0.0010000000474974513 | 无collision | — |
| head_link | 1.036 | 1.0360000133514404 | 无collision | — |
| imu_in_torso | None | 0.0 | 无collision | — |
| imu_in_pelvis | None | 0.0 | 无collision | — |
| d435_link | None | 0.0 | 无collision | — |
| temp_link | None | 0.0 | 无collision | — |
| d455_link | None | 0.0 | 无collision | — |
| mid360_link | None | 0.0 | 无collision | — |
| left_shoulder_pitch_link | 0.718 | 0.7179999947547913 | cylinder radius=0.03 length=0.05 | 0 0.04 -0.01 / 0 1.5707963267948966 0 |
| left_shoulder_roll_link | 0.643 | 0.6430000066757202 | cylinder radius=0.03 length=0.03 | -0.004 0.006 -0.053 / 0 0 0 |
| left_shoulder_yaw_link | 0.734 | 0.734000027179718 | mesh filename=../meshes/left_shoulder_yaw_link.STL | 0 0 0 / 0 0 0 |
| left_elbow_link | 0.6 | 0.6000000238418579 | mesh filename=../meshes/left_elbow_link.STL | 0 0 0 / 0 0 0 |
| left_wrist_roll_link | 0.08544498 | 0.08544497936964035 | mesh filename=../meshes/left_wrist_roll_link.STL | 0 0 0 / 0 0 0 |
| left_wrist_pitch_link | 0.48404956 | 0.48404955863952637 | mesh filename=../meshes/left_wrist_pitch_link.STL | 0 0 0 / 0 0 0 |
| left_wrist_yaw_link | 0.08457647 | 0.08457647264003754 | 无collision | — |
| left_rubber_hand | 0.17 | 0.17000000178813934 | mesh filename=../meshes/left_rubber_hand.STL | 0 0 0 / 0 0 0 |
| left_palm_link | None | 0.0 | 无collision | — |
| right_shoulder_pitch_link | 0.718 | 0.7179999947547913 | cylinder radius=0.03 length=0.05 | 0 -0.04 -0.01 / 0 1.5707963267948966 0 |
| right_shoulder_roll_link | 0.643 | 0.6430000066757202 | cylinder radius=0.03 length=0.03 | -0.004 -0.006 -0.053 / 0 0 0 |
| right_shoulder_yaw_link | 0.734 | 0.734000027179718 | mesh filename=../meshes/right_shoulder_yaw_link.STL | 0 0 0 / 0 0 0 |
| right_elbow_link | 0.6 | 0.6000000238418579 | mesh filename=../meshes/right_elbow_link.STL | 0 0 0 / 0 0 0 |
| right_wrist_roll_link | 0.08544498 | 0.08544497936964035 | mesh filename=../meshes/right_wrist_roll_link.STL | 0 0 0 / 0 0 0 |
| right_wrist_pitch_link | 0.48404956 | 0.48404955863952637 | mesh filename=../meshes/right_wrist_pitch_link.STL | 0 0 0 / 0 0 0 |
| right_wrist_yaw_link | 0.08457647 | 0.08457647264003754 | 无collision | — |
| right_rubber_hand | 0.17 | 0.17000000178813934 | mesh filename=../meshes/right_rubber_hand.STL | 0 0 0 / 0 0 0 |
| right_palm_link | None | 0.0 | 无collision | — |

URDF合计33.34114202 kg；USD合计33.34114242 kg。未把质量一致推断成所有惯量/接触响应等价。

## 全部专家文件与当前映射

hash是完整文件SHA256；同hash意味着字节一致，不仅是同名或同帧数。源概率按19段总weight45；wall5按组40/40/20重新加权。

| PhysHSI文件（相对dataset_carrybox） | 帧数 | 源weight | 当前文件 | 文件SHA256 |
|---|---:|---:|---|---|
| `pickUp/pickup1.pt` | 192 | 4 | pick_up/pick_up_01.pt | `6a44d35afc4912781505615576e7a5ba141ffe3c756db652968c5bb0af31d17a` |
| `pickUp/pickup2.pt` | 178 | 4 | pick_up/pick_up_02.pt | `429cb67521975946fcf930fb5a430bbae9c7495e6d4db1ba2d4b330cdfbf023d` |
| `pickUp/pickup3.pt` | 129 | 4 | pick_up/pick_up_03.pt | `cd54f21376d77ea7d6cccb662b5ea2ae53b68ca7a61528742e40ef0c2cdf30f5` |
| `putDown/putdown1.pt` | 141 | 5 | 未纳入 | `a740984fa8ccc6b7cc43d2055a5e5f2416dc994df9887712c5d7f80369723479` |
| `putDown/putdown2.pt` | 238 | 5 | 未纳入 | `70390d0a4da3ace685dc7c2b7548080e08f0b55539c8a99439ceee870454d9e7` |
| `carryWith/carrywith1.pt` | 256 | 5 | 改造为hold/hold_box_01.pt，非同文件 | `da7e7cb38bcc2324a9d6aeac347dfb94d567f624a4d0c8cb86f22c860bffafb9` |
| `carryWith/carrywith2.pt` | 194 | 2 | 未纳入 | `a35d464857092be005533adbfbe5b4e77ae637f8616210ddeb342f7fdd886ff0` |
| `carryWith/carrywith3.pt` | 323 | 5 | 未纳入 | `1f0868733cee5eafeb85f72fd2975c521f8d6d085f7961541c1f55f505c55d29` |
| `loco_direction/B1_-_stand_to_walk_stageii.pt` | 342 | 1 | locomotion/stand_to_walk_01.pt | `b5183955fe3766bc30901e66c650f3601daf4fd2969125acc5e73e2ba93064bd` |
| `loco_direction/B2_-_walk_to_stand_stageii.pt` | 340 | 1 | locomotion/walk_to_stand_01.pt | `a341d6821635bbbc9cda0ec0711034511e9ddb267be3c9206f8aaf539cb21fec` |
| `loco_direction/B2_-_walk_to_stand_t2_stageii.pt` | 293 | 1 | locomotion/walk_to_stand_02.pt | `78fea9d0b50e521da7e373e7202d5d5c2f625273ef095ae5371249d5a35b762e` |
| `loco_direction/B3_-_walk1_stageii.pt` | 456 | 1 | locomotion/walk_forward_01.pt | `02cbd97382a70f4e6ac33c03939a98ce723528326b5ea9046802d65f38b039b9` |
| `loco_direction/B9_-_walk_turn_left_(90)_stageii.pt` | 214 | 1 | locomotion/walk_turn_left_090.pt | `200d9e22dbff9245d10749173896fd0bb822149491d96fc0d3c7c29d94727bd3` |
| `loco_direction/B10_-_walk_turn_left_(45)_stageii.pt` | 253 | 1 | locomotion/walk_turn_left_045.pt | `dfdf2fe9bf0014327477bed39cd08f5526b6e4e4092613ae463d15fa47524fcb` |
| `loco_direction/B11_-_walk_turn_left_(135)_stageii.pt` | 289 | 1 | locomotion/walk_turn_left_135.pt | `f399edac6517b511d277aed64026d1169eb724281f9e386a27d4a162f6021374` |
| `loco_direction/B12_-_walk_turn_right_(90)_stageii.pt` | 263 | 1 | locomotion/walk_turn_right_090.pt | `d643da4f4971ab3d78ba272d14a1761ef80e54cb429070bf3a1cc92b85366a33` |
| `loco_direction/B13_-_walk_turn_right_(45)_stageii.pt` | 256 | 1 | locomotion/walk_turn_right_045.pt | `9aa45b671abcd29d5d092c6caf0b38367e861b41c8950b98a4a2b2761c9b34fa` |
| `loco_direction/B14_-_walk_turn_right_(135)_stageii.pt` | 321 | 1 | locomotion/walk_turn_right_135.pt | `1ca14d346efac52f5f0ebcd9bc52cd1e6eb6a67a73c37a65e78024abec696868` |
| `loco_direction/B15_-_walk_turn_around_(same_direction)_stageii.pt` | 329 | 1 | locomotion/walk_turn_around_01.pt | `bbf1bf4b9a6abc7db5a05fc166a6e11f454ecb14ba7371d4aca2476c45fb5cca` |

当前hold文件：`hold/hold_box_01.pt`，300帧，SHA256=`ac0e873274b3425925b218ccbd682e59590210363754c39bc78092231be273e8`。前21帧后重复frame20；并不是完整carryWith轨迹。

## 独立FK检查：每段最多32个均匀帧

五端点顺序：left_palm、right_palm、left_ankle_pitch、right_ankle_pitch、mid360。用原URDF、数据q和root quaternion独立计算，比较数据前五行link_position。单位mm。

| 当前文件 | 检查帧数 | 左掌最大误差 | 右掌最大误差 | 左踝最大误差 | 右踝最大误差 | mid360最大误差 |
|---|---:|---:|---:|---:|---:|---:|
| hold/hold_box_01.pt | 32 | 1.64641 | 1.64643 | 5.36015e-05 | 5.46915e-05 | 1.64641 |
| locomotion/walk_turn_left_045.pt | 32 | 3.76267 | 3.76263 | 0.000235848 | 0.000206765 | 3.76268 |
| locomotion/walk_turn_left_135.pt | 32 | 3.3676 | 3.36766 | 0.000199191 | 0.000173686 | 3.36765 |
| locomotion/walk_turn_right_090.pt | 32 | 3.81122 | 3.81121 | 0.000195186 | 0.000128976 | 3.8113 |
| locomotion/walk_turn_right_045.pt | 32 | 3.72716 | 3.72721 | 0.000167666 | 0.000175865 | 3.72722 |
| locomotion/walk_turn_right_135.pt | 32 | 3.56242 | 3.56238 | 0.000118306 | 0.000208441 | 3.56248 |
| locomotion/walk_turn_around_01.pt | 32 | 3.8101 | 3.81015 | 0.000209264 | 0.000173045 | 3.81014 |
| locomotion/stand_to_walk_01.pt | 32 | 3.51431 | 3.51433 | 0.000134836 | 0.000193253 | 3.51433 |
| locomotion/walk_to_stand_01.pt | 32 | 3.688 | 3.68797 | 0.00020748 | 9.87404e-05 | 3.68799 |
| locomotion/walk_to_stand_02.pt | 32 | 3.62848 | 3.62844 | 0.000205733 | 0.000232734 | 3.62846 |
| locomotion/walk_forward_01.pt | 32 | 3.53227 | 3.53229 | 0.000216436 | 0.000188395 | 3.53234 |
| locomotion/walk_turn_left_090.pt | 32 | 3.65599 | 3.65595 | 0.000212771 | 0.000131588 | 3.65599 |
| pick_up/pick_up_01.pt | 32 | 6.82939e-05 | 6.34703e-05 | 5.97799e-05 | 5.64266e-05 | 7.94763e-05 |
| pick_up/pick_up_02.pt | 32 | 9.10016e-05 | 7.74731e-05 | 6.83985e-05 | 6.12142e-05 | 7.48104e-05 |
| pick_up/pick_up_03.pt | 32 | 0.000143445 | 8.93789e-05 | 5.48774e-05 | 5.33449e-05 | 8.63846e-05 |

源base_height和按双踝相对z重建的专家高度在这些样本上基本一致，详见data.json的差值；这不是动态仿真的根部/足底高度检查。

## 每一个有效reward term与最终注册函数

下表来自正式wall5 env.yaml；None不算有效项。函数内部更深的门控在主报告第11节。

| term | weight | func | params |
|---|---:|---|---|
| dof_acc | -1.0e-07 | `isaaclab.envs.mdp.rewards:joint_acc_l2` | `{}` |
| action_rate | -0.03 | `isaaclab.envs.mdp.rewards:action_rate_l2` | `{}` |
| torques | -0.0001 | `isaaclab.envs.mdp.rewards:joint_torques_l2` | `{}` |
| dof_vel | -0.0002 | `isaaclab.envs.mdp.rewards:joint_vel_l2` | `{}` |
| dof_pos_limits | -5.0 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled:reference_joint_pos_limits` | `{}` |
| dof_vel_limits | -0.001 | `isaaclab.envs.mdp.rewards:joint_vel_limits` | `{"soft_ratio": "1.0"}` |
| walk_task | 1.0 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5:walk_task` | `{}` |
| carryup_task | 1.0 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5:grasp_task_reward` | `{"name": "carryup_task"}` |
| standup_task | 0.4 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards:task_reward` | `{"name": "standup_task"}` |
| slow_pickup | -0.0005 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5:grasp_task_reward` | `{"name": "slow_pickup"}` |
| stable_grasp | 0.2 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5:grasp_task_reward` | `{"name": "stable_grasp"}` |
| arm_speed_pickup | -0.02 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5:grasp_task_reward` | `{"name": "arm_speed_pickup"}` |
| arm_acc_pickup | -2.0e-05 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_wall5:grasp_task_reward` | `{"name": "arm_acc_pickup"}` |
| grip_force_cap | -0.02 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_x2_rewards:task_reward` | `{"name": "grip_force_cap"}` |
| held_hand_speed | -0.02 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled:held_joint_excess` | `{"acceleration": "false", "threshold": "1.0"}` |
| held_hand_acc | -2.0e-05 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled:held_joint_excess` | `{"acceleration": "true", "threshold": "20.0"}` |
| waist_yaw_penalty | -0.5 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled:waist_yaw` | `{}` |
| search_turn | 0.5 | `perceptual_ball.tasks.manager_based.perceptual_ball.mdp.carrybox_walled:search_turn` | `{}` |
| alive | 3.0 | `isaaclab.envs.mdp.rewards:is_alive` | `{}` |

PhysHSI有效scales（所有非零项）：

| term | weight |
|---|---:|
| action_rate | -0.03 |
| carryup_task | 1.0 |
| dof_acc | -1e-07 |
| dof_pos_limits | -5.0 |
| dof_vel | -0.0002 |
| dof_vel_limits | -0.001 |
| relocation_task | 1.0 |
| standup_task | 0.2 |
| torque_limits | -0.03 |
| torques | -0.0001 |
| walk_task | 1.0 |

## 源码/资产身份与符号入口

完整展开参数保存在sources.json，所有相关函数起始行保存在source_symbols。以下hash锁定本轮审阅身份；当前工作区不是干净checkout，不能只用git HEAD替代文件身份。

| 文件 | SHA256 |
|---|---|
| [/home/cao/PhysHSI/README.md](/home/cao/PhysHSI/README.md) | `cd84d1f6a96deacb7cf33f04741986c29f00b7dbc250cb252cb74d3c30802a48` |
| [/home/cao/PhysHSI/legged_gym/legged_gym/envs/__init__.py](/home/cao/PhysHSI/legged_gym/legged_gym/envs/__init__.py) | `546af72c8239cc6a23f26cc7fe863258d289876981a476bdcc57418024efd9ba` |
| [/home/cao/PhysHSI/legged_gym/legged_gym/envs/base/legged_robot_config.py](/home/cao/PhysHSI/legged_gym/legged_gym/envs/base/legged_robot_config.py) | `5162a4241c3da2d5410c594d57d0f561a5f84463cebe1870259cb9f3c2f55697` |
| [/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py) | `c37e7c5ff4884baba2a40ddfde5b9d91f01b427fea7bf9812da26231c35630b7` |
| [/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox_config.py](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox_config.py) | `dcb44bb88c7bdcb204ae8beab0d4bd480cd26a8c15a8b819cb76d05511d00a9b` |
| [/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox_resume_config.py](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox_resume_config.py) | `0d033399933aaf582266f46e889b28b2d78865d78494b979008a688bb5b0326f` |
| [/home/cao/PhysHSI/legged_gym/legged_gym/envs/motionlib/motionlib_carrybox.py](/home/cao/PhysHSI/legged_gym/legged_gym/envs/motionlib/motionlib_carrybox.py) | `c88409cd1a1f2f797af80fa56d21dfb302ac6e4bdd2a0001a9d10b1ab746d862` |
| [/home/cao/PhysHSI/legged_gym/legged_gym/scripts/play.py](/home/cao/PhysHSI/legged_gym/legged_gym/scripts/play.py) | `bcba79883d3a601f52a5bf7d4e871fdc983f1e4c86635328cb6721b7fbd20df4` |
| [/home/cao/PhysHSI/legged_gym/resources/config/carrybox.yaml](/home/cao/PhysHSI/legged_gym/resources/config/carrybox.yaml) | `dd2898e872d3ea80f48c35f19e3ebbc09232791e31cdb42076c21b0ecfe75bbc` |
| [/home/cao/PhysHSI/legged_gym/resources/config/joint_id.txt](/home/cao/PhysHSI/legged_gym/resources/config/joint_id.txt) | `0e09bd4a124e1e00e92b742ff9954405bd7ff0c17ab42bc91072248bd6e72da7` |
| [/home/cao/PhysHSI/legged_gym/resources/robots/g1/urdf/g1_29dof.urdf](/home/cao/PhysHSI/legged_gym/resources/robots/g1/urdf/g1_29dof.urdf) | `427c3b69c2f3f3bfb16e1bfdecd564326a505642efba33198c8d33db44ac974e` |
| [/home/cao/PhysHSI/rsl_rl/rsl_rl/algorithms/him_ppo.py](/home/cao/PhysHSI/rsl_rl/rsl_rl/algorithms/him_ppo.py) | `0a9b7bb651565293030f036e9e6ddc3526d23d78ae08fafc5d085fa4d86fa0b2` |
| [/home/cao/PhysHSI/rsl_rl/rsl_rl/modules/amp.py](/home/cao/PhysHSI/rsl_rl/rsl_rl/modules/amp.py) | `84102e02973726b6471d3131bc649d4c98983b859676e6148e008de4a0859f78` |
| [/home/cao/PhysHSI/rsl_rl/rsl_rl/modules/actor_critic.py](/home/cao/PhysHSI/rsl_rl/rsl_rl/modules/actor_critic.py) | `e927c12730ee1fe0635524cda05507ff11259e8102f0b0e16d9da756887b2efd` |
| [/home/cao/PhysHSI/rsl_rl/rsl_rl/runners/him_on_policy_runner.py](/home/cao/PhysHSI/rsl_rl/rsl_rl/runners/him_on_policy_runner.py) | `b8cebe9f2cb619012217a8952ebac9c3d35f648103da52efd1cc400deaffc56c` |
| [/home/cao/PhysHSI/rsl_rl/rsl_rl/storage/him_rollout_storage.py](/home/cao/PhysHSI/rsl_rl/rsl_rl/storage/him_rollout_storage.py) | `5be810433c54cfda48774193521e1c91ea66d07566c2a5fb9193f35b998897f4` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_amp.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_amp.py) | `2156aef8eb3833522e0b0c4adf98f3dfa308e15b548ea860c85230f349523e24` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_wall5.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_wall5.py) | `3128a3300862d017909cb59cef7112e6d63137364aa2c19dd76b0d7e9046d21d` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_wall10.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_wall10.py) | `766dbfdbe0dd723eb1f87ea4418c7129c4e5d5ac0ccc14812e8c20728f29e506` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_physhsi.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_physhsi.py) | `cbe963f2e0885c99871f0badb287066b47b9402dbdaa25a35b5d8674b7c3bee9` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_reward_geometry.py) | `9ab270b74216de3206514ea38beff0adcf5b1aa22d6c0816189c292c4bd51a07` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_walled.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_walled.py) | `2a5e1543ce93b6bd0fd0adc66b51e0a959e57e0612ed336e85d524a004f3906b` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py) | `6ae09ebfc08972392db6b1a22867812ed24758de669ac6b7898d3755cfe9e6fb` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_raycast.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_raycast.py) | `694ca58c162aebf078ae922020b6a9b80e5dbabe72865d0178a4020645e83421` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof.py) | `fce7c3aef21f8d848f5333e81b0446676a02aa1552eb1e8ba144ccd7f14072d5` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/config.yaml](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/config.yaml) | `707afdd528d204129ba229c0d5b08793b2cbe501d090a068a2bf2889038f793d` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py) | `b1a4030937bbdcbeb37811119b2cbdf24825c87d00a00e1ca33aff974e282061` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py) | `fb1311d3f0dcdbb2069fc9f8e0b4cca687733a1f267aaf5c540177b975ae25b9` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py) | `8e88c20dcc26f80733d76d8e824019c128da9182954c5faff984d55196cf0bb5` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/amp.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/amp.py) | `e58c3cc4bcc646dec92f9733e8243eeac12f4eb6395a16fc1375dd7116d614bd` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/modules.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/modules.py) | `ff99f6c18276bb75279ac01071152bde44c72947fb8dd615b6a7c71dd3bd580b` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py) | `a7452ff77eed2eac49458a83e105a50629e6aec6be6994ec4f46c5e7216a1f5c` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py) | `00530b20fd176d33b1b7c65052da02e668ff7b6b5b5e943ba60a356c814d4de0` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py) | `8a34e999cba3f4b55e7c2589d748db4d80aaea9c448cb7ad9a3b0c64a2f88608` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py) | `a765a41b07406169559b36345b1c88600e0f2e2e22606d72a4d98495d5bad6b9` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py) | `613052334f3ed3db49d18f5ab5eaf4fee65a8043a878b46b436e388e6e624ddb` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py) | `1797d679e5fc8b38ca49392752fb0bc1f6960d185734c0c05022eb535434878e` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_state.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_state.py) | `e48d3d2706673cbb94dfda8a3a445697d6e6e89b700915288ec2a6057253580f` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py) | `1d31ed2b47cc93f8d82d15a1fe81b4d680da228a225b389a1367a4d77fb533f0` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py) | `f54f6ab8852a0b416d566e5de4bdd01a5c830416c81e57a5ffe86d1aa042cf34` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py) | `4bc1e3743031af2a9e407da78fa1e237080dcc3b0f6967aaa9316606429c6791` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py) | `e232d431a023cb8163d083b385e7403fe1e271b81a13564d56de1181eefaec81` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py) | `e3ad1681f2ab3718ef6c0cf17ec588ffdf7973cbafa4719a52db65e0ed925183` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/g1_29dof.usd](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/g1_29dof.usd) | `3d758783f76d86afdfd5df6e951a1d521dcebba8fd27120f181cfee588aca132` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/configuration/g1_29dof_base.usd](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/configuration/g1_29dof_base.usd) | `fb6897abaa287dc547e36ab73c3c955432195200d71948b697968c45ab3222c7` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/configuration/g1_29dof_physics.usd](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/configuration/g1_29dof_physics.usd) | `c4f83d17273ae97b1d4c71feb399bd6cb9c8ba6f607dd64ecb62ae3b6fcd5a52` |
| [/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/configuration/g1_29dof_sensor.usd](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/assets/robots/g1_29dof/configuration/g1_29dof_sensor.usd) | `173c9feba7fd9fbafa38f4cefa03859a6f89d6fe6e82ef4a1f464940db95a3a9` |

## 机器可读原始参数

[effective_parameters.tsv](effective_parameters.tsv)按source_default / source_resume / wall5逐字段展平全部已存配置。各框架字段名不同，这个文件用于找漏项，不以同名字段自动判定语义等价。
