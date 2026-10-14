# 项目看板

2026-10-14：FB-006补充实时深度窗口，MuJoCo图形启动默认启用；真实桌面双窗口短测通过，未改变策略/训练。

2026-10-14：FB-006足球MuJoCo深度可视化完成，[12秒策略输入视频](../docs/agilekickball_v4/sim2sim_20261014/depth_visualization/depth.mp4)及原始深度已保存；未改变控制或训练。

2026-10-14更新：FB-004足球MuJoCo部署接口实现完成，官方仓库同步、G1编译及8项CPU/500步闭环通过；FB-005接球回传稳定迁移待完成，60秒训练步长诊断出现1次跌倒。未启动训练或真机。[s2s记录](../docs/agilekickball_v4/sim2sim_20261014/README.md)。

更新时间：2026-10-14（wall4奖励修复后重新启动，Asia/Tokyo）。项目管理员：用户；具体开发与验证结果写入对应项目记录。

本仓库维护两个独立任务，共享G1资产、Isaac Lab运行环境和通用训练入口。`findbox`与`football`是并列项目标识；源码和已有产物保留稳定路径，由各项目入口统一索引。

## 并列项目入口

| 项目 | 入口目录 | 范围 |
|---|---|---|
| `findbox` | [findbox/](findbox/README.md) | 深度找箱、抬起保持、位姿辅助监督、FindBox AMP及walled变体 |
| `football` | [football/](football/README.md) | AgileKickball接球、回传和恢复站稳 |

`carrybox → findbox`是旧文档入口的兼容符号链接，不是第三条项目线。根目录`findbox/`继续存放原始动作。现有`carrybox_*`源码、`CarryBox`任务ID、CB任务编号和`carrybox-*`工程记录均归属findbox，保留原名以兼容已有引用。共享的`source/`、`scripts/`、`tests/`与资产不归属于任一任务的子目录；具体模块归属由下表和各入口索引。

## 当前工作

| 编号 | 项目 | 工作项 | 状态 | 验收或下一步 |
|---|---|---|---|---|
| FB-001 | [足球](football/README.md) | v4回传任务实现与工程验证 | 完成 | 已有状态回归、真实仿真及4096环境短训记录 |
| FB-002 | 足球 | v4正式训练至50000次迭代 | 完成 | 最终model_49999.pt、日志49999/50000及进程退出已核验；独立评估待做 |
| FB-003 | 足球 | 固定球速和固定±0.2m目标门的独立评估 | 待开始 | 分开报告回传命中、恢复站稳及失败情况 |
| CB-001 | [搬箱子](findbox/README.md) | 真实深度拾箱、无特权actor/critic、位姿辅助头 | 完成 | CPU与真实仿真管线通过 |
| CB-002 | 搬箱子 | FindBox动作数据接入AMP | 完成 | 17段动作、9项CPU测试、PPO/AMP更新及恢复/导出通过 |
| CB-003 | 搬箱子 | 正式训练 | 进行中 | [Warp正式PID2348537](../docs/carrybox/warp_20261014/README.md)，16:01核验iteration18，4.02秒/轮；未证明收敛 |
| CB-011 | 搬箱子 | 不收敛根因诊断与跌倒奖励修复 | 完成 | [历史终止标记跨回合漏罚已修，21项CPU与真实回放通过；新重训见CB-003](../docs/carrybox/convergence_20261014/README.md) |
| CB-015 | 搬箱子 | G1/X2深度后端与计时核对 | 完成 | [同源码profile分项](../docs/carrybox/depth_timing_20261014/README.md)：本地为RTX，Warp后端未迁移；无新增GPU试验，正式训练继续 |
| CB-014 | 搬箱子 | 4096完整迭代≤6秒 | 完成 | [Warp动态43几何迁移](../docs/carrybox/warp_20261014/README.md)：RTX差异≤0.164mm，24项CPU/碰撞/完整更新恢复通过；正式热身后均值4.023秒、最慢4.078秒 |
| CB-013 | 搬箱子 | 4096相机位姿读取性能优化 | 完成 | 同规模环境步减少23.2%，22项CPU/真实几何/4096更新恢复通过；正式训练继续 |
| CB-012 | 搬箱子 | RSI动作范围对齐与基础技能验证 | 待开始 | pickUp三片段20.8%/29.8%/49.6%帧目标超出当前控制范围；本次重训未调整，仍需专项处理 |
| CB-004 | 搬箱子 | 独立拾箱成功率评估 | 待开始 | 使用双手接触+离地+持续保持的任务成功判据 |
| CB-008 | findbox / football | 深度安装与遮挡管线核对 | 完成 | [FindBox三变体RTX遮挡通过；Football解析深度无场景遮挡；实机标定待提供](../docs/carrybox/depth_audit/README.md) |
| CB-006 | 搬箱子 | G1 FindBox walled3/walled4迁移 | 完成 | [19项CPU、两变体4环境20＋2轮、wall4 128环境50＋2轮及真实碰撞/遮挡通过](../docs/carrybox/wall4_repair/README.md) |
| CB-005 | 搬箱子 | FindBox全部动作可视化录制 | 完成 | [2026-10-14逐PT独立录制17段60fps MP4](../outputs/carrybox/findbox_individual/README.md)；全4628源帧、帧号/时间标注及hash校验通过；旧30fps合辑保留 |

“完成”描述该工作项的工程验收；短仿真通过不等于策略已学会任务。正式训练进度和评估结果分别记录。

CB-009：2026-10-13首次登记的[football→wall4等待](../docs/carrybox/wall4_queue/README.md)曾被GPU故障阻塞，该页保留历史证据。CB-010已完成[运行修复、正式规模验收及队列重新登记](../docs/carrybox/wall4_repair/README.md)。

CB-007：2026-10-13完成项目入口整理，findbox与football并列；兼容旧入口，未移动数据、模型或源码。此次整理没有更新训练运行状态，未解决CB-006的GPU故障。

## 资源归属

| 资源 | football | findbox |
|---|---|---|
| 主任务ID | `Template-Perceptual-Ball-AgileKickball-v4` | `Template-Perceptual-Ball-CarryBox-v0` |
| 数据 | `assets/motions/kick/`、`unitree_g1_retarget/` | 根目录`findbox/`；默认行走/拾起/持箱40/40/20% |
| 正式输出 | `logs/rsl_rl/agilekickball_v4/` | `logs/rsl_rl/g1_carrybox_depth/` |
| 设计与验证 | `docs/agilekickball_v4/` | `docs/carrybox/` |
| 工程工件前缀 | `agilekickball-*` | `carrybox-*` |
| 主要测试 | `test_agilekickball_v4.py`、`test_state_feedback.py` | `test_carrybox.py`、`test_carrybox_amp.py`、`test_carrybox_walled.py` |

`assets/`路径相对于`source/perceptual_ball/perceptual_ball/`。足球历史输出按原版本目录保留；`*_smoke`、`docs/**/smoke_model.pt`属于验证产物。

## 每次工作的记录方式

1. 确定所属项目及看板工作项；涉及共享代码时标明两条任务的影响。
2. 实现和验证使用对应项目的数据、task ID和checkpoint版本，产物进入该项目目录。
3. 更新项目入口的状态日期、验收证据、下一步；长期训练启动或结束后记录run目录和checkpoint。
4. 在`agent/`沿用对应任务前缀保存需要的工程交接，随后更新本看板。

状态统一使用“待开始 / 进行中 / 完成 / 阻塞 / 历史”。阻塞项需记录具体原因和恢复条件。PID和迭代数只是检查时快照；判断当前运行状态时重新读取进程与日志。

## 共享改动和运行边界

共享G1资产、CNN编码器、AMP判别器、train/play入口及导出器的改动，需要检查另一任务是否受影响。专项改动优先放在各任务自己的模块。两条任务checkpoint分别管理；足球v3→v4使用显式warm start，CarryBox当前schema=2含AMP训练状态。

项目管理工作只更新索引与记录。训练的启动、停止、恢复和资源分配按用户的实际任务指令执行；整理目录时保留已有训练进程、checkpoint、数据和历史证据。
