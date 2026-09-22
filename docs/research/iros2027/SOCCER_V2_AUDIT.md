# G1 Soccer v2 改进审查

日期：2026-09-19。平台：用户已确认 G1。范围：当前工作树 `Template-Perceptual-Ball-Soccer-v2` 及其共享实现。

结论：已有深度 PPO、辅助回归、双 AMP/critic、噪声与随机化，但应先修复训练信号与测量定义，再训练稳定回踢，最后研究高速机制。发现的问题不能单独解释用户报告的全部失衡；本轮没有运行仿真或训练。

## 证据与复现

读取实际源码、本地 Isaac Lab、ball 环境中的 RSL-RL 3.0.1、两段 `.pt` 动作、Soccer v2 checkpoint 和 TensorBoard。CPU 探针严格加载 v2 `2026-09-18_18-50-26/model_2.pt` 成功。

复现命令：

```bash
/home/cao/ENTER/envs/ball/bin/python docs/research/iros2027/audit_soccer_cpu.py
```

结果：`audit_soccer_cpu_results.json`；执行回执：`audit_test_receipts.json`。包含文件哈希、数值与构造反例。探针通过表示本报告所述缺陷在当前源码下被复现，不表示策略通过性能测试。AST 提取只隔离相关源码计算，替代的场景与四元数函数仅用于明确的 identity-orientation 构造状态。

## A. 应先修复的确定问题

### A1 / P0：AMP 专家与策略的高度特征公式不一致

位置：`mdp/amp.py:76` 与 `mdp/amp.py:148`。

策略侧为 `min(root_z - ee_z)`，等于 `root_z - max(ee_z)`；专家侧为 `root_z - min(ee_z)`。末端集合包括头、手和脚，因此两侧测的不是同一个量。

将本地参考动作的同一批 root/末端位置分别送入两个源码表达式：

| 动作 | 策略侧范围 / m | 专家侧范围 / m |
|---|---:|---:|
| kick_left，498 帧 | -0.2798 至 -0.0108 | 0.6404 至 0.7410 |
| kick_right，589 帧 | -0.2798 至 -0.0090 | 0.6493 至 0.7409 |

影响：即使身体完全复现专家动作，该维也明显不同，判别器可利用这个捷径分类，破坏动作先验的训练目的。不能据此声称实际 AMP 完全无效，但该不变量必须先修。

建议：共享同一特征构建函数，统一高度、关节/末端顺序、坐标系与时间采样；以同一动作回放验证 60 维逐维一致。动作文件带 joint_names，但缺少末端名元数据；当前 `SceneEntityCfg` 默认不保留输入名称顺序，需额外核对而不能直接认定已错序。修复后旧 checkpoint 的策略仍可评测，但不能与修复后的训练当成同一基线。

### A2 / P0：episode 终止后的新观测被用于上一条 transition 的 AMP 奖励

位置：`rsl_rl_extensions/algorithm.py:191`；本地 `ManagerBasedRLEnv.step` 先 reset 再生成返回观测。

`SkillAMPPPO.process_env_step` 无论 done 与否都对返回的 `obs['amp']` 打分。对终止环境，这已经是新 episode 的姿态和历史，而 task reward 来自结束前的状态。CPU spy 用 done=1、reset feature=0.8、terminal feature=0.2，证实收到 0.12 的混合 AMP 分量，terminal feature 未被消费。

建议：在 reset 前保存终止 AMP window 及一致的 skill label，按 done mask 使用；终止窗口写入历史时避免重复推进 buffer。定义并测试路由 label 在 transition 中的采样时刻，避免击球后球位置改变而用另一技能给整段挥脚评分。

另一个边界：本地 RSL-RL 3.0.1 timeout bootstrap 使用 `transition.values`（动作前状态值），没有读取 terminal critic observation。若要求精确使用结束状态做 bootstrap，应同时补 terminal critic 流程；不能误述为“当前已使用 reset 后 critic bootstrap”。

### A3 / P1：checkpoint 不保存 AMP 与辅助优化器

位置：`rsl_rl_extensions/runner.py:18` 仅重写构造算法，没有重写 save/load；继承的 RSL-RL save/load 只处理 policy/PPO 和可选 RND。

实际 v2 checkpoint 只有 `model_state_dict`、`optimizer_state_dict`、`iter`、`infos`；没有判别器、AMP optimizer、ball_aux_optimizer 状态。球辅助头本身属于 policy，因此其权重是保存的。

影响：恢复训练时 actor/critic 回到 checkpoint，判别器重新初始化，奖励函数和额外优化器历史不连续。

建议：保存/加载三个训练分支、版本与必要归一化状态；用 round-trip 验证权重、优化器与同一输入 AMP reward 一致。若追求逐步精确续训还需处理随机数和环境状态。旧 checkpoint 缺 AMP 时明确记录重新初始化，不能宣称等价续训。

### A4 / P1：脚球成功判定与回球奖励的有效接触条件不一致

位置：`mdp/kickball_state.py:245–279`、`mdp/rewards.py:108`。

v2 对成功 bonus 加了脚距限制，但 dense return speed 先由任意球速突变开放，未受脚距过滤。另一个问题是脚距仅为 XY，脚的高度完全不参与。

两个离线反例：

- 两只脚都远离球，球速发生向外突变：success=false，但 return speed=1 m/s，仍会给正回球奖励。
- 脚在球正上方 0.89 m：XY 距离为零，配合球速突变时 success=true。

这是判定逻辑的构造反例，不是测得的物理误判频率。建议统一 valid_strike，用脚球过滤接触/子步接触记录确认物体交互；若暂用代理，至少同时使用 3D 几何、相对运动方向和高度条件，并明确其局限。球重发时重置 prev velocity/事件脉冲，避免把 teleport 当作物理速度突变；不能断言当前重发一定产生 success，因为向外速度门槛还在。

### A5 / P1（部署前必修）：play 的导出只带 actor MLP，漏掉深度 CNN

位置：`scripts/rsl_rl/play.py` 的 `export_policy_as_jit/onnx` 调用；`rsl_rl_extensions/modules.py:194`；本地 `isaaclab_rl/rsl_rl/exporter.py`。

官方通用 exporter 只复制 `policy.actor`。本项目 actor 的输入是 864 维本体历史 + 128 维深度 latent，即 992 维；完整推理还需要 CNN、v2 frame difference 与拼接。

CPU 检查：导出 wrapper 没有 perception_encoder；输入预先算好的 992 维特征可匹配原模型输出，但 11232 维原始展开观测会报矩阵维度错误。仿真 play 调用 `act_inference` 的路径仍包含 CNN，不能混为一谈。

建议：独立导出完整推理 wrapper，接收深度栈与本体历史，明确历史管理、关节顺序与动作缩放的外部契约，并验证 eager/JIT/ONNX 数值等价。

## B. 训练稳定性需要进一步量化的地方

### B1：判别器尺度和辅助更新的稳定性

`rsl_rl_extensions/amp.py:28–35` 将所有层权重初始化为 U(-1,1)，未按 fan-in 缩放，也没有特征归一化。最后一个 v2 短跑记录的 `Loss/amp` 是 1,244,993 → 589,254 → 417,530。该记录仅 3 次 iteration，不能推断收敛或将大 loss 全归因于 A1。

建议在修复特征后分项记录 expert/policy logits、梯度惩罚、AMP reward 为零的比例、每个技能的数据量，再比较初始化/共享归一化设置。`_update_amp` 各技能 loss 为 mean 后直接相加，注释所说的“按样本量占比贡献”并未实现；若希望等权就修正文档，若希望样本加权就显式乘数量占比。

`algorithm.py:79–98` 在 PPO 更新后再用独立 Adam 更新共享 CNN，额外更新没有 PPO KL 检查。并非仅凭这一点就能判为错误，但应记录辅助更新前后 action KL、梯度范数和任务表现；必要时采用联合 loss、控制辅助更新比例或添加行为约束。

### B2：左右技能跨 episode 延续，挥脚中也可能切换

`mdp/kickball_state.py:131–135, 215–236` 的 EMA 与 label 在 reset 时不清理；新局开头的路由受上一局来球影响。CPU probe 已确认。每个 tick 都更新 label，故一次动作窗口可能经历技能变化。

建议从新发球初始化 EMA；由预计拦截位置和支撑状态决定候选踢球脚，进入明确的准备/挥脚阶段后锁定，再在恢复或下一 serve 解锁。先比较简单、可追溯的路由规则；不把改双 critic 当作研究贡献。

### B3：随机化与关节偏置的语义需校正

v2 一开始同时启用深度噪声、摩擦、±0.05 m 质心偏移和每 1–3 s 推扰。短跑日志不够判断这些是否过强。建议先在简单条件下建立站立/回踢性能，再逐项增加并测退化；不要在新方法和基线之间采用不同随机化难度。

`events.py` startup 改 default_joint_pos，但本地 `JointPositionAction.__init__` 在 startup 前已 clone 了默认位置到 `_offset`。因此观测/重置默认位和动作中心不一致，和 helper 注释“共同改变动作零点”的描述不符。先明确希望模拟传感器零偏、执行器偏置还是姿态差异，再从单一标定定义实现并验证。

动作 clip 在实际 agent.yaml 为 null，执行器 limits 在 Python 配置为 null 并不等于无穷，可能来自 USD。需要导出实际 joint/effort/velocity limits、量化饱和率；本轮未核实实际限幅，不能宣称执行器已饱和。

## C. 最贴近用户目标的任务改进

### C1：成功从“踢走”扩展为“有效回传并恢复”

当前 success 当步即奖励，未检查之后是否跌倒；没有 RECOVER/READY 阶段，也没有目标区域。`stand_task` 全程要求低 base 速度和接近 anchor，既可能压制合理重心转移，也没有专门强化接触后的恢复。

建议新增清晰的 PREPARE → CONTACT → RECOVER → READY 状态，以 valid contact 给较小即时反馈，以进入目标区域且恢复完成给回合奖励。恢复条件用姿态、root/关节速度、支撑与持续时间组合定义；不固定要求身体在整个挥脚期间静止。发下一球保留外部预设节奏或恢复超时上限，避免策略通过拖延 READY 回避困难来球。首先评测恢复时间与连续回合，不用简单增大站立奖励代替。

添加指定区域时，目标命令也必须通过部署时可获得的输入提供给 actor；仅在奖励中随机换目标会制造不可观测任务。

### C2：给感知训练补上相机自运动和时间信息

`mdp/perception.py:105–126` 只对球做解析 ray-sphere，没有地面、自遮挡；当前每控制步更新，无异步帧、实际延迟或观测年龄。添加像素噪声并不能覆盖这些差异。

`modules.py:226` 的辅助头仅看 depth latent，却回归 root 坐标下球的位置与速度。相机随躯干/腰运动时，深度变化同时来自球与相机，纯球背景下容易混淆；actor 后面融合 proprio 并不能让这个独立辅助头直接利用 proprio。

建议优先将辅助感知与本体/动作历史融合，加入时间戳、观测年龄与有效标记，构造延迟/遮挡测试。目标相机条件明确后，补地面与自遮挡，或用真实深度回放量化解析图差距。没有证据前不直接提高网络规模。

### C3：高速目标应由准备时间和完整成功率推动

当前 SERVE_SPEED_RANGE 固定为 0.4–0.8 m/s，距离固定 1.3–2.0 m。提高速度同时缩短准备时间，会混淆接触动力学与反应能力。

建议把来球速度、首次可见时间、延迟和初始支撑状态分开控制；课程进阶依据有效接触 + 回传 + 恢复的联合成功率。先跑低速可信基线，再逐级扫速。两段 AMP 动作仅作人体先验；高速下是否约束过强，应在上述错误修正后再消融时间尺度/权重。

主要图：实际到达速度 × 可用准备时间的完整回合成功率；接触时刻误差 × 恢复成功率。分母保留全部发球，单独记录无观测、未接触、非脚接触、错误方向、接触前跌倒、接触后跌倒和恢复超时。

## 建议实施顺序

1. 修 A1–A3，补特征一致性、终止 transition、训练状态 round-trip 检查。
2. 修 A4，建立每次发球的有效接触与失败分解；加 AMP 分项日志，确认奖励可学习。
3. 实现 C1 的恢复与完整回合指标，建立稳定低速基线；v2 尚只有短跑产物，先完成足够训练再谈优劣。
4. 对 C2 做最小感知融合与延迟诊断，再研究身体条件的接触时间窗口；保持对照训练预算与奖励一致。
5. 部署前完成 A5、实际 actuator/动作限幅与机载延迟验证。

本次改动仅为审查文档、CPU 诊断与 G1 平台记录；未修训练代码，未新增训练 checkpoint，未取得实机或性能结论。
