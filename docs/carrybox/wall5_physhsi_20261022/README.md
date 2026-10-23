# wall5 revision24：PhysHSI G1 碰撞与 reset 迁移

2026-10-22，用户授权“把碰撞和逻辑改成 PhysHSI 版本，然后重启训练”。依据本地 G1 `carrybox` 实际配置与调用路径，见[只读对照](../physhsi_collision_reset_20261022/README.md)。本次迁移机器人碰撞、混合初始化、动作延迟和失败终止；不是把整个 FindBox 改成 PhysHSI 的搬运放置任务。

## 生效变化

| 项目 | revision23 | revision24 |
|---|---|---|
| 碰撞几何 | 视觉凸包全身补齐，新增pelvis根外壳、整小腿/肩凸包 | 原URDF碰撞，22个mesh、4个小腿Cube、4个肩Capsule；28个有碰撞link/30个形状 |
| 自碰撞 | 开启，显式过滤三对结构重叠 | 保持开启；去掉全身外壳及三对自定义过滤，保留引擎相邻关节默认规则 |
| 髋膝接触扣分 | 净接触力>1N计数，包含自接触 | `undesired_contacts=None`，与PhysHSI未注册collision奖励一致 |
| reset选择 | 固定env配额75/5/20，全RSI | 每次独立抽样20%默认、80%参考；参考条件权重8/2/2归一化 |
| 全部reset的概率 | 默认0、loco75%、pickup5%、hold20% | 默认20%、loco RSI53.33%、pickup RSI13.33%、hold RSI13.33% |
| pickup RSI | 地面03，第0–31帧 | 三段完整pickup，连续时间插值；接触前使用支撑平台，接触后平台移到地下 |
| 根部速度 | 保留参考速度 | 参考六轴U[-.2,.2]，默认六轴U[-.5,.5]；线速度m/s、角速度rad/s；COM世界系 |
| 关节reset | 参考角/差分速度 | 参考角加±.1rad，再裁剪到URDF范围90%软限位；使用数据记录的joint_velocity；默认关节速度0 |
| 根部高度 | 参考高度+5cm，再按足底hull向上修正 | 原生base_height+5cm；默认站姿0.8m，无额外足底修正 |
| 动作延迟 | 无 | 每个5ms物理步更新5格队列，对应0–20ms；每回合重采样，reset实际关节角填满队列 |
| 失败终止 | 低骨盆.2311、head_link COM低于.4387、roll/pitch | 骨盆<.2、mid360原点<.6、任一hip_yaw原点<.15、箱子XY速度>3m/s；roll.5/pitch1.1保持 |

非有限保护与20秒episode保持；没有接触力直接终止、箱子倾倒终止或成功立即reset。三个低高度原因使用新配置函数分别记录，避免日志继续引用旧阈值。默认起点合并到现有loco任务统计，但通过独立`default_reset`标记及`Reset/default_fraction`区分，不能把loco任务统计全部解释为loco RSI。

## 保留与坐标适配

- 普通loco/default仍是FindBox前方±45°、0.7–2m的地面箱，保留2%视野外搜索、墙/圆柱和箱子yaw课程；没有照搬PhysHSI普通箱子各轴±0.7–4m、随机高度以及目标放置平台。此前向用户说明并给出选择，未收到改变此默认范围的回复。
- 机器人和参考箱一起去掉参考yaw、平移到环境原点；默认朝向同样采用FindBox正向。这是场景坐标适配，不改变参考的相对机器人/箱关系。箱子参考高度下限保持地面5mm间隙；支撑平台采用当前项目0.5×0.5×0.8m代理并匹配接触前箱底，不重建PhysHSI随机尺寸/材质场景。
- actor仍为93×4本体+4×27×48米制深度；critic123独立MLP、AMP60、15段完整数据、全配对帧辅助监督系数1.0保持。平台也进入Warp深度遮挡目标。
- revision23抓取/站位奖励、PD、摩擦、推扰课程和PPO保持；动作目标仍按物理限位裁剪。没有把PhysHSI的全部奖励或显式力矩控制照搬过来。
- 共享G1 USD/URDF不修改；碰撞转换只发生在wall5运行stage。wall3/wall4与football行为保持。

## 实现与兼容性

新纯函数和碰撞构建：[carrybox_physhsi.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/carrybox_physhsi.py)。运行时reset、延迟和终止：[mdp/carrybox_physhsi.py](/home/cao/perceptual_ball/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_physhsi.py)。wall5配置绑定新路径，父reset只新增可选initializer；未传该参数的旧任务沿用原实现。

checkpoint schema仍为2，迁移revision升为24；契约写明碰撞profile、混合概率、记录关节速度、90%软限位、COM速度、延迟与终止。旧revision23恢复在短测中被严格拒绝，新正式训练从零开始。原始15段AMP数据及manifest未改；只把RSI加载路径由ground_pickup快照切回完整findbox目录。

## 验证与修正记录

24项CPU检查通过：抽样概率与重新抽样、连续插值/四元数、延迟0/4步、乱序部分reset、终止阈值/坐标/箱速，并回归AMP数据、抓取奖励和米制深度。

64环境仿真读回原始碰撞形状和自碰撞设置、取消接触扣分，覆盖默认/loco/全部三个pickup/hold；检查乱序部分reset不污染其他环境，根部COM速度、记录关节速度、90%软限位及五格缓存与实际初始化一致。每policy步队列恰好更新四次，平台可被Warp看见。完成PPO/AMP两轮更新、保存/严格恢复、再更新一轮及actor导出等价检查；旧模型契约拒绝。详见[smoke.json](smoke.json)。

首次检查误把空`pelvis/collisions` Xform当作碰撞体，失败后保留回执并改为检查CollisionAPI及完整叶形状集合，几何要求没有放宽。随后复核PhysHSI发现reset必须裁剪90%软限位，已补齐并增加实际状态边界断言；中间启动进程1759807在初始化期间停止，其日志保留，不作为最终正式训练。两次修正记录见`repair1.json`、`repair2.json`及对应attempt文件。

短测和正式启动验收只说明管线运行、配置与更新有效，不证明已经学会稳定行走或地面拾箱。

## 正式训练验收快照

2026-10-22T20:37:21.658897+09:00：原revision23 PID 1588407已停止，最后日志迭代7491，保留模型`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-22_12-27-03_wall5_v23_grasp_selfcollision_fresh_20261022_122658/model_7400.pt`及全部旧日志。中间PID1759807已退出，其初始化日志归档。

最终PID **1760747**，4096环境、seed42、40000轮、**fresh**；首模型schema2/revision24、全新优化器step20与AMP统计计数61440、参数有限，完整环境契约与短测一致。检查到**第15轮**，最近10轮平均**3.871s**、最慢**3.910s**，满足每轮6秒要求。

Run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-22_20-33-25_wall5_v24_physhsi_fresh_20261022_203320`

```bash
tail -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v24_physhsi_fresh_20261022_203320.log
```

[最终执行回执](receipts.json)、[正式启动快照](snapshot.json)、[源身份](validated_sources.json)。训练进行中，尚未验证稳定行走或从地面拾箱成功率。
