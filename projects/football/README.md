# 足球项目 · football

2026-10-16：[与CarryBox交叉核对相机](../../docs/carrybox/camera_crosscheck_20261016/README.md)：v4/v5训练仍为89.16°×58°/50Hz，名义安装匹配G1 rev_1_0；v4仅球体射线距离，v5为含自遮挡的光轴米制。MuJoCo官方参考profile不自动替换训练或v5模型内嵌profile；60Hz官方profile当前不能直接用于50Hz lazy训练。实机内参/光心仍未验证，本次未改生产配置。

2026-10-16：[s2s相机按官方G1文档对齐](../../docs/agilekickball_v5/official_g1_camera_20261016/README.md)：默认独立D435i profile为官方示例640×480 Z16/60fps、官方图示垂直55.2°和rev_1_0安装。60Hz物理tick采集与50Hz策略分开，31项检查/100步闭环/121次采集审计通过；旧camera_nominal及v5训练/模型源契约保留。

2026-10-16：[s2s已默认切换完整场景深度](../../docs/agilekickball_v5/sim2sim_scene_20261016/README.md)：相机对完整机身可见网格、地面、球和模型内所有静动态环境表面求最近交点，输出光轴Z米制；支持v5 profile/导出契约，旧解析模式显式`--depth-mode analytic`保留。28项检查及100控制步/20帧视频通过。当前默认v4权重仍是旧球体深度训练，场景输入会改变分布；未启动v5正式训练，未声称实机标定或稳定迁移完成。

2026-10-15：[足球快球跌倒诊断](../../docs/agilekickball_v4/speed_fall_20261015/README.md)完成：固定场景4/6m/s复现；4m/s无球机器人碰撞仍1.60秒跌倒，单独恢复训练hip-roll上限也未修复。接触前抬腿限幅及踢后支撑恢复失稳已取证；训练速度课程已到6m/s。8项接口检查与CPU诊断通过，不等于策略稳定；未改生产控制器或训练。

2026-10-15：[足球s2s球/深度一致性核对](../../docs/agilekickball_v4/sim2sim_parity_20261015/README.md)完成：球0.43kg/0.11m一致；相机非单位四元数逆变换已修，384姿态命中mask零差异、最大误差0.0166mm，12项检查与两次10秒闭环通过。球阻尼/接触及G1质量、力矩、相机基准仍有差异，未证明接球改善或稳定迁移。

2026-10-15：足球MuJoCo深度窗口新增球速滑块、立即应用与重新发球，显示设定/实际水平速度；8项原检查和4项新增检查（含实际GUI交互100步）通过。[使用方式与证据](../../docs/agilekickball_v4/sim2sim_20261014/README.md)。仅接口验证，未形成稳定迁移或真机结论。

2026-10-14：v5增益倍率0.9–1.1及深度scale/bias/距离噪声/缺失随机化已接入并通过短测；[范围、开关与证据](../../docs/agilekickball_v5/randomization/README.md)。扰动仅在模拟环境使用，范围尚非实机标定。

2026-10-14新增独立 [AgileKickball-v5](../../docs/agilekickball_v5/README.md)：继承v4回传流程，改用完整机身/Ball/ground网格光轴深度，包含自遮挡。仿真实现与4环境PPO/AMP、恢复/导出、18组遮挡对照已通过（最大差异0.152mm）；实机标定尚缺，未启动v5正式训练。v4作为已完成训练的基线保留。

2026-10-14：MuJoCo图形启动默认同步打开实时深度窗口（当前帧+8帧历史，10Hz）；双窗口100控制步/20次刷新短测通过。可用`--no-depth-window`关闭，详见[s2s命令](../../docs/agilekickball_v4/sim2sim_20261014/README.md)。

2026-10-14：新增[策略深度可视化](../../docs/agilekickball_v4/sim2sim_20261014/depth_visualization/depth.mp4)，12秒视频/8帧历史/原始NPZ已验证；v4解析球体深度，无场景遮挡。

2026-10-14：已更新官方MuJoCo/main并保留定制，G1控制器编译完成；新增v4独立CPU s2s，8项CPU与500步闭环通过。60秒诊断仍有漏接/跌倒风险，未验收任务稳定性、真实视觉或真机；[运行命令与证据](../../docs/agilekickball_v4/sim2sim_20261014/README.md)。

2026-10-14 11:39 JST检查：football正式训练已结束，日志到49999/50000，最终model_49999.pt已由队列核验版本及全部张量有限性，原进程已退出。随后wall4正式训练启动，PID2307414。独立足球成功率评估仍未执行；下文10月13日在训状态为历史。

已训练基线：`Template-Perceptual-Ball-AgileKickball-v4`，revision `return_to_sender_20261012`。目标是连续接球、回传给本轮发球者并恢复站稳。项目待办见[总看板](../README.md)。

## 项目归属

本目录是`football`项目的统一入口，与[findbox](../findbox/README.md)并列。`AgileKickball`/历史`Soccer`任务、`agilekickball_*`源码及`agilekickball-*`工程记录属于本项目。G1资产、Python包和通用train/play由两个项目共享；数据、任务配置、checkpoint与验收记录分别管理。

## 运行状态与下一步

2026-10-13约23:54 JST只读检查：正式训练进程PID `2056902`仍存在，配置为4096环境、50000次迭代、seed42；当前约48693/50000轮，最近已保存`model_48600.pt`；checkpoint版本与全部浮点张量有限性检查正常。这是检查时快照，不能当作实时状态。

- run目录：`logs/rsl_rl/agilekickball_v4/2026-10-12_13-48-41_return_to_sender_20261012_v3init/`
- 运行日志：`logs/rsl_rl/agilekickball_v4/train_20261012.log`
- 初始化来源：稳定v3的`2026-10-08_11-48-24_feedback_stable_20261008_v2init/model_49999.pt`
- 下一步：跟踪当前训练结束，然后以固定球速和固定±0.2m目标门单独评估；训练分布命中率不代替独立评估结果。

从仓库根目录只读查看：

```bash
ps -p 2056902 -o pid,etime,args
tail -n 100 logs/rsl_rl/agilekickball_v4/train_20261012.log
```

已有训练时先核对状态与资源，再决定后续启动。

2026-10-13 23:54 JST已重新登记football→wall4队列，等待器PID2300674，READY / WAITING_FOOTBALL。wall4已通过128环境50＋2轮验收；队列仍须核验本次足球最终model_49999.pt、日志及进程结束，才会复核资源并启动wall4。足球代码、进程及训练参数未改，未停止/重启。见[最新运行修复和串行记录](../../docs/carrybox/wall4_repair/README.md)。

## 配置与代码地图

源码均在`source/perceptual_ball/perceptual_ball/`下：

| 模块 | 路径 |
|---|---|
| v4环境和PPO配置 | `tasks/manager_based/perceptual_ball/agilekickball_v4_env_cfg.py` |
| v4回传奖励和课程 | `tasks/manager_based/perceptual_ball/mdp/agilekickball_v4.py` |
| 继承的v3网络/环境 | `agilekickball_v3_env_cfg.py`、`rsl_rl_extensions/state_feedback.py` |
| 训练深度与任务状态 | `mdp/perception.py`（v4）、`mdp/agilekickball_v5.py`、`mdp/kickball_state.py` |
| MuJoCo场景深度与相机契约 | `scripts/sim2sim/scene_depth.py`、`scripts/sim2sim/kickball_mujoco.py`、`kickball_depth.py`（路径相对仓库/包） |
| 足球runner与checkpoint | `rsl_rl_extensions/runner.py` |
| AMP动作参考 | `assets/motions/kick/` |

环境与MDP的短路径均相对于`tasks/manager_based/perceptual_ball/`。足球v4使用解析深度，v5使用Warp场景深度，均保留足球自身critic配置；搬箱子的无特权观测规则仅适用于CarryBox。

## 深度管线边界（2026-10-13核对）

当前主线的相机名义安装位置与训练G1 rev_1_0模型一致，但深度仍是解析球面相交，**不包含地面、机身或其他障碍遮挡**，输出为沿射线距离；与FindBox的RTX光轴深度不同。详细[两条管线核对](../../docs/carrybox/depth_audit/README.md)。实机CameraInfo/光学外参/预处理尚未核对，本次未改足球训练。

## 命令

在仓库根目录执行，运行环境须配置Isaac Lab。当前v4正式配方：

```bash
bash scripts/rsl_rl/train_agilekickball_v4.sh
```

脚本默认加载稳定v3完整权重，新建v4优化器与课程；v3来源路径已写在脚本中。恢复已有v4训练：

```bash
bash scripts/rsl_rl/train_agilekickball_v4.sh \
  --resume --checkpoint /path/to/v4/model.pt
```

播放同版本checkpoint：

```bash
python scripts/rsl_rl/play.py \
  --task Template-Perceptual-Ball-AgileKickball-v4 \
  --num_envs 4 --checkpoint /path/to/v4/model.pt --visray
```

针对当前主线的CPU检查：

```bash
python -m unittest discover -s tests -p test_agilekickball_v4.py
python -m unittest discover -s tests -p test_state_feedback.py
```

`scripts/rsl_rl/smoke_agilekickball_v4.sh`包含真实仿真及4096环境100轮训练，应在有资源预算时运行。

## 版本与历史

| 版本 | 角色 | 文档 |
|---|---|---|
| AgileKickball v5 | 场景深度开发版本，实机标定待核对 | [v5说明](../../docs/agilekickball_v5/README.md) |
| AgileKickball v4 | 已训练回传基线 | [任务设计](../../docs/agilekickball_v4/README.md) |
| AgileKickball v3 stable | v4初始化基线 | [v3说明](../../docs/agilekickball_v3/README.md) |
| AgileKickball v2 | 速度课程历史基线 | [v2设计](../../docs/agilekickball_v2/DESIGN.md) |
| AgileKickball v1 | 渐进来球课程历史版本 | [v1说明](../../docs/agilekickball_v1/README.md) |
| AgileKickball v0 | 基础连续踢球版本 | [基础说明](../../docs/agilekickball/README.md) |
| v3-StateFeedback-20261006 / v3-Outcome | 归档实验；保留旧checkpoint入口 | v3文档及对应源码 |
| Template-Perceptual-Ball-v0 / Soccer-v2 / Soccer-v3 | 早期实现与回归参考 | 任务注册与对应源码 |

历史v1/v2从头训练命令分别见其文档；它们不再作为根README的默认入口。`--ballspeed MIN MAX`、`--visray`见[深度可视化说明](../../docs/play_visray/README.md)。

当前实现与训练启动证据：[v4交接](../../agent/handoff/agilekickball-v4-return.md)、[验证目录](../../docs/agilekickball_v4/return_to_sender_20261012)。交接中的PID/进度同样按记录日期解读。
