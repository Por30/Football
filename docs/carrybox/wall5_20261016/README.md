# Wall5：依据 X2/G1 差异文档实施 AMP 阶段 A

2026-10-16：新增独立任务 `Template-Perceptual-Ball-CarryBox-Walled5-v0`，继承当前 wall4 revision8 的完整物理任务，落实 [`x2g1differ.md`](../../../x2g1differ.md) 第6节“阶段A”的P0组。实现、50项CPU回归和4环境3轮＋恢复1轮短测通过。**未启动wall5正式训练，未验证长期收敛或4096环境速度。** 12:35 JST只读核对原wall4 PID2660033仍在运行，本次未停止、重启或切换它。

## Wall4 与 Wall5 的实际区别

以下wall4指当前G1 revision8，不是差异文档部分日志引用的旧revision6。

| 项目 | Wall4 | Wall5 |
|---|---|---|
| 正式目录 | `logs/rsl_rl/g1_carrybox_depth/walled4/` | `logs/rsl_rl/g1_carrybox_depth/walled5/`（尚无正式run） |
| 每步混合奖励 | 有效窗口时 `0.75*r_task + 0.01*style`；无效窗口给完整 `r_task` | 每个transition均 `0.75*r_task + 0.125*style` |
| AMP时间尺度 | `0.25 * dt(0.02) * 2 * style` | `0.25 * 0.5 * style`，不再乘dt；环境任务奖励仍由奖励管理器乘dt |
| AMP单帧 | 关节角29＋关节速度29＋重力3＋root角速度3＝64 | 关节角29＋重力3＋root角速度3＝35 |
| D输入 | 10×64＝640 | 10×35＝350，在线、专家、terminal一致 |
| D输入预处理 | 专家mean/std，std下限0.1，再截断±10 | 原始物理量，无标准化、无输入截断 |
| D优化 | 独立Adam，lr `1e-4`，无weight decay | 独立Adam，lr `5e-5`；trunk decay `1e-3`，输出层 `0.1` |
| reset后AMP窗口 | 首帧填充，但前8个transition不参与奖励/D更新 | 复用首帧填充，从第1个transition参与奖励和D更新 |
| `Skill/*_valid_amp_steps` | 每个完成回合 `max(length-8,0)` | 每个完成回合全部实际transition |
| 奖励日志 | style、valid fraction及环境原始奖励 | 新增原始任务、加权任务、AMP和混合后的每步均值 |
| checkpoint | 外层schema2，环境revision8，AMP配置schema1 | 外层schema2，环境revision9，AMP配置schema2；完整恢复不能混用 |

AMP奖励上限从0.01变为0.125，即12.5倍；这不是保证实际奖励也提高12.5倍，实际值仍取决于D的style分数。`style = max(0, 1 - 0.25*(D-1)^2)`保持不变。

D仍为350→512→256→1、ReLU；沿用Kaiming trunk/输出层U[-0.01,0.01]初始化、LSGAN与系数0.5的专家梯度惩罚、D梯度范数裁剪10。与X2共享PPO自适应优化器、无D梯度裁剪的实现仍有区别，本次按文档允许的独立低学习率方案实现。P0是一组AMP修订，不构成某个单因素已经解决收敛问题的证据。

## 保留的任务与观测

场景仍是1面墙＋3个圆柱，G1 29关节位置控制，200Hz仿真、50Hz策略，20秒上限。寻找箱子、接近、双手拾起并保持；不增加搬运目的地或放下流程。保留G1实际头部COM、关节硬限制、RSI脚底5mm接地修复及全部终止条件。

- actor和critic：同样的372维本体历史（4×93）＋4×27×48深度。仍共享128维深度CNN，再经各自[256,128] MLP；critic没有特权输入。
- 深度：现有G1 torso挂载、48×27、58°垂直FOV、0.1–3m光轴深度，Warp与地面、箱子、平台、墙、3圆柱及机器人可视网格求最近交点。保留身体/障碍遮挡、噪声、延迟、冻结和相机安装扰动。此轮没有修改相机几何或宣称补做了实机光心标定。
- 辅助监督：9维相机系箱子xyz＋rot6d，D4对称位姿损失系数0.5；标签与深度时序配对，只进入监督。
- AMP：350维只进入判别器与训练奖励，不进入actor/critic。原始数据仍为`assets/motions/findbox/`的15段；文件、manifest、采样概率40/40/20、60→50Hz插值均不变。去掉的是D的关节速度特征，RSI的关节/基座初始化速度仍保留。
- PPO：固定lr `3e-4`，4 epochs×4 minibatches、24步/轮、entropy `0.001`、初始std `0.2`，与wall4相同。
- RSI：loco/pickup/hold仍为60/30/10%；搜索概率2%、yaw分段课程、推扰课程和物理奖励权重均不变。

IsaacLab CircularBuffer在reset后的首次append会重复当前新回合帧填满10帧；不保留上回合历史，不复制X2重复append行为。done transition使用reset前terminal窗口，下一步才使用新回合首帧。4环境测试确认了错开reset及存活环境的历史只推进一次。

## 文档中尚未采用的建议

本轮按阶段A只改P0，便于先检验AMP修订。以下不是已实现功能：

| 建议 | 当前处理 |
|---|---|
| P1 特权critic / X2含箱子真值AMP | 不采用，遵守仓库“策略/价值只用深度本体、AMP纯本体”约束；独立深度critic可后续评估 |
| P1 adaptive PPO、5帧历史、大MLP/5×5 CNN、std0.5、entropy0.01 | 未改，保留wall4作为对照；不是仅把学习率调高 |
| P1 去转身pickup和原地转身专家片段 | 未加工或替换用户15段数据；需单独核验重定向、裁切与manifest |
| P2 3D到箱距离、G1站立/头高阈值、叠加push | 未改，仍沿用wall4；身高建议值需要数据统计，不能当作标定值直接抄入 |
| 文档建议先关闭pickup RSI | 未改，当前60/30/10保持；支撑台估计问题留作后续独立排查 |
| 可选value平滑损失 | 未加入 |

差异文档的训练失败分析部分取自旧revision6，而当前wall4为revision8；因此这轮是依据代码差异新增对照任务，不能声称已证明当前wall4不收敛的唯一原因。

## 验证与工件

- [CPU日志](cpu.log)：50项PASS，包含原44项与新6项；覆盖真实15段特征投影、RSI数据不变、无归一化/截断、优化器参数组、奖励0/1端点及dt不变性、首步和短终止窗口、PPO/D实际更新、双向恢复拒绝、导出和旧wall行为。
- [4环境结果](result.json)、[日志](smoke.log)：生产24步×4epochs×4minibatches；3轮更新＋新runner恢复后1轮；6次强制/自然reset，实际history验证；JIT输出与策略一致、ONNX checker通过。静态配置比较确认环境仅变体身份和AMP观测函数不同，runner仅身份、AMP scale/lr/算法类不同。
- [测试回执](receipts.json)。初次CPU测试仅测试脚本导出比较缺少`inference_mode`，已修；[初次回执](receipts_initial.json)保留，生产代码未因该失败修改。GPU通过后只重跑失败的CPU命令。
- `model.pt`、`train/`、`resumed/`和`export/`均为本页下的短测工件，不能当正式模型或拾箱成功率证据。
- 本次小规模测试与既有wall4并存，耗时不能外推到4096环境；尚未复测wall5≤6秒/轮。

新增源码：[`carrybox_wall5.py`](../../../source/perceptual_ball/perceptual_ball/carrybox_wall5.py)负责专家特征投影；[`rsl_rl_extensions/carrybox_wall5.py`](../../../source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py)负责AMP和runner；[`carrybox_wall5_env_cfg.py`](../../../source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py)与[`mdp/carrybox_wall5.py`](../../../source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py)负责配置/terminal/schema。

共用文件只增加Wall5注册及train/play分支、允许yaw课程枚举walled5、按变体计算有效AMP步数（旧任务默认仍扣8步）。没有修改wall4奖励公式、PPO实现、数据、相机或足球训练接口。

## 后续启动命令（本轮未执行）

释放正式训练资源并完成wall5正式规模计时后，可从头启动：

```bash
cd /home/cao/perceptual_ball
CARRYBOX_VARIANT=5 bash scripts/rsl_rl/train_carrybox_walled.sh \
  --num_envs 4096 --max_iterations 40000 \
  --run_name wall5_amp_stage_a
```

不带`--resume`或warm-start，使用独立walled5目录。正常完整恢复要求同wall5环境/AMP契约，旧wall4 checkpoint会被拒绝。虽然同形actor/critic允许显式policy-only迁移，但它不恢复AMP/PPO状态，本次没有使用或默认启用。

长训需按技能监控loco实际寿命、tipped比例、D expert/policy loss、style及`Reward/amp_per_step`；`Reward/mixed_per_step`是timeout价值bootstrap前真正混合的每步奖励，runner原来的`Mean reward`仍来自环境原始任务奖励，二者不要混用。是否学会从地面完整拾箱，仍需独立loco起点评估。
