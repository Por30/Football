# 项目看板

2026-10-16：[Kickball / CarryBox相机交叉核对](../docs/carrybox/camera_crosscheck_20261016/README.md)：两训练线名义安装匹配官方G1 rev_1_0，但足球v4/v5与wall3–5仍是58°垂直FOV；官方图示55.2°目前仅在足球部分MuJoCo路径应用。v4无自遮挡，v5/wall有现有场景遮挡；实机标定、训练/s2s profile和时序对齐待完成。本次仅审计，未改生产配置或进程。

2026-10-16：[足球s2s官方G1相机对齐](../docs/agilekickball_v5/official_g1_camera_20261016/README.md)完成：官方D435i例程640×480 Z16/60fps、图示55.2°/下俯47.6°，物理tick绝对相位采集，50Hz策略取最新帧。31项检查、2秒100控制步/121采集与独立审计通过，漏采0；旧v5训练profile及checkpoint契约保留，名义K不标实测。

2026-10-16：[足球s2s完整场景深度](../docs/agilekickball_v5/sim2sim_scene_20261016/README.md)完成：默认scene光轴Z、完整机身/地面/环境最近表面，复用v5相机profile与严格契约；28项检查（含GUI、遮挡/动态物体/采集保持）及100步CPU闭环/20帧视频通过。旧v4权重仅作分布变化诊断；实机标定和任务稳定性待验证，未启动训练。

2026-10-16：[wall5早期AMP占比核对](../docs/carrybox/wall5_start_20261016/README.md#amp早期占比核对第5574轮)：第55–74轮AMP占净混合奖励约47.3%，style0.098、D expert/policy loss0.0198/0.0669、有效率100%，量级符合差异文档X2参考；仍以倾倒结束、拾箱成功0，尚不能判断收敛；只读检查，未改参或重启。

2026-10-16 13:49 JST：[wall5正式训练启动核验](../docs/carrybox/wall5_start_20261016/README.md)：用户启动PID2996727，4096环境、40000轮、fresh；已完成第12轮，热身后10轮平均4.244秒、最慢4.36秒。model_0为schema2/revision9/35维AMP/15段数据，策略与D有限且优化器有更新，AMP有效率100%；训练进行中，未证明收敛。

2026-10-16：[新增wall5：X2/G1差异文档的AMP阶段A](../docs/carrybox/wall5_20261016/README.md)。基于wall4 revision8，AMP改为每步上限0.125、35维原始本体特征、D正则化与较低学习率、reset首步参与奖励和更新。PPO/深度/任务几何保持；50项CPU、4环境3＋1轮恢复导出通过。未正式训练或验证收敛/4096耗时；12:35 JST原wall4 PID2660033仍运行。

2026-10-15：[足球快球跌倒诊断](../docs/agilekickball_v4/speed_fall_20261015/README.md)完成：固定场景4/6m/s复现；4m/s无球机器人碰撞仍1.60秒跌倒，单独恢复训练hip-roll上限也未修复。接触前抬腿限幅及踢后支撑恢复失稳已取证；训练速度课程已到6m/s。8项接口检查与CPU诊断通过，不等于策略稳定；未改生产控制器或训练。

2026-10-15 13:10 JST：[G1站立reset排查、接地修复与wall4正式重启](../docs/carrybox/g1_reset_20261015/README.md)：旧model_14000真实横滚超限（1600回合均3步）；另修复G1参考初始化脚底穿地，wall3/wall4共同revision8按实际足部碰撞几何补足5mm间隙。G1相机位姿/身体与障碍遮挡、44项CPU、16环境更新恢复导出、4096验收通过。新wall4 PID2660033，4096环境fresh、核验iteration12，正式热身平均4.238秒/轮、最慢4.33秒；训练进行中，未证明收敛。

2026-10-15：[足球s2s球/深度一致性核对](../docs/agilekickball_v4/sim2sim_parity_20261015/README.md)完成：球0.43kg/0.11m一致；相机非单位四元数逆变换已修，384姿态命中mask零差异、最大误差0.0166mm，12项检查与两次10秒闭环通过。球阻尼/接触及G1质量、力矩、相机基准仍有差异，未证明接球改善或稳定迁移。

2026-10-15：新增[旧wall4模型显式仅权重播放](../docs/carrybox/play_v6_20261015/README.md)，model_14000在当前revision7环境的4环境命令已提供；实际权重CPU兼容检查通过，未启动GUI或训练。默认严格恢复规则保留。

2026-10-15：[wall3/wall4公共修复与正式命令](../docs/carrybox/wall_parity_20261015/README.md)：revision7统一实际头部COM、膝限位惩罚、物理动作目标裁剪、RSI60/30/10、搜索/yaw/推扰课程及训练配方。默认wall3仅墙，wall4墙加3圆柱，其他行为一致；41项CPU及两任务4环境更新/恢复/导出通过。未启动新版正式训练，未证明收敛；旧wall4 PID2448113仍使用revision6。

2026-10-15：[wall4不收敛诊断](../docs/carrybox/convergence_20261015/README.md)：13691轮快照及16环境纯推理确认行走起点约3步倾倒，保持reset角约39步；直接抱箱轨迹占有效样本；发现head_link腰部原点误作头部高度及专家膝角与软限位惩罚冲突。仅关闭push未修复，AMP训练style近零。已完成诊断，生产修复待做；PID2448113保持运行，未修改或重启训练。

2026-10-15：足球MuJoCo深度窗口新增球速滑块、立即应用与重新发球，显示设定/实际水平速度；8项原检查和4项新增检查（含实际GUI交互100步）通过。[使用方式与证据](../docs/agilekickball_v4/sim2sim_20261014/README.md)。仅接口验证，未形成稳定迁移或真机结论。

2026-10-14 21:13 JST：[wall4 handoff修订与新版AMP重启](../docs/carrybox/handoff_20261014/README.md)：完整X2奖励/G1适配、RSI80/0/20、双向roll、深度/物理随机化及wall动作范围修复完成；35项CPU、4环境更新/恢复/导出及4096完整更新通过（平均4.295秒、最慢4.318秒）。旧PID2348537已停止，新PID2448113已核验到iteration30，正式热身后平均4.230秒、最慢4.300秒，首个checkpoint schema2/revision6及15段AMP身份一致；15段AMP，旧model_4200仅作权重迁移。未证明收敛。

2026-10-14 20:46 JST：CB-017[新版AMP默认配置复核](../docs/carrybox/amp_default_20261014/README.md)通过，基线/wall3/wall4及RSI均用规范15段；两组CPU PASS。当前旧wall4进程model_4000.pt仍记录17段，未切换正式训练。

2026-10-14：FB-006补充实时深度窗口，MuJoCo图形启动默认启用；真实桌面双窗口短测通过，未改变策略/训练。

2026-10-14：FB-006足球MuJoCo深度可视化完成，[12秒策略输入视频](../docs/agilekickball_v4/sim2sim_20261014/depth_visualization/depth.mp4)及原始深度已保存；未改变控制或训练。

2026-10-14更新：FB-004足球MuJoCo部署接口实现完成，官方仓库同步、G1编译及8项CPU/500步闭环通过；FB-005接球回传稳定迁移待完成，60秒训练步长诊断出现1次跌倒。未启动训练或真机。[s2s记录](../docs/agilekickball_v4/sim2sim_20261014/README.md)。

更新时间：2026-10-15 13:10（G1接地适配修复，wall4 revision8正式启动，Asia/Tokyo）。项目管理员：用户；具体开发与验证结果写入对应项目记录。

本仓库维护两个独立任务，共享G1资产、Isaac Lab运行环境和通用训练入口。`findbox`与`football`是并列项目标识；源码和已有产物保留稳定路径，由各项目入口统一索引。

## 并列项目入口

| 项目 | 入口目录 | 范围 |
|---|---|---|
| `findbox` | [findbox/](findbox/README.md) | 深度找箱、抬起保持、位姿辅助监督、FindBox AMP及walled变体 |
| `football` | [football/](football/README.md) | AgileKickball接球、回传和恢复站稳 |

`carrybox → findbox`是旧文档入口的兼容符号链接，不是第三条项目线。根目录`findbox/`保留旧命名数据快照；当前规范数据在Python包`assets/motions/findbox/`，与足球`kick/`并列。现有`carrybox_*`源码、`CarryBox`任务ID、CB任务编号和`carrybox-*`工程记录均归属findbox，保留原名以兼容已有引用。共享的`source/`、`scripts/`、`tests/`与资产不归属于任一任务的子目录；具体模块归属由下表和各入口索引。

## 当前工作

| 编号 | 项目 | 工作项 | 状态 | 验收或下一步 |
|---|---|---|---|---|
| FB-001 | [足球](football/README.md) | v4回传任务实现与工程验证 | 完成 | 已有状态回归、真实仿真及4096环境短训记录 |
| FB-002 | 足球 | v4正式训练至50000次迭代 | 完成 | 最终model_49999.pt、日志49999/50000及进程退出已核验；独立评估待做 |
| FB-004 | 足球 | v5场景光轴深度与机器人自遮挡 | 仿真通过；实机待标定 | [继承v4回传/AMP，独立ID和深度契约](../docs/agilekickball_v5/README.md)；4环境更新/恢复/导出、18组遮挡对照通过，未正式训练 |
| FB-007 | 足球 | v5 Kp/Kd与深度训练随机化 | 完成 | [默认开启、CPU/4环境增益同步与噪声时序/PPO恢复导出通过](../docs/agilekickball_v5/randomization/README.md)；未正式训练，范围非实机标定 |
| FB-003 | 足球 | 固定球速和固定±0.2m目标门的独立评估 | 待开始 | 分开报告回传命中、恢复站稳及失败情况 |
| CB-001 | [搬箱子](findbox/README.md) | 真实深度拾箱、无特权actor/critic、位姿辅助头 | 完成 | CPU与真实仿真管线通过 |
| CB-002 | 搬箱子 | FindBox动作数据接入AMP | 完成 | 初次17段接入及PPO/AMP更新、恢复/导出已通过；当前15段修订见CB-016 |
| CB-003 | 搬箱子 | 正式训练 | wall5运行中 | [2026-10-16 13:49核验](../docs/carrybox/wall5_start_20261016/README.md)：PID2996727、4096环境、第12轮，热身平均4.244秒/轮；未证明收敛 |
| CB-011 | 搬箱子 | 不收敛根因诊断与跌倒奖励修复 | 完成 | [历史终止标记跨回合漏罚已修，21项CPU与真实回放通过；新重训见CB-003](../docs/carrybox/convergence_20261014/README.md) |
| CB-015 | 搬箱子 | G1/X2深度后端与计时核对 | 完成 | [同源码profile分项](../docs/carrybox/depth_timing_20261014/README.md)：本地为RTX，Warp后端未迁移；无新增GPU试验，正式训练继续 |
| CB-014 | 搬箱子 | 4096完整迭代≤6秒 | 完成 | [Warp动态43几何迁移](../docs/carrybox/warp_20261014/README.md)：RTX差异≤0.164mm，24项CPU/碰撞/完整更新恢复通过；正式热身后均值4.023秒、最慢4.078秒 |
| CB-013 | 搬箱子 | 4096相机位姿读取性能优化 | 完成 | 同规模环境步减少23.2%，22项CPU/真实几何/4096更新恢复通过；正式训练继续 |
| CB-012 | 搬箱子 | RSI动作范围对齐与基础技能验证 | 部分完成 | [wall专属clip9已覆盖全部15段及默认角扰动](../docs/carrybox/handoff_20261014/README.md)；独立基础技能评估待做 |
| CB-018 | 搬箱子 | wall4分技能失败与AMP/奖励冲突诊断 | 诊断完成；修复见CB-019 | [日志、纯推理、实际USD软限位证据](../docs/carrybox/convergence_20261015/README.md)；未改变正式训练 |
| CB-019 | 搬箱子 | wall3/wall4共用修复、仅障碍不同 | 实现与短测完成 | [revision7与4096环境正式命令](../docs/carrybox/wall_parity_20261015/README.md)；41项CPU、两任务更新恢复导出通过；未启动新版正式训练、未验证收敛 |
| CB-020 | 搬箱子 | G1站立reset/相机/构型复核与正式重启 | 实现/验收/启动完成 | [revision8接地适配](../docs/carrybox/g1_reset_20261015/README.md)，旧策略倾倒与脚底穿地分别取证；实机光心标定及独立收敛评估待做 |
| CB-021 | 搬箱子 | wall5 AMP阶段A对照任务 | 实现/短测完成 | [50项CPU、4环境3＋1轮更新恢复及导出通过](../docs/carrybox/wall5_20261016/README.md)；保留wall4，wall5未正式启动、未验证收敛或4096速度 |
| CB-004 | 搬箱子 | 独立拾箱成功率评估 | 待开始 | 使用双手接触+离地+持续保持的任务成功判据 |
| CB-008 | findbox / football | 深度安装与遮挡管线核对 | 完成 | [FindBox三变体RTX遮挡通过；Football解析深度无场景遮挡；实机标定待提供](../docs/carrybox/depth_audit/README.md) |
| CB-006 | 搬箱子 | G1 FindBox walled3/walled4迁移 | 完成 | [19项CPU、两变体4环境20＋2轮、wall4 128环境50＋2轮及真实碰撞/遮挡通过](../docs/carrybox/wall4_repair/README.md) |
| CB-005 | 搬箱子 | FindBox全部动作可视化录制 | 完成 | [当前15段逐PT独立60fps视频](../outputs/carrybox/findbox_hold_20261014/README.md)；4155帧/69.25秒及hash校验通过；旧17段视频保留 |
| CB-016 | 搬箱子 | carrywith1开头抱箱延长与AMP整理 | 完成 | [原0–20帧保留、重复第20帧至5秒](../docs/carrybox/amp_hold_20261014/README.md)；有效11/3/1共15段，旧17段全量备份，AMP/RSI检查通过；未切换正式训练 |
| CB-017 | 搬箱子 | AMP数据规范命名与kick并列存放 | 完成 | [assets/motions/findbox规范目录](../source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md)；15段字节不变，AMP/RSI默认一致、CPU检查通过；旧路径保留，未切换训练 |

“完成”描述该工作项的工程验收；短仿真通过不等于策略已学会任务。正式训练进度和评估结果分别记录。

CB-009：2026-10-13首次登记的[football→wall4等待](../docs/carrybox/wall4_queue/README.md)曾被GPU故障阻塞，该页保留历史证据。CB-010已完成[运行修复、正式规模验收及队列重新登记](../docs/carrybox/wall4_repair/README.md)。

CB-007：2026-10-13完成项目入口整理，findbox与football并列；兼容旧入口，未移动数据、模型或源码。此次整理没有更新训练运行状态，未解决CB-006的GPU故障。

## 资源归属

| 资源 | football | findbox |
|---|---|---|
| 主任务ID | `Template-Perceptual-Ball-AgileKickball-v4` | `Template-Perceptual-Ball-CarryBox-v0` |
| 数据 | `assets/motions/kick/`、`unitree_g1_retarget/` | `assets/motions/findbox/`；默认行走/拾起/抱箱40/40/20%，根findbox为兼容快照 |
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
