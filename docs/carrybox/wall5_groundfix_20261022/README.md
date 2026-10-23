# wall5 revision26：恢复PhysHSI倾斜终止并修复reset穿地

2026-10-22。用户在确认本地PhysHSI也有角度终止后，要求采用相同实现、排查bug再启动训练。本轮恢复实际注册的roll/pitch终止，并修复前次640初态审计已证实的G1足底穿地。没有把放宽终止当作稳定性修复。

## 终止条件

本地 `/home/cao/PhysHSI/legged_gym/legged_gym/envs/g1/carrybox.py:303` 实际执行 `abs(roll)>0.5 OR abs(pitch)>1.1`；保留[源码片段与hash](physhsi_termination.txt)。wall5使用同样的绝对角度和严格大于比较（单位rad；约28.6°/63.0°）。恢复 `Episode_Termination/tipped`。

其他条件保持：pelvis link origin相对地面高度<0.2m、mid360_link origin<0.6m、任一hip_yaw link origin<0.15m、箱子世界XY速度模长>3m/s、20秒/1000 policy步超时。非有限值仍报错停止；无成功或独立箱子倾倒reset。PhysHSI源码超时使用`>`，IsaacLab使用`>=1000`；两者配置上限同为20秒，未改变IsaacLab既有超时边界。

`Skill/*_tilt_at_episode_end_fraction` 保留明确的物理姿态名称：它是结束回合时的倾斜多标签统计，可与低高度同时发生，不是独占原因比例。manager的`Episode_Termination/*`还存在记忆/覆盖语义，不能直接当作近期完成回合百分比。

## 确认的bug与修复

revision24迁移直接采用PhysHSI `base_height+0.05m`，移除了原G1足底几何校正。该高度结合当前USD和最终关节随机化/软限位，不能保证脚部凸包在地面以上。revision25仅取消倾斜终止，并未修复接地。

revision26在随机关节姿态、速度写入之后调用`sim.forward()`刷新FK，不推进物理时间。复用已有`reference_ground_correction`，读取当前实际双脚convexHull的最低点，只向上补足5mm间隙；默认和所有参考起点都处理。只重写根部位姿z，保持根COM速度、关节角/速度、动作延迟缓存和其他环境状态。

配对参考箱子及活动支撑台上移相同距离，父级仍执行箱底地面下限和平台箱底上限。默认/loco箱子仍贴地；非活动平台仍在地面下5m。新增`Reset/ground_correction_mean_m`和`Reset/ground_correction_max_m`用于记录每批reset的修正，训练日志是采样聚合值，不是全程极值。

这是当前G1碰撞几何的适配修复；PhysHSI原源码没有这条几何校正，因此不能声称两套reset全部逐行相同。PhysHSI本身未修改。

## 对同一批640初态的验证

每个初态在修正前后都用实际物理FK变换足部碰撞几何测量；只读测量不推进仿真。结果与上次审计的原始640起点分布/穿地数量吻合。

| 起点 | 样本数 | 修正前穿地>1mm | 修正后穿地>1mm | 修正后最小间隙 |
|---|---:|---:|---:|---:|
| 默认 | 122 | 10 | 0 | 约5mm |
| loco | 350 | 303 | 0 | 约5mm |
| pickup | 88 | 80 | 0 | 约5mm |
| hold | 80 | 80 | 0 | 约5mm |

总体修正前473/640穿地；最深6.56cm，最大全部上移量7.06cm。修正后全体最低4.999906mm，差异为浮点误差。640初态无立即触发的倾斜、高度或箱速终止。详细逐样本数据见[smoke.json](smoke.json)，按技能统计见[ground_summary.json](ground_summary.json)。

检查最终箱子和平台物理位置、非活动平台、根COM速度、关节速度、五格延迟缓存；无序部分reset保持幸存环境机器人/箱台状态及缓存不变。三个pickup片段均覆盖。保留角度恰好等于0.5/1.1时不终止的标量边界测试；实际仿真分别测试±0.49/±0.51、±1.09/±1.11，隔离高度后结果符合阈值。低高度、箱速2.99/3.01m/s、1000步超时检查通过。

5项已有CPU检查通过；64环境一次完整PPO/AMP更新参数有限，actor/critic/CNN/辅助头有更新，新revision26可严格恢复，旧revision25拒绝。仅三个wall5生产文件变化；wall3/wall4、football、共享资产、数据hash保持。新旧环境契约只变化revision、角度终止描述/阈值、接地/配对平移声明和诊断语义；奖励、PD、网络、AMP、RSI抽样及数据保持本轮前配置。

[专家只读审查](expert_brief.json)、[原样执行回执](receipts.json)、[改动补丁](change.patch)。测试命令为`bash docs/carrybox/wall5_groundfix_20261022/smoke.sh`及`bash docs/carrybox/wall5_groundfix_20261022/start_and_verify.sh`。

## 结论边界

已确认并消除采样初态的穿地；未证明这是之前失稳的唯一原因，也未证明修复后策略能稳定行走或拾箱。先前回放还显示策略动作加速侧倒，任务奖励中原始力矩惩罚与PhysHSI归一化公式不同；本轮不将未经新动态对照的奖励假说作为已确认bug修改。学习效果需要后续训练曲线和空手起点回放评估，持箱RSI成功不能当作从地面抓起。

## 正式训练验收快照

2026-10-22T22:17:45.034302+09:00：旧revision25 PID **1792770** 已退出，日志最后第 **153** 轮；保存到 `/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-22_22-00-37_wall5_v25_no_tilt_fresh_20261022_220032/model_0.pt`，所有旧文件保留。

新 PID **1796143**，4096环境、seed42、40000轮、**从零初始化**；首模型schema2/revision26、全新优化器step20与AMP计数61440、参数有限，环境契约与短测一致。核验到第 **17** 轮，近10轮平均 **3.839s/轮**、最慢 **3.850s/轮**。

Run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-22_22-13-48_wall5_v26_groundfix_fresh_20261022_221344`

```bash
tail -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v26_groundfix_fresh_20261022_221344.log
```

[正式启动快照](snapshot.json)、[来源身份](validated_sources.json)、[执行回执](receipts.json)。训练正在进行；目前未评估是否学会稳定行走或拾箱；本轮确认消除了采样初态足底穿地。
