# PhysHSI G1 carrybox 与 wall5 revision23：碰撞和 reset 对照

2026-10-22。实际目录为`/home/cao/PhysHSI`。按任务注册追踪`carrybox`及`carrybox_resume`，读取真实G1 URDF、配置继承和调用代码，并做CPU配置/数据核对。**两边都开自碰撞，但碰撞几何、接触奖励、参考起点分布和初始速度并不相同。** 本次没有启动PhysHSI仿真，没有修改任一生产任务、数据或训练进程。

## 碰撞：物理接触、奖励与直接终止须分开看

| 项目 | PhysHSI `carrybox` | 当前 wall5 revision23 |
|---|---|---|
| 自碰撞开关 | `self_collisions=0`传给Isaac Gym `create_actor`，0表示启用 | 任务覆写`enabled_self_collisions=True`；共享G1基类默认仍为false |
| 几何来源 | 原始`g1_29dof.urdf`的collision定义 | 同一URDF转换的USD，再由wall5函数补全/替换外壳 |
| 碰撞元素 | XML去注释后28个link、30个collision元素 | 源码逐link替换后35个碰撞形状；与此前运行核对的profile一致 |
| 骨盆 | `pelvis`本身无collision；`pelvis_contour_link`有mesh，不能说整个骨盆没碰撞 | 保留contour，并给`pelvis`新增整个视觉网格凸包 |
| 膝/小腿 | 每侧两个box，尺寸0.09×0.07×0.10m、0.05×0.04×0.10m | 每侧替换为整块视觉mesh的convex hull |
| 肩pitch/roll | 小圆柱，配置`replace_cylinder_with_capsule=True` | 用肩部视觉mesh凸包 |
| 其余新增 | 腰yaw/roll、head、wrist_yaw、logo没有collision | 这些link补视觉mesh凸包 |
| 成对过滤 | 该任务Python未额外配置shape filter或指定碰撞对；导入器自身规则本次未动态读回 | 显式过滤waist_yaw↔torso、左右knee↔同侧ankle_roll三对；其余仍受PhysX默认规则和碰撞几何约束 |
| 接触扣分 | **没有启用**`collision`奖励 | `undesired_contacts=-1`，对髋/膝净接触力超过1N的link计数，包含自接触 |
| 碰撞直接reset | `terminate_after_contacts_on=[]`，该分支无触发对象 | 也没有接触力直接终止项；碰撞导致姿态/高度越界时才会reset |

PhysHSI虽然定义`penalize_contacts_on=[hip,knee,torso,shoulder,pelvis]`及`_reward_collision`函数，但`G1Cfg.rewards.scales`没有collision；注册器只注册非零配置项，所以这条惩罚没有运行。不能把“定义了接触部位”解释为“启用了碰撞奖励”。同样，它没有启用termination奖励。

这解释了为何“参考PhysHSI打开自碰撞”还不足以对齐：wall5碰撞包络更大，并额外惩罚髋膝自接触。此前wall5诊断读到`pelvis↔left_hip_roll_link`约4.15kN峰值；PhysHSI原URDF没有wall5新增的pelvis根凸包，因此不能假定它有同样的接触。不能据此直接删除所有自碰撞，仍应分辨结构重叠和真实接触。

来源：[原配置](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox_config.py:115)、[actor创建](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:1531)、[奖励注册](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:1236)、[当前外壳补全](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_fullbody_collision.py:1)、[当前接触奖励](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py:106)。

## Reset：PhysHSI实际执行顺序

1. 每次reset先做Bernoulli抽样，80%参考初始化、20%默认姿态初始化。参考组再按`[0.8,0.2,0.2,0]`权重抽loco/pickUp/carryWith/putDown。
2. 这组权重总和是1.2，`torch.multinomial`实际条件概率为66.67%/16.67%/16.67%/0。因此全部reset的概率为：**默认20%、loco RSI53.33%、pickup RSI13.33%、carry RSI13.33%、putdown0**。不是80/20/20%，也不是X2的80/0/20。
3. 参考片段内部随机连续时间，插值关节角、关节速度、根姿态和位置。读取根参考速度后，**随后统一覆盖根部六维速度为U[-0.2,0.2]**，线速度单位m/s、角速度rad/s。关节速度仍保留参考值；关节角加±0.1rad扰动并裁剪到配置限位。
4. 默认起点使用配置站姿加关节扰动、关节速度0；但根部六维速度是U[-0.5,0.5]，所以这20%也不是完全静止起点。
5. 按起点重置箱子和支撑平台/目标平台，再批量写入机器人与物体状态；清理动作、速度等缓存，并用`reset后的关节角−默认角`填满动作延迟缓存。
6. 动作延迟每个物理步更新一次，物理dt=5ms，5格缓存对应0–4步，即**0–20ms**。不是0–100ms的五个policy步。开始时缓存里的旧项对应reset姿态，避免延迟队列输出无关的默认姿态；阻尼项、参考关节速度与随后策略仍会影响运动，不能理解成短暂固定机器人。

来源：[reset与延迟填充](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:310)、[RSI速度覆盖](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:797)、[混合抽样](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:830)、[物理步动作延迟](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:737)。

## 当前wall5的不同点

| 项目 | PhysHSI | wall5 revision23 |
|---|---|---|
| 技能分配 | 每次reset重新抽样 | 按env编号固定75%loco/5%pickup/20%hold配额；片段与帧仍随机 |
| 默认姿态起点 | 20% | 无，100%参考初始化 |
| pickup RSI | 三段均可抽全片段时间，包含接触/抬升后的姿态 | 仅地面03的0–31帧；**三段完整AMP不等于三段完整RSI** |
| 根部速度 | RSI各轴±0.2随机值，覆盖参考速度 | 直接使用源位置差分速度，去yaw后写到pelvis link；角速度也用参考 |
| 关节状态 | 参考角+扰动+裁剪，参考关节速度 | 参考角/速度，没有相同的每回合±0.1rad关节位置扰动；默认角另有启动时小扰动 |
| 接地修正 | 根高来自base_height+0.05，无相同的足底hull计算 | 根据实际足底凸包最低点，只向上修正到5mm间隙 |
| 动作缓冲 | 0–20ms动作延迟，reset角预填充 | 无动作延迟队列；动作历史清零，下一次策略输出直接生成限位内位置目标 |
| 箱子/平台 | pickup参考前段按contact_index设置支撑台；默认/loco箱子可在不同高度 | loco/pickup箱底贴地5mm，无平台；hold保留手边参考箱子高度 |

本次重新核对了11段loco文件，PhysHSI与本项目文件hash逐段一致。按当前“片段等概率、片段内帧均匀”方式统计源水平速度：均值**0.743m/s**，P95 **1.071m/s**，最大**1.290m/s**。PhysHSI的**RSI分支**水平速度理论上限仅√2×0.2≈**0.283m/s**；其默认起点分支另有√2×0.5上限，不能把0.283说成所有reset的上限。

因此wall5通常要求策略从一个已经以行走速度运动的姿态接管，PhysHSI则显著降低RSI根部初速度，同时用延迟缓存维持最初目标。这会改变学习难度；但是PhysHSI保留参考关节速度而覆盖根速度，本身也不是完整动力学一致的参考状态，不能把它直接当作更正确的物理reset。旧版wall5在当前RSI下已经能走，故该差异也不能单独解释revision23退化。

PhysHSI默认/loco的箱子XY每轴独立取±[0.7,4]m，箱心高度随机后下限夹到半箱高，最高约0.65m，并配置平台；wall5普通loco为前方±45°、半径0.7–2m、贴地，另有2%视野外搜索起点。两者任务分布不同。

## 终止触发条件

| 条件 | PhysHSI carrybox | wall5 |
|---|---|---|
| roll / pitch | abs(roll)>0.5或abs(pitch)>1.1 | 相同 |
| 根高 | <0.2m | <0.2311m |
| 头高 | 读取配置`mid360_link`，<0.6m | 读取`head_link`物理COM，<0.4387m；测量点不同，不能直接当同比例阈值 |
| 其他 | hip_yaw高度<0.15m；箱子水平速度>3m/s | 无这两项；有非有限状态终止 |
| 超时 | 配置20s，代码`episode_length > max` | 配置20s |
| 箱子倾倒 | carrybox关闭；carrybox_resume开启 | 没有独立箱子倾倒终止 |
| 成功立即reset | 无，成功标记用于任务统计/奖励 | 无，保持原回合逻辑 |

PhysHSI的`gravity_termination_buf >0.8`虽被计算，但没有并入`reset_buf`；不能写成有效终止规则。`rigid_body_states[:,2]`在该场景指箱子：前两个body为两张平台、第三个是箱子，不是机器人根部。这一3m/s终止条件也不能误报成“机器人跑太快reset”。

来源：[完整终止函数](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:284)、[状态布局](/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:1068)、[wall5终止覆写](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py:80)。

## 与当前不稳定问题的关系

优先检查wall5新增骨盆/整小腿凸包及自接触计分。PhysHSI提供了一个具体参照：保留自碰撞，但使用原始较保守的碰撞几何，且搬箱子任务没有启用通用collision惩罚。再分别验证参考速度接管与动作缓存；不能把碰撞、速度、RSI比例和奖励同时全部照搬后宣称根因已解决。

另一个与奖励比较直接相关的旁证：PhysHSI `_reward_torques`计算`sum((torque / p_gain)^2)`，当前通用`joint_torques_l2`计算原始力矩平方；即便配置权重同为−1e−4也不是同一量级。本次只记录公式，未改权重，也未将其认定为revision23独有根因。

本次为源码/配置与数据核对；CPU检查PASS，不代表PhysHSI实际接触对、接触峰值或成功率已经重新动态验证。详见[audit.json](audit.json)、[执行回执](receipts.json)。正式wall5训练未停止或重启。
