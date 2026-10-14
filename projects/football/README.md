# 足球项目 · football

2026-10-14：MuJoCo图形启动默认同步打开实时深度窗口（当前帧+8帧历史，10Hz）；双窗口100控制步/20次刷新短测通过。可用`--no-depth-window`关闭，详见[s2s命令](../../docs/agilekickball_v4/sim2sim_20261014/README.md)。

2026-10-14：新增[策略深度可视化](../../docs/agilekickball_v4/sim2sim_20261014/depth_visualization/depth.mp4)，12秒视频/8帧历史/原始NPZ已验证；v4解析球体深度，无场景遮挡。

2026-10-14：已更新官方MuJoCo/main并保留定制，G1控制器编译完成；新增v4独立CPU s2s，8项CPU与500步闭环通过。60秒诊断仍有漏接/跌倒风险，未验收任务稳定性、真实视觉或真机；[运行命令与证据](../../docs/agilekickball_v4/sim2sim_20261014/README.md)。

2026-10-14 11:39 JST检查：football正式训练已结束，日志到49999/50000，最终model_49999.pt已由队列核验版本及全部张量有限性，原进程已退出。随后wall4正式训练启动，PID2307414。独立足球成功率评估仍未执行；下文10月13日在训状态为历史。

当前主线：`Template-Perceptual-Ball-AgileKickball-v4`，revision `return_to_sender_20261012`。目标是连续接球、回传给本轮发球者并恢复站稳。项目待办见[总看板](../README.md)。

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
| 深度与任务状态 | `mdp/depth_v3.py`、`mdp/kickball_state.py`及各版本MDP |
| 足球runner与checkpoint | `rsl_rl_extensions/runner.py` |
| AMP动作参考 | `assets/motions/kick/` |

环境与MDP的短路径均相对于`tasks/manager_based/perceptual_ball/`。足球使用现有解析深度及其自身critic配置；搬箱子的无特权观测规则仅适用于CarryBox。

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
| AgileKickball v4 | 当前开发和训练主线 | [任务设计](../../docs/agilekickball_v4/README.md) |
| AgileKickball v3 stable | v4初始化基线 | [v3说明](../../docs/agilekickball_v3/README.md) |
| AgileKickball v2 | 速度课程历史基线 | [v2设计](../../docs/agilekickball_v2/DESIGN.md) |
| AgileKickball v1 | 渐进来球课程历史版本 | [v1说明](../../docs/agilekickball_v1/README.md) |
| AgileKickball v0 | 基础连续踢球版本 | [基础说明](../../docs/agilekickball/README.md) |
| v3-StateFeedback-20261006 / v3-Outcome | 归档实验；保留旧checkpoint入口 | v3文档及对应源码 |
| Template-Perceptual-Ball-v0 / Soccer-v2 / Soccer-v3 | 早期实现与回归参考 | 任务注册与对应源码 |

历史v1/v2从头训练命令分别见其文档；它们不再作为根README的默认入口。`--ballspeed MIN MAX`、`--visray`见[深度可视化说明](../../docs/play_visray/README.md)。

当前实现与训练启动证据：[v4交接](../../agent/handoff/agilekickball-v4-return.md)、[验证目录](../../docs/agilekickball_v4/return_to_sender_20261012)。交接中的PID/进度同样按记录日期解读。
