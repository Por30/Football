# Perceptual Ball：FindBox 与 Football

2026-10-15 13:10 JST：[G1站立reset排查、接地修复与wall4正式重启](docs/carrybox/g1_reset_20261015/README.md)：旧model_14000真实横滚超限（1600回合均3步）；另修复G1参考初始化脚底穿地，wall3/wall4共同revision8按实际足部碰撞几何补足5mm间隙。G1相机位姿/身体与障碍遮挡、44项CPU、16环境更新恢复导出、4096验收通过。新wall4 PID2660033，4096环境fresh、核验iteration12，正式热身平均4.238秒/轮、最慢4.33秒；训练进行中，未证明收敛。

2026-10-15：[wall3/wall4公共修复与正式命令](docs/carrybox/wall_parity_20261015/README.md)：revision7统一实际头部COM、膝限位惩罚、物理动作目标裁剪、RSI60/30/10、搜索/yaw/推扰课程及训练配方。默认wall3仅墙，wall4墙加3圆柱，其他行为一致；41项CPU及两任务4环境更新/恢复/导出通过。未启动新版正式训练，未证明收敛；旧wall4 PID2448113仍使用revision6。

2026-10-14 21:13 JST：[wall4 handoff修订与新版AMP重启](docs/carrybox/handoff_20261014/README.md)：完整X2奖励/G1适配、RSI80/0/20、双向roll、深度/物理随机化及wall动作范围修复完成；35项CPU、4环境更新/恢复/导出及4096完整更新通过（平均4.295秒、最慢4.318秒）。旧PID2348537已停止，新PID2448113已核验到iteration30，正式热身后平均4.230秒、最慢4.300秒，首个checkpoint schema2/revision6及15段AMP身份一致；15段AMP，旧model_4200仅作权重迁移。未证明收敛。

2026-10-14：v5默认增加[每回合Kp/Kd与逐帧深度随机化](docs/agilekickball_v5/randomization/README.md)，CPU及4环境更新/恢复/导出通过，未启动正式训练。

2026-10-14新增 [kickball v5](docs/agilekickball_v5/README.md)：继承v4回传任务，深度加入完整机身与地面遮挡、改为光轴米制，并提供相机配置/部署预处理契约。4环境更新/恢复/导出与18组遮挡对照通过（最大差异0.152mm），尚未启动v5正式训练；实机标定待核对。

2026-10-14：足球新增[MuJoCo s2s入口](docs/agilekickball_v4/sim2sim_20261014/README.md)，官方仓库更新、G1编译及部署接口短测完成；接球回传稳定迁移、真实视觉和真机尚未验收。

2026-10-14 16:01 JST：Warp迁移完成，正式训练PID2348537已核验到iteration18；4096环境×24步、PPO 4 epochs×4 minibatches及完整AMP保持，热身后平均4.023秒、最慢4.078秒，达到6秒目标。新model_0.pt为schema2/revision5/warp，策略和AMP参数有限。尚未完成长训或证明拾箱收敛。[迁移与日志](docs/carrybox/warp_20261014/README.md)。下方为历史快照。

2026-10-14 15:09 JST：正式wall4 4096环境已从原正式model_0.pt恢复，PID2341959，检查到iteration2；后两轮17.62/17.42秒，schema2/revision4、策略与AMP有限值检查通过。6秒目标未达，训练尚未完成或证明收敛。[性能记录与日志](docs/carrybox/render6s_20261014/README.md)。下方状态为历史快照。

基于 Isaac Lab / RSL-RL 的 Unitree G1 项目。当前维护两个并列项目：`findbox`（找箱并抬起）与 `football`（接球回传），共享机器人资产和训练基础设施：

| 任务 | 当前主线 | 状态快照（2026-10-15） | 项目入口 |
|---|---|---|---|
| 足球 `football` | AgileKickball v4：接球、回传给发球者、恢复站稳 | 正式50000轮已结束，最终 `model_49999.pt` 已核验，独立评估待做 | [足球项目](projects/football/README.md) |
| 搬箱子 `findbox` | CarryBox v0：深度找箱、双手抬起保持、位姿辅助监督、FindBox AMP | revision8 wall4已正式从头启动，4096环境约4.24秒/轮；未证明收敛 | [搬箱子项目](projects/findbox/README.md) |

搬箱子新增的[walled3/walled4迁移](docs/carrybox/walled/README.md)已完成[运行修复](docs/carrybox/wall4_repair/README.md)，两变体4环境持续短训通过；128环境50＋2轮运行验收曾通过，但正式训练未收敛并已停止；最新[根因与任务设计](docs/carrybox/convergence_20261014/README.md)区分运行稳定性和学习有效性。CarryBox-v0基线仍保留。2026-10-14 12:54按用户新指令[重新启动wall4](docs/carrybox/restart_20261014/README.md)，使用独立新run与日志。

2026-10-14 14:06已停止上述128环境run，切换为[4096环境新训练](docs/carrybox/scale4096_20261014/README.md)。

2026-10-14 14:41历史：[4096相机读取优化与正式恢复](docs/carrybox/performance_20261014/README.md)，环境步耗时减少23.2%，新PID2336376。

[项目看板与管理约定](projects/README.md)记录任务归属、待办和进度更新规则。状态是带日期的快照，运行状态以进程及最新日志为准。

## 安装

使用已配置 Isaac Sim / Isaac Lab 的 Python 环境。模型和动作数据由 Git LFS 管理：

```bash
git lfs install
git clone https://github.com/Por30/Football.git
cd Football
git lfs pull
python -m pip install -e source/perceptual_ball
python scripts/list_envs.py
```

本地训练 checkpoint、日志和临时验证模型不随仓库分发。搬箱子 AMP 训练默认使用 [`assets/motions/findbox/`](source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md) 及其 `amp_manifest.json`，与足球`assets/motions/kick/`并列；根目录`findbox/`保留旧命名兼容快照。CarryBox-v0基线播放及策略导出不需要动作数据集，walled变体仿真播放的参考初始化需要该数据集。

## 任务入口

足球当前训练配方：

```bash
bash scripts/rsl_rl/train_agilekickball_v4.sh
```

2026-10-13检查时已有足球训练进程；再次启动前查看[足球运行状态](projects/football/README.md#运行状态与下一步)。脚本默认由稳定v3权重初始化，恢复v4训练使用同版本checkpoint。

搬箱子从头训练配方：

```bash
python scripts/rsl_rl/train.py \
  --task Template-Perceptual-Ball-CarryBox-v0 \
  --num_envs 128 --device cuda:0 --headless --enable_cameras \
  --max_iterations 30000 --seed 42 --run_name depth_pose_amp_scratch
```

真实深度相机需要 `--enable_cameras`。两条任务目前都使用 `cuda:0`，启动前检查已有训练和可用显存，环境数量分别由任务配方决定。

## 目录

```text
projects/
├── findbox/       # 找箱、拾箱、深度辅助监督、FindBox AMP
├── football/      # 接球、回传、恢复站稳
└── README.md      # 两项目总看板

source/            # 共享Python包；各任务模块保持原导入路径
scripts/           # 通用train/play，以及各项目训练和验证脚本
findbox/           # FindBox旧命名数据快照；当前默认数据在Python包assets/motions/findbox/
```

两个项目处于同一层级。`projects/carrybox → findbox`仅为旧链接兼容别名；`CarryBox`继续作为已有Gym任务和源码名称，不代表第三个项目。


| 路径 | 归属与用途 |
|---|---|
| `projects/football/`、`projects/findbox/` | 两个项目的入口、状态、代码地图和任务命令 |
| `source/perceptual_ball/` | 共用Python包、G1资产及两条任务的独立配置/实现 |
| `scripts/rsl_rl/train.py`、`play.py` | 共用训练和播放入口；通过任务ID选择 |
| `scripts/rsl_rl/*agilekickball*` | football配方和验证脚本 |
| `scripts/rsl_rl/*carrybox*`、`scripts/visualize_findbox*` | findbox配方、验证与数据可视化脚本 |
| `source/perceptual_ball/perceptual_ball/assets/motions/findbox/` | 当前15段FindBox AMP/RSI规范数据，与`kick/`并列 |
| `findbox/` | 旧命名15段兼容快照；完整原始17段保存在抱箱修订记录中 |
| `docs/agilekickball*/`、`docs/carrybox/` | 各任务设计和验证记录 |
| `tests/` | 测试按任务文件名前缀区分 |
| `logs/rsl_rl/agilekickball_v4/` | 足球当前正式训练产物 |
| `logs/rsl_rl/g1_carrybox_depth/` | 搬箱子正式训练产物；首训时创建 |
| `agent/{plan,task,report,handoff}/` | 历史工程工件，按任务前缀索引 |
| `unitree_g1_retarget/` | 足球动作重定向来源及演示 |

足球旧版本、旧入口和checkpoint兼容说明见[足球版本索引](projects/football/README.md#版本与历史)。工程协作边界见 [AGENTS.md](AGENTS.md)。
