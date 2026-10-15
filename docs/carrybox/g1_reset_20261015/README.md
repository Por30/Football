# G1站立reset排查、接地适配与wall4重启（2026-10-15）

本轮按用户要求排查旧model_14000播放易reset，核对X2交接在G1上的相机/构型适配，并在验证后后台启动4096环境wall4。已后台启动PID2660033，2026-10-15T13:10:49.858630+09:00核验到iteration12；正式状态见launch.json和formal_check.json。

## 站立reset的直接原因

revision7环境、旧revision6 model_14000、16环境、300步纯推理：1600个loco完成回合全部3步触发tipped，均非fell或timeout。首例结束root_z=.716m、实际head COM_z=1.153m、roll=.534rad，越过原有abs(roll)>.5条件。初始roll=-.086rad正常，旧策略第一步已产生约9.14rad/s横滚角速度。相机不是终止条件输入。

固定同一RSI关节目标时平均38.93步；同时清零初始化速度为50.39步；默认站姿零动作平均57.75步。这些是开环诊断，不证明站立控制稳定。证据支持旧策略控制造成快速倾倒，不支持放宽roll阈值或把它全归因相机。新训练明确不用该失败checkpoint或旧warm-start。

[完整探针](probe.json) / [分情形摘要](probe_summary.json)。每情形另有16个未结束回合，不混入完成回合统计。probe为修复前revision7；不是revision8训练结果。

## 本轮新增G1修复

发现RSI固定base_height+.05仍使真实G1脚底穿地：16个样本中loco最低-17.74mm、pickup最低-11.01mm、hold最低-8.31mm。这是独立于旧策略失效的初始化适配问题，可能引入接触冲量。

共同wall MDP在写入参考root/joints后用sim.forward刷新运动学，从实际G1足部collisions父Xform的合并convexHull提取局部支撑顶点，一次缓存；按本次足部完整link姿态和各env地面高度求最低点。补偿dz=max(ground+5mm-min_foot,0)，只向上调整本次reset的root z，参考箱z和pickup支撑高度同步补偿，保留姿态、速度和关节。最终箱体贴地/防穿透逻辑保留。不会添加物理step或移动其他环境。

revision升到8，schema仍为2。wall3/wall4均使用该helper，仍只在墙/圆柱场景及任务日志身份上不同。未改共享G1资产、足球、AMP原始数据、策略输入和相机参数；原revision7的实际head COM、双膝下限惩罚和动作hard-limit裁剪继续生效。旧revision6/7不能完整resume到revision8。

[修正前后同样本比较](ground_fix_comparison.json)显示root姿态和速度不变，脚底高度变化等于root补偿（最大数值误差小于0.1微米）；修正后最低点约5mm。手—箱参考位置在最终箱体贴地限制之前保持；极低箱体仍须遵守地面约束。

## G1相机和构型核验

- 29个G1关节按名称映射；源xyzw转换到IsaacLab wxyz，写入/读回一致，PhysX转换由IsaacLab完成。新增CPU检查正负roll/pitch边界、yaw与四元数符号。
- 物理head COM作为头高，不使用G1腰部附近的head_link原点。站立/抱箱约1.2m，pickup蹲姿可约.67m；.4m终止阈值不会误杀这些样本。真实倾倒条件保持。
- 名义相机挂在G1 torso_link，偏移[.0576235,.01753,.42987]m、pitch=.8307767rad（47.6度下俯），与源G1 URDF d435_joint一致，非X2 head_pitch_link。平移/旋转机器人后实际相机parent变换误差约0.4微米。
- Warp光轴深度48×27、50Hz、0.1–3m；内参fx=fy=24.354645，cx=24、cy=13.5。43组可见几何含36个机器人link、箱/墙/三柱/平台及地面。实际墙/柱遮挡后移后方箱子不改变对应深度；抱箱姿态身体遮挡42–43像素（仅该姿态统计，不代表所有姿态）。
- actor/critic均为本体372维（4帧）+深度4×27×48；9维位姿标签只作辅助监督；AMP10×64仅作判别器/奖励。验证修改标签和AMP观测不会改变actor/critic输出。

这些检查确认本地G1资产名义适配。用户未提供具体实机光心外参、CameraInfo及预处理，不能把名义URDF核验说成实机标定完成。

## 验证和状态

44项CPU；16环境三技能实际接地、部分reset保持其他环境root/joints/targets、相机变换、障碍/身体遮挡、fresh首4步均无reset、PPO/AMP更新恢复导出；loco/pickup/hold均形成有效AMP窗口。4096环境完整迭代维持24步、PPO4epochs×4minibatches，热身后平均4.544秒、最慢4.664秒，通过≤6秒验收；见4096/result.json。

前期验证脚本修正过16环境障碍探针与随机机器人重叠、inference-mode重置范围；读取USD碰撞时发现CollisionAPI在合并父Xform而非叶Mesh，修正后重新验收。失败日志/回执保留。发现接地问题后中断未修正版本的4096预检，新版结果单独记录。短测不能证明收敛。

新正式配方：wall4、4096环境、40000轮、seed42、fresh，无resume/warm_start；15段规范FindBox AMP。初始化loco/pickup/hold=60/30/10；初始std=.2、entropy=.001；推扰前1000轮关闭，之后4000轮渐增；yaw/search/奖励沿用共同配置。不得将直接抱箱RSI成功算作完整地面找箱拾取成功，应分别观察Skill/loco_*、Skill/pickup_*、Skill/hold_*。

## 已启动的正式训练

- PID：2660033，独立后台session，4096环境、seed42、40000轮，从头训练。
- 核验快照：2026-10-15 13:10:49 JST，iteration12；正式热身后平均4.238秒、最慢4.33秒。
- 首个model_0.pt：schema2/revision8，15段AMP身份一致，策略/判别器参数有限，action std约0.19988；无旧checkpoint迁移。
- run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-15_13-06-53_wall4_g1_v8_scratch_20261015_130649`。
- 正式训练仍在进行，未证明站立/完整拾箱收敛；独立评估待做。

```bash
tail -n 100 -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/launch_g1_v8_20261015_130649/train.log
```

[最终测试回执](final_receipts.json) · [16环境验收](16/result.json) · [4096验收](4096/result.json) · [正式身份/耗时](formal_check.json) · [分技能启动快照](formal_metrics_snapshot.json) · [验证过程说明](validation_notes.json)。验证模型只保存在docs内，没有作为正式初始化。
