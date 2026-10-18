# Wall5 revision12：任务相关AMP与可见监督

2026-10-17。按用户的X2/G1训练端对照落实到G1 wall5；Gym ID保持`Template-Perceptual-Ball-CarryBox-Walled5-v0`。只完成实现和短测，未启动正式训练，未验证收敛或4096环境每轮耗时。后台football训练保持。

## 改动

| 项目 | revision11 | revision12 |
|---|---|---|
| AMP每帧/窗口 | 35 / 350，原始姿态特征 | 60 / 600，含任务与末端信息，running normalization |
| 辅助监督 | 所有xyz/rotation6目标，coef0.5 | 可见且范围内才监督，coef0.1；无效样本零梯度 |
| PPO | fixed 3e-4，entropy0.001，std0.2，4 epochs | 初始3e-4，adaptive KL0.01，entropy0.01，std1.0，5 epochs |
| actor/critic MLP | 256/128 | 512/256/256 |
| 侧倾终止 | abs roll>0.5 | abs roll>0.8；pitch仍1.1 |
| 失败惩罚 | 无 | 当前fell/tipped一次性weight=-10，排除timeout/旧回合flags |
| reset技能 | loco/pickup/hold = 0.7/0.3/0 | 0.8/0.2/0 |
| RSI速度语义 | z取base_height差分，写COM速度 | xyz均取base_position差分，写pelvis link速度，与新AMP一致 |

失败惩罚通过RewardManager的dt=0.02折算为任务奖励-0.2，混合后为-0.15。仍为20s回合，不因找到或抱起立即reset；root/head高度等其余终止保持。

AMP混合仍为`0.75 * task_reward + 0.125 * style_reward`；0.125是每步最大AMP贡献，不是固定总奖励占比。本次保留AMP系数/学习率5e-5及权重衰减，先修正特征语义。KL调节范围沿用已安装RSL-RL的[1e-5,1e-2]，每个minibatch按1.5倍调整；恢复checkpoint时同步恢复当前学习率。

动作std是策略动作单位；经过action scale0.25后，std1对应约0.25rad目标角扰动，原std0.2对应0.05rad。不能直接将std0.2解释为0.2rad关节扰动。

## 60维schema和数据

固定顺序：`height1 | joint_pos29 | endpoints15 | linear_vel3 | angular_vel3 | root_rot6 | box_pos3`，10帧、50Hz，专家60Hz片段内插值，不跨片段。

- pelvis link作为原点/坐标系；高度为pelvis到两个ankle_pitch原点中较低者的垂直差。
- 五末端依次为left_palm_link、right_palm_link、left_ankle_pitch_link、right_ankle_pitch_link、mid360_link。使用link原点，不用COM、rubber_hand中心或head_link腰部原点。
- 原数据link_position/box_pos_local为世界轴表达的root相对位移，专家和在线都做完整root逆旋转。
- 线速度使用base_position三维差分并转到root系，online使用root_link_lin_vel_w，避免COM混淆。真实RSI也按该语义写入，脚底凸包高度修正继续保持。
- 角速度用相邻单位四元数最短弧差分，避开原数据Euler差分在转身换支处约376.69rad/s的尖峰。
- root旋转去yaw后取旋转矩阵第1、第3列；辅助pose的6D仍是第1、第2列。
- box局部XY距离>0.7m时径向归一到0.7m，z置0；近处保留xyz。
- Normalizer跨10个时刻共享60维统计；初始2048个专家窗口拟合，之后每次D更新前从最多2048个policy窗口与等量expert窗口的原始值更新一次。保存mean/variance/count，epsilon1e-4、clip±10，奖励/小批次期间冻结。梯度惩罚作用在归一化坐标，系数0.5，避免因标准差隐式改变量纲。

原13段ground_pickup和原15段文件均未改写，manifest与文件映射保持。13段仍为11行走、完整地面pickup03的129帧、hold300帧，AMP组权重0.4/0.4/0.2。RSI只取pickup03的0–31帧，hold不参与reset，所有箱底离地5mm、无平台；全身35碰撞形状及自碰撞关闭保持。

独立URDF FK审计发现loco/hold的掌部与mid360端点存在最大约3.86mm残差；GPU对13段首帧逐字段核验时最大末端分量差约3.42mm，脚点和其余字段单独严格核验。pickup03基本为浮点精度。保留并报告该原数据/骨架细差，没有把所有60维一起放宽容差。

## 深度与信息边界

actor和critic始终只读372维本体历史与4×27×48深度历史。训练专用AMP为600维；辅助标签为xyz+rotation6+有效位共10维，网络输出仍9维。箱子真值、AMP、有效位、末端位置均不进入策略或价值输入。

Warp在原来的同一组射线、几何、遮挡关系上，wall5额外记录最近命中的mesh ID。至少一个Box像素在噪声/孔洞处理后有效，并且箱中心的相机光轴Z在[0.1,3.0)m内，才监督该帧。完全被墙、圆柱或身体挡住、视野外、太远、相机后方或有效像素全丢失时mask=0。mask和pose/depth经同一个delay/freeze buffer传递，partial reset仅刷新对应环境。所有样本屏蔽时loss与梯度为有限零值。

相机安装、FOV、分辨率、50Hz频率及噪声配置保持。本次没有完成实机标定，也没有将已有名义相机参数宣称为实测参数。football/wall3/4默认不开启hit-ID输出，旧Warp深度kernel保持原路径；共享CarryBox PPO新增hook的默认行为仍是原fixed PPO和原辅助损失。

日志可监控`Loss/box_position`、`Loss/box_rotation`、`Loss/box_visible_fraction`、`Loss/box_visible_distance`、`Loss/ppo_kl`、`Loss/ppo_learning_rate`、`Loss/amp_normalizer_count`及`Reward/*_per_step`。mask消除不可观测远箱的监督，不保证任何训练阶段loss永远小于1；不通过clamp损失掩盖异常。

## 验证与边界

固定命令：

```bash
bash docs/carrybox/wall5_training_v12_20261017/check.sh
bash docs/carrybox/wall5_training_v12_20261017/smoke.sh
```

38项CPU覆盖真实数据/坐标变换、AMP归一化与保存恢复、梯度mask、遮挡/丢帧、延迟冻结/partial reset、KL、终止一次性罚、旧任务及football随机化回归。4环境GPU覆盖实际PhysX/Warp、13段专家/live首帧、生产RSI速度、terminal/reset历史、2轮PPO/AMP+恢复1轮、优化器有限、策略导出等价以及旧checkpoint拒绝。最终短测辅助xyz loss依次约0.310、0.214、0.113，可见样本占比约92.7%、88.5%、82.3%；仅为短测，不推断长期趋势。32个pickup起点按新版RSI速度再测首20ms，箱速最大0.1962m/s，与重力自由落体量级一致，无接触弹飞。真实回执见[receipts.json](receipts.json)，详细数值见[smoke.json](smoke.json)。初次CPU夹具dtype/缺字段错误及修复记录保留；复核后又补了真实RSI速度路径，未把直接注入state当作reset验收。

资产单独审计：膝kp/kd保持300/4。虽然actuator配置未显式填所有限值，运行时USD已提供关节力矩5–139Nm、速度约20–37rad/s的有限限制，不能据“cfg未填写”推断无约束。左右手滤波接触传感器在隔离接触probe中均非零；probe只证明接触链路有效，不证明已学会抓箱。没有同时调整PD/碰撞体，也没有做150/5的独立训练比较。

用户对历史崩溃提出的因果链仍是待长期实验验证的解释；奖励数值占比不等于梯度贡献，辅助loss与episode length同时变化也不能单独证明因果。本次落实的是具体可验证机制修复。

## checkpoint与后续训练

新版环境migration_revision=12，AMP schema=3；外围CarryBox checkpoint schema仍为2。旧revision9/10/11完整恢复被拒绝，actor/critic尺寸变化也使旧weights-only入口不兼容；需要fresh训练。短测模型只在本docs目录，不能作为正式训练或成功率证据。

以下是后续fresh训练命令，本次未执行；执行前核对实际football进程/GPU占用。

```bash
cd /home/cao/perceptual_ball
source /home/cao/isaacsim/setup_conda_env.sh
export PYTHONPATH="/home/cao/IsaacLab/source/isaaclab:/home/cao/IsaacLab/source/isaaclab_rl:/home/cao/IsaacLab/source/isaaclab_tasks:/home/cao/IsaacLab/source/isaaclab_assets:$PWD/source/perceptual_ball:${PYTHONPATH:-}"
export OMNI_KIT_ACCEPT_EULA=YES
/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-CarryBox-Walled5-v0 \
  --num_envs 4096 --device cuda:0 --headless --seed 42 \
  --max_iterations 40000 --run_name wall5_task_amp_v12
```

正式输出仍在`logs/rsl_rl/g1_carrybox_depth/walled5/`。新增网络宽度及5 epochs可能改变更新时间；4环境耗时不能推断4096环境满足6秒/轮。
