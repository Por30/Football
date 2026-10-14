# AgileKickball-v3：球状态反馈策略

任务：`Template-Perceptual-Ball-AgileKickball-v3`；当前 revision：`state_feedback_20261006`。

本版重新以 v2 `v1_speed_only_20260925` 为基线，恢复相同的物理任务和课程，增加可进入动作决策的球状态反馈。默认从零训练，不加载 v2 权重。原 v2 代码、旧模型和旧日志保留。

旧 v3 `contact_outcome_20261003` 已完成 50000 轮，但训练表现弱于 v2：最后 1000 轮平均 episode 长度约 23.76 s 对 53.07 s，恢复发球比例约 81.03% 对 94.37%，最终课程球速上限约 2.19 m/s 对 6 m/s。旧辅助模块确实更新过；这些结果不能把差异归因于辅助，因为旧 v3 同时扩大了空间难度。原始审计见 [comparison.json](training_audit_20261006/comparison.json)。

## 本次改动

| 项目 | v2 | 新 v3 |
|---|---|---|
| 控制与部署输入 | 50 Hz，8 帧本体/深度历史 | 相同 |
| 当前球状态预测 | 深度 CNN → 6 维位置/速度，MSE 辅助 | 深度特征 + 本体历史 → 6 维均值和 6 维 log 标准差，Gaussian NLL 辅助 |
| 预测如何参与动作 | 通过共享 CNN 间接影响 | 增加置信度/可见性门控的动作修正分支，PPO 学习修正 |
| 原动作网络 | 992 → 512 → 256 → 256 → 29 | 保留；新增修正分支末层零初始化 |
| 最终发球距离 | 1.3–2.0 m | 相同，恢复 v2 范围 |
| 横向来球目标 | ±0.25 m | 相同，恢复 v2 范围 |
| 机器人/球离 anchor 边界 | 0.6 / 3.0 m | 相同 |
| 球速课程 | 起步 0.4–0.8 m/s，上限最多 6 m/s | 相同 |
| 奖励、PPO、AMP、恢复规则 | v2 设置 | 相同 |
| 未来后果辅助 | 无 | 移除旧 v3 的未来辅助 |

较宽的 3 m / ±0.35 m / 1.2 m 场景只保留在旧 Outcome 任务中。本轮先在 v2 分布上比较方法；不把降低旧 v3 难度后的改善当作创新有效的证据。

## 模块与约束

`StateFeedbackActorCritic` 将 864 维本体历史与 128 维深度编码拼接，使用 `992→128→12` 预测当前球状态分布。监督为机器人完整姿态坐标系下的球 XYZ，以及世界速度旋转到该坐标系后的 XYZ；速度不是减去机器人速度的相对速度。位置/速度分别除以 3 m / 6 m/s，log 标准差限制在 [-4,1]，Gaussian NLL 不含常数项，数值可以为负。

修正分支输入为本体历史加预测均值/log 标准差，网络 `876→128→64→29`。均值、log 标准差和门控在此分支 detach，防止 PPO 通过预测头操纵不确定性；PPO 仍训练主 actor、共享编码器和修正网络。NLL 只训练编码器/预测头，不直接更新动作网络。特权球真值仅用于训练监督及原 critic，部署无需真值。

米制深度中 `.1 < depth < 3−1e−5` 的像素视作可见球；历史由旧到新，最近可见程度为 `max(visible[t] × 0.8^age[t])`。门控为该值除以 `1 + mean(exp(logstd))`。全历史不可见时修正为零，原视觉策略继续工作。该规则对应当前球专用解析深度观测，不适用于任意实拍深度图；预测标准差尚未经过校准验证。

最终动作均值为 `原动作 + gate × 0.25 × tanh(修正网络输出)`。每维最大修正为 0.25 raw action，对应现有 0.25 rad/action 缩放下 0.0625 rad。仅修正网络末层置零，所以初始输出等于原主 actor，前面层仍可学习。

`StateFeedbackPPO` 使用单一当前状态 NLL 阶段替换原球状态 MSE 阶段，不叠加第二个辅助阶段。辅助系数 0.5、Adam 初始学习率 1e-3、每轮一遍/4 minibatch。每个 trial 监控完整策略动作在批内和固定最多 512 个样本上的 KL，上限 0.01；最多 7 次尝试，每次学习率乘 1/4。失败恢复编码器、预测头及 Adam 状态，整批跳过。因为预测头已经影响动作，禁止旧 head-only 回退。该 KL 是有限样本上的辅助阶段约束，不是所有状态或整个 PPO 更新的保证。

## 训练与日志

```bash
cd /home/cao/perceptual_ball
bash scripts/rsl_rl/train_agilekickball_v3.sh
```

脚本自动设置本机 Isaac 环境，正式默认：4096 环境、cuda:0、50000 迭代、seed 42、每轮 24 步，PPO 5 epoch / 4 minibatch，独立 scratch run。运行名为 `state_feedback_20261006_scratch`。当前后台实例的 PID、日志和首轮验证见 [launch.json](state_feedback_20261006/launch.json) 和 [verified_start.json](state_feedback_20261006/verified_start.json)；已有实例运行时不要重复执行启动命令。

TensorBoard 的 `Loss/state_feedback/` 记录 NLL、门控、预测标准差、修正动作幅度和累计接受的辅助批次数；`Loss/aux/` 记录接受/拒绝/跳过及阶段 KL。`Loss/ball/` 保留物理单位位置/速度误差，`AgileV3/` 保留课程和恢复指标。

NLL 和球状态误差是训练样本诊断，不能替代独立评测。课程速度上限也不是已经掌握的球速。新结构是否优于 v2，需要训练后以相同发球分布、交互预算和多个随机种子评估；拆分状态反馈、NLL 和门控的贡献还需要消融实验。本次实现和启动不代表已验证论文创新性。

## Checkpoint、导出与旧版本

新 checkpoint 保存 `state_feedback` 配置和累计辅助更新次数、辅助 Adam，以及 `agile_v3_state_feedback_curriculum` 课程。新旧 revision 不可互相 resume；配置/课程/辅助恢复状态检查发生在加载权重之前。正常续训使用同 revision 配置；推理加载不要求辅助优化器。课程在播放时冻结。

TorchScript/ONNX 包含完整 CNN、预测头、门控、原 actor 和修正分支，调用方提供同样顺序的本体/深度历史。验证使用非零修正分支，并比较动态批量输出，避免只验证初始零输出的空分支。

旧 v3 使用 `Template-Perceptual-Ball-AgileKickball-v3-Outcome`，指向归档的 `agilekickball_v3_outcome_env_cfg.py` 和 `mdp/agilekickball_v3_outcome.py`，仍可读取旧 `contact_outcome_20261003` checkpoint。旧源码快照和当时说明见 [before](state_feedback_20261006/before/)；原有 `outcome_20261003/`、`launch_20261003/` 和训练模型不覆盖。

## 验证

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_state_feedback.py
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py
bash scripts/rsl_rl/smoke_agilekickball_v3.sh
```

验证覆盖梯度路由、动作约束、NLL 单位和非有限值、完整参数/Adam 回退、checkpoint 预检查、非零分支导出、v2 物理行为及旧 Outcome 回归。真实 CPU 仿真检查训练/续训、课程冻结、几何边界和旧最终模型；GPU 检查使用正式 4096 环境及原 PPO 参数执行一次更新。证据保存在 [state_feedback_20261006](state_feedback_20261006/)，最终 PASS 以 receipts.json 为准。短测只能确认可运行性，不能证明长期性能。
