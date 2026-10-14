# AgileKickball-v3：短时后果预测辅助的直接控制

任务：`Template-Perceptual-Ball-AgileKickball-v3`。当前 revision：`contact_outcome_20261003`。
以 v2 `v1_speed_only_20260925` 的代码为基线，在此前 v3 空间扩展上增加训练期预测辅助；默认从零训练，不加载 v2 权重。v2 任务及其已有 checkpoint 保持原行为。

## 正式训练

在当前机器直接运行，无需先手动激活 conda：

```bash
cd /home/cao/perceptual_ball
bash scripts/rsl_rl/train_agilekickball_v3.sh
```

脚本设置本机 Isaac Sim/Isaac Lab 环境，然后执行：

```bash
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-AgileKickball-v3 \
  --num_envs 4096 --device cuda:0 --headless \
  --max_iterations 50000 --seed 42 \
  --run_name contact_outcome_20261003_scratch
```

日志和 checkpoint：`logs/rsl_rl/agilekickball_v3/<时间戳>_contact_outcome_20261003_scratch/`。本次开发只运行有限验证，没有启动正式长训。已用 16 环境完成两次 GPU 更新，并用正式 4096 环境、24 步 rollout、5 epoch/4 minibatch 完成一次完整更新（98304 transitions），未出现 OOM；单次更新不代表长期稳定性或收敛表现。

辅助关闭的消融命令（相同 v3 空间分布、actor 和奖励）：

```bash
bash scripts/rsl_rl/train_agilekickball_v3.sh \
  --run_name outcome_off_20261003_scratch agent.algorithm.outcome_aux_coef=0.0
```

纯 v2 与完整 v3 同时存在空间分布差异，不能仅凭两者性能差宣称辅助机制有效。上述 outcome-off 是更直接的机制对照；仍需多种子、相同评测分布和训练交互预算。

## 具体改动

| 项目 | v2 | 当前 v3 |
|---|---|---|
| 控制 | 50 Hz 直接关节动作 | 相同；不跟踪参考轨迹 |
| Actor 输入 | 8 帧本体历史 + 深度历史 | 相同，无额外真值输入 |
| Critic / PPO / AMP / 奖励 | 当前 v2 设置 | 相同 |
| 当前球状态辅助 | 预测位置和速度 | 保留 |
| 新辅助 | 无 | 当前观测和动作 → 8 控制步后的球平面速度、身体倾斜/高度，以及窗口内 kick proxy |
| 最终发球距离 | 1.3–2.0 m | 1.3–3.0 m |
| 横向目标 | ±0.25 m | 从 ±0.25 m 渐进到 ±0.35 m |
| 机器人离 anchor 终止半径 | 0.6 m | 1.2 m |
| 球离 anchor 结束半径 | 3.0 m | 4.0 m |
| 球速课程 | 起步 0.4–0.8 m/s；上限逐步到 6 m/s | 相同 |

空间范围是之前已经指定的 v3 行为，本次新增方法主要是 `OutcomeActorCritic` / `ContactOutcomePPO`。共享原深度 CNN，辅助头输入为 actor 特征 992 维加当前动作 29 维，MLP 为 `1021→128→64→6`。辅助更新只优化深度编码器及辅助头；部署继续使用原 CNN 和动作 MLP，辅助头不参加 `act_inference`，导出时也不包含该头。

## 标签、损失与边界

- 默认预测跨度 8 步，即 0.16 s；正式 rollout 长 24 步。`obs[t]` 是动作 `a[t]` 前的状态，目标来自 `obs[t+8]`。每段尾部 8 个源时刻没有完整未来，跳过。
- 球速预测目标是未来世界平面速度在**源时刻机器人 yaw 坐标系**下的分量，单位 m/s；身体目标为未来身体坐标中的 projected gravity XY 及离环境地面的 root 高度 m。
- 第六项是 `successes[t+8] > successes[t]`，沿用 v2 的运动学踢球代理计数。它不是真实接触传感器标签，不表示任意碰撞，更不等于有效回球且保持稳定的联合成功。
- 当前动作之后继续执行 rollout 策略，因此这是当前策略下的统计预测，不是反事实动作评价器；本版未实现候选动作搜索、世界模型规划或教师蒸馏。
- `outcome_state` 是独立、无历史、无噪声、float64 的训练真值组；只用于造标签，不进入 actor/critic。观测函数只读，不推进状态机。
- 完整窗口内必须无 done、无发球 ID 变化；源时刻球必须 active。重置和重新发球不会串入标签。源输入/目标非有限时排除并计数；无有效样本时明确跳过。终止前窗口因此不用于辅助训练，本版没有学习跌倒风险分类器。
- 球速除以 6，gravity 保持原尺度，高度转换为 `(h−0.8)/0.2`。回归使用 Smooth L1；总损失为 `0.5×ball + 0.5×body + 0.2×proxy_BCE`，整体辅助系数默认 0.1。
- proxy BCE 的正样本权重按抽样批总体负/正比裁剪到 [1,20]；输出不能视作已校准接触概率。
- 独立 Adam 学习率 1e-4。每次 PPO 更新后最多均匀抽取 8192 个有效样本，一遍，每批最多 2048；可设置 `agent.algorithm.outcome_aux_coef=0.0` 关闭。
- outcome 阶段监控批内和固定样本集上的动作均值 KL，默认上限 0.005。最多四次尝试，学习率依次缩小为 1、1/4、1/16、1/64；失败恢复参数及 Adam 动量，再只训练头。该 KL 仅约束 outcome 阶段，不是 PPO 与所有辅助更新的总漂移上界。
- 当前实现只支持单 GPU、非递归策略；多 GPU 会明确报错。

TensorBoard 中 `Loss/outcome/` 下记录有效/抽样数量、proxy 正例比例、球速向量 RMSE（m/s）、gravity XY 向量 RMSE、高度 RMSE（m）、Brier 误差、encoder 更新次数、回退次数与阶段 KL。预测误差在各批更新前统计，仅作训练诊断，不是独立验证集表现。`AgileV3/` 保留课程、恢复及发球指标。

## 空间与课程语义

距离和横向偏移使用平均来球曝光 `E`：`p=min(E/60000,1)`，距离 `[0.5+0.8p, 0.7+2.3p]` m，横向偏移 `±(0.25+0.1p)` m。距离从 episode 初始站位 anchor 测量；偏移沿发球点到 anchor 方向的垂线，不是固定世界 Y。方位角保持相对初始朝向 ±0.35 rad。anchor 不跟随机器人。

球速继续由 v2 近期恢复发球表现控制扩展，最高均匀采样 0.4–6 m/s；课程上限不代表已掌握该速度。恢复仍要求连续稳定 0.3 s、最少等待 0.4 s，5 s 恢复超时结束 episode；下一球仍等待恢复，没有改变发球节奏。

## Checkpoint 与验证

模型包含辅助头；新增 checkpoint 字段 `contact_outcome` 保存辅助配置和 Adam 状态。课程键沿用 `agile_v3_wide_serve_curriculum`，但 revision 已变。旧 v2、旧空间版 v3 均不能直接 resume；缺失辅助恢复状态或配置不匹配会在模型加载前拒绝。新 v3 同配置可恢复，播放时课程仍冻结；关闭辅助的消融存档需用相同系数配置加载。

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_contact_outcome.py
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py
bash scripts/rsl_rl/smoke_agilekickball_v3.sh
```

当前验证结果保存于 `outcome_20261003/`。测试覆盖时间和坐标对齐、done/再发球边界、特权信息隔离、真实 PPO/辅助反向传播、KL 回退及优化器恢复；仿真检查原空间边界和课程冻结/恢复，并调用正式启动脚本进行 16 环境、2 次迭代的 GPU 验证。额外 4096 环境规模检查记录在 `scale_smoke.json`，有效窗口 62685 个、抽取 8192 个、共享编码器更新 4 批。有限 smoke 只验证可运行性，不证明比 v2 更好。

历史 `validation/` 属于 2026-09-27 ±0.75 m 空间版本，`aim035_20260928/` 属于 ±0.35 m 调整；历史记录未覆盖。本次修改前文件存于 `outcome_20261003/before/`。
