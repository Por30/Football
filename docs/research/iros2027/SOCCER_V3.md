# G1 Soccer v3

任务 ID：`Template-Perceptual-Ball-Soccer-v3`。平台为本项目 29 关节 G1。v3 将脚球接触、定向回球和站稳恢复串成一轮，训练基础设施已通过 CPU 回归与小规模 IsaacLab 验证；尚未完成策略训练或性能评估。

## 启动训练

在本机执行；脚本已配置 ball Python、Isaac Sim 和 IsaacLab 路径，无需手动激活 conda：

```bash
cd /home/cao/perceptual_ball
bash scripts/rsl_rl/train_soccer_v3.sh --max_iterations 10000 --run_name v3_baseline
```

默认 headless、CUDA:0、256 个并行环境、seed 42、TensorBoard；可追加 `--num_envs 512` 等覆盖默认值。配置类默认 1024，启动脚本使用 256 作为较小的初始规模；未测 GPU 大批量内存和吞吐。日志与模型写入 `logs/rsl_rl/g1_soccer_v3/<时间>_v3_baseline/`。10000 次迭代是初次运行预算，并非收敛保证。

恢复一个本版本的训练：

```bash
bash scripts/rsl_rl/train_soccer_v3.sh --resume \
  --load_run '<完整运行目录名>' --checkpoint model_1000.pt \
  --max_iterations 10000 --run_name v3_resume
```

恢复时迭代数表示本次额外执行的次数。旧 v0/v2 checkpoint 缺少完整 AMP 训练状态，且 v3 输入/辅助头维度变化，不能直接当作 v3 完整恢复；本轮未改写旧 checkpoint。保存包含策略、PPO、判别器及其统计量、AMP/辅助优化器和 CPU torch RNG。环境瞬时状态、课程计数及 CUDA RNG 不在保存范围，恢复不是逐步完全复现。

## 一轮的定义

发球后进入 PREPARE，左右脚选择在发球时确定并锁定。本版本基础来球速度为 0.4–0.8 m/s。

1. 两个独立脚部传感器各自过滤球，覆盖全部 4 个物理子步；有效脚触球后进入 RECOVER。球对机器人整体的传感器用于排除非脚接触，同步出现的摔倒优先记失败。
2. 回球必须穿过距离发球锚点 2 m 的目标平面，目标方向随机偏航 ±0.25 rad；横向误差不超过 0.6 m、球速 0.4–4 m/s、球高小于 0.5 m。
3. 接触后 3 s 内满足目标并连续站稳 0.3 s，才记完整成功。站稳要求：重力投影 XY 范数 <0.15、水平基座速度 <0.3 m/s、角速度 <0.6 rad/s、根高度 >0.65 m、关节速度 RMS <2 rad/s，且双脚有支撑力。
4. 重复触球、非脚碰球、出界目标、恢复超时、漏球和环境终止均独立计数为失败。每个发球仅结算一次，重置不会隐藏失败；结算后等待 0.4 s 再发球。

球侧过滤器显式列出当前 G1 的 28 个碰撞部件。实测 Isaac Sim 4.5 的 `Robot/.*` 分组过滤会返回空力列，不能仅检查张量形状判断其可用。smoke 同时核对实际 USD 的碰撞部件集合，并要求真实脚触球进入 RECOVER；更换资产后必须更新过滤集合并重新验证。

训练控制周期 20 ms，物理周期 5 ms。接触、完整成功和失败的原始单次奖励分别为 +0.2、+2、−0.4，之后仍经 AMP/task 混合，不能把配置权重直接当作单次奖励。

观察 `Soccer/served`、`settled`、`pending`、`contact`、`success` 和各失败原因；始终应有 `served = settled + pending`。`success_per_served` 包含未结算发球，属于累计在线诊断；正式成功率需要固定条件、完整结算的独立评估。`mean_recovery_s` 是成功轮次从接触到完整结算的均值，包含等待球过目标平面的时间。

## 修复与新增

| 路径 | v3 行为 |
| --- | --- |
| AMP | 专家/在线共用 60D 特征布局和高度定义；显式末端顺序；参考统计归一化、小幅输出层初始化、独立梯度裁剪 |
| 终止处理 | reset 前保存真实 terminal AMP/critic；timeout 使用 terminal value 补一次；skill 使用动作发生时的路由 |
| 训练更新 | 各 skill 判别器损失按样本比例加权；辅助回归更新约束动作 KL，超阈值恢复参数及 Adam 状态 |
| checkpoint | 保存/恢复 AMP、PPO、辅助优化器；缺失训练状态时禁止静默完整恢复 |
| 接触与奖励 | v3 使用过滤的物理接触；旧任务修正 3D 距离代理和 dense 回球奖励门控；同步默认关节偏置与 action offset |
| 恢复任务 | 定向目标、完整回合状态机、持续站稳、失败原因和发球分母 |
| 感知 | 25 Hz 采样、0–40 ms 传输延迟、5% 丢帧、帧龄/有效位；加入地面及近似身体遮挡；辅助头融合本体感知 |
| 导出 | TorchScript/ONNX 包含深度 CNN 和 actor；manifest 记录输入顺序、深度历史顺序及动作后处理 |

深度仍是解析合成传感器，身体由半径 6 cm 球体代理；没有真实相机噪声标定或网格级遮挡。重复帧和采样间隔可能让帧龄超过传输延迟。随机推力关闭，躯干 COM 扰动降至 ±1 cm；这些设置只构成初始训练条件。

速度课程已实现，但默认 `max_serve_speed=0.8` 不自动扩大难度。若另行启用更高上限，可在启动命令后追加 `env.events.setup_kickball_state.params.max_serve_speed=2.0`；每累计至少 200 个结算发球后，根据最近完整成功比例调上界，每次 0.1 m/s。当前没有高速可行性的证据。

## 验证与文件入口

冻结命令及绑定回执见 `v3_test_receipts.json`。CPU 的 10 项测试覆盖参考特征、状态边界、terminal/timeout、辅助 KL 回退、保存恢复、JIT/ONNX 数值一致性和传感时序。真实仿真为 CPU、2 环境、小规模 rollout 和 1 次 PPO 更新；详见 `validation/smoke_v3.json`。两个动作片段的末端 FK 最大误差低于 1 微米，满足预设 3 mm 容差。

```bash
/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_soccer_v3.py
bash scripts/rsl_rl/smoke_soccer_v3.sh
```

`validation/smoke_model.pt` 仅是流程验证产物，不是训练好的踢球策略。历史 `audit_soccer_cpu.py` 的断言用于复现旧缺陷，修复后不作为正确性验收；请使用新测试。

任务配置：`source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/soccer_v3_env_cfg.py`；状态机：同目录 `mdp/soccer_v3.py`；交接：`agent/handoff/g1-soccer-v3.md`。下一步先训练低速基线并检查失败分布，再确定面向 IROS 2027 的实验方案与科学贡献。
