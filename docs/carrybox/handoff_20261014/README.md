# G1 wall4：按 X2 handoff 修订与训练重启

2026-10-14。用户授权在核对handoff.txt差异后修改并重启训练。本记录区分实现、短测、正式训练和学习效果；CPU与真实仿真验收已通过，正式新进程已于21:08 JST启动，21:13 JST核验到iteration30。正式热身后平均4.230秒、最慢4.300秒；首个checkpoint schema2/revision6、新15段AMP身份与有限参数检查均通过。

## 已实现的变更

- wall3/wall4 RSI从80/15/5调整为80/0/20；新版规范FindBox数据15段4155帧，AMP专家采样仍40/40/20。pick_up保留为判别器专家数据，默认不作回合初始状态。
- wall3共18项、wall4共19项奖励。用handoff的walk/carryup/standup、slow_pickup、stable_grasp、pickup手臂速度/加速度、grip_force_cap及基础关节/接触惩罚替换旧approach/reach/lift/success/fall；保留held手臂惩罚、waist yaw，wall4另含search_turn。RewardManager仅乘一次dt=0.02。没有torque_limits或1.5倍力矩奖励。
- 终止修正为abs(roll)>0.5、abs(pitch)>1.1、root z<0.2或head z<0.4，以及20秒超时。所有高度相对env origin；成功不终止，非法数值硬报错保留。
- standup奖励用X2即时条件：箱高>0.6m、torso投影重力XY范数<0.2、头高>0.8m、手中心距箱<0.3m。独立G1严格成功率仍要求双手接触、离地、直立、低箱速和连续0.5秒；两者不混称。
- 深度米域高斯std0.06m、相邻梯度阈值0.15m/边缘5%丢失、像素2%孔洞、距离相关std=0.024+0.066*z/3米；10%延迟上一帧；0.2%概率冻结15帧（含开始帧）。每回合相机安装位置随机单位方向偏移0.01m，旋转误差置0。深度与监督标签同步延迟/冻结，reset刷新，不重复同帧采样。
- startup箱体摩擦static0.3–2.0、dynamic0.4–1.5、restitution0–0.2、64 buckets；基础质量改0.8kg，reset缩放0.1–1.5（实际0.08–1.2kg），质量和惯量均从默认值计算，不连乘。startup默认关节角±0.01rad并同步action offset；G1 torso COM x±0.025m、y/z±0.05m；每1–3秒设置root速度扰动，xyz分别±0.5/0.5/0.2m/s、roll/pitch/yaw分别±0.52/0.52/0.78rad/s。reset基础状态之后RSI覆盖，再放箱/墙/柱。
- 仅wall runner动作裁剪从5变9，动作缩放保持0.25rad，物理关节限制不改。三个pickup片段旧裁剪不可达帧比例20.8%/29.8%/49.6%，最大需要8.84195；含默认角扰动的上界8.88195，9覆盖当前全部15段。原CarryBox-v0与football仍为各自原配置。

## 有意保留的 G1 适配

actor/critic只用372维本体历史（4×93）及4×27×48深度；深度为光轴米值除以3，位姿辅助头输出相机光学坐标xyz+旋转6D，真值不进入策略/价值输入。AMP仍10×64纯本体窗口，不复制X2含箱子真值的600维输入。CNN/MLP、PPO配置与辅助系数保持本地实现，未改为X2特权critic或5帧网络。

G1相机仍挂torso_link，名义位置(0.0576235,0.01753,0.42987)m；并非X2 head_pitch_link安装。48×27、50Hz、垂直58°、0.1–3m光轴深度及43组Warp几何（机器人自身、地面、箱子、墙柱、平台）保留。真实硬件标定尚未提供，不声称已与真机逐项标定一致。

手部奖励使用G1 rubber_hand与Box过滤接触力，防止碰墙产生抓箱奖励；hip/knee用独立全接触传感器。COM映射G1 torso_link。standup身体速度/gravity和search yaw rate取torso frame。障碍继续使用已验证的六轴锁定刚体，以避免本机Isaac Sim 4.5运动学reset碰撞问题。

深度无命中像素始终为far3m，最终clamp至0.1–3m；这是相对handoff加噪后可为0m的显式适配。边缘差分不跨图边界。推扰使用有界速度赋值，不采用本机同名helper的速度累加语义。

## 契约与旧状态

checkpoint schema仍为2，wall migration_revision从5升为6，包含奖励权重、新噪声、初始化概率、随机化参数和动作范围。旧环境/旧17段AMP完整resume明确拒绝。后续正式新run从旧正式model_4200.pt显式weights-only warm-start：编码器、actor/critic、辅助头迁移，PPO/AMP/课程重建。yaw课程从0°重新开始。

[旧进程停止记录](stopped_run.json)：核对PID2348537命令行后于21:01 JST发送SIGINT，旧日志和checkpoint保留。验证模型只写本目录，不用于正式训练初始化。

## 验证

冻结命令：

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p 'test_carrybox*.py' -v
bash scripts/rsl_rl/validate_carrybox_handoff.sh
```

CPU覆盖奖励数值/门控、坐标平移、双向倾倒、动作覆盖、米域噪声/无命中/边界、恰好15帧冻结及reset幂等；真实仿真覆盖PhysX质量/摩擦/COM范围与不连乘、默认动作offset同步、PPO/AMP更新、旧契约拒绝、新契约恢复、无真值泄漏与导出。4096环境保持24步/迭代、PPO4 epochs×4 minibatches，完整AMP/辅助损失与所有遮挡，热身后每轮必须≤6秒。

尚未完成新的长训练，也没有独立拾箱成功率结论。

## 本次验收结果

[冻结测试回执](test_receipts_attempt1.json)两条均PASS；35项CPU测试通过。4环境3+2次完整PPO/AMP更新、实际物理参数审计、新runner恢复与JIT/ONNX导出通过。4096环境6+4次完整更新/恢复通过，舍去前2轮热身后8轮平均4.295秒、最慢4.318秒，达到6秒目标。新增传感器、全部奖励、原始50Hz遮挡、24步采样与4×4 PPO/AMP均开启。

[4环境结果](scale4/result.json) · [4096结果](scale4096/result.json) · [源码hash](source_hashes.json)

## 正式运行

21:08 JST启动PID2448113，`wall4_handoff_v6_amp15_20261014_210808`。当前状态以[启动与核验记录](launch.json)及实时日志为准。

```bash
tail -n 100 -F logs/rsl_rl/g1_carrybox_depth/walled4/handoff_v6_20261014_210808/train.log
```

正式核验见[formal_health.json](formal_health.json)：4096环境、clip9、19项奖励和仅策略权重迁移配置一致。当前早期回合较短，主要因姿态越限终止；运行与性能通过不代表收敛，仍需后续学习曲线及独立搬箱子成功率评估。
