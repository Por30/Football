---
task_id: "agilekickball-v11-20261025"
language: "zh-CN"
axes: ["L", "P", "D", "C"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "新建kickballv11任务，在wall11基础保持框架，改为把球踢回来，数据集参考agilekickball。确认：沿用足球v4目标门和来球范围，最高5m/s，不保留墙柱；Actor深度与本体，Critic球位置/速度/回传目标真值；球位置速度辅助头；连续来球回踢恢复再发球；全部站立初始化。"
allowed_paths: ["source/perceptual_ball/perceptual_ball/kickball_v11.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/kickball_v11.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/kickball_v11_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_v11.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_kickball_v11.sh", "scripts/rsl_rl/play_kickball_v11.sh", "tests/test_kickball_v11.py", "docs/kickball_v11", "projects/README.md", "projects/football/README.md", "agent/plan/agilekickball-v11-20261025.md", "agent/task/agilekickball-v11-20261025.md", "agent/report/agilekickball-v11-20261025.md", "agent/handoff/agilekickball-v11-20261025.md"]
forbidden_scope: ["改变已有任务行为、动作原始数据、正式checkpoint", "正式长训或停止/重启其他进程", "真实硬件与无关重构"]
development_modes: ["ML_TRAINING", "ML_DATA_PIPELINE", "SIMULATOR_EXTENSION", "STATE_MACHINE"]
steps: ["核对wall11与v4调用链，审计迁移接口", "建立独立足球场景、站姿reset和连续回传状态", "接入左右踢球AMP、特权critic与球状态辅助监督", "接入独立注册、训练播放及checkpoint导出", "执行CPU回归与16环境2+1轮仿真更新恢复导出", "写回文档、项目入口与工程回执"]
tests: [{"command": "bash docs/kickball_v11/validate_cpu.sh"}, {"command": "bash docs/kickball_v11/validate_sim.sh"}]
stop_conditions: ["两次范围内修复后冻结验收仍失败", "需要范围外生产修改", "GPU资源不足或与既有正式训练冲突"]
safeguards: ["actor仅558本体与4x27x48米制深度；真值及阶段不进入actor或导出", "AMP专家与策略均零球位置，校验关节/连杆/frame与数据hash", "保留wall11显式PD/扰动/噪声/联合Adam/5x4/24步，辅助头只训练", "partial reset/终止历史/标签按同一时刻配对；恢复课程完整保存", "独立v11契约拒绝跨任务resume；验证模型只进入docs", "课程实际终点5m/s且覆盖参数受限，独立保存恢复并重置首轮，播放冻结课程", "保留kick原有命名关节和wrist_roll/ankle_pitch/head_link末端及rot6，核验实际刚体解析", "辅助标签使用current rollout观测，同次联合optimizer更新CNN/辅助头，导出无反馈", "tick在奖励读取前每步一次，保持足部代理与目标门统计区别", "站姿接地后同步动作延迟FIFO，终止快照用于AMP及timeout bootstrap"]
expert_required: true
expert_brief: {"affected_call_path": ["独立注册/train/play→v11场景/reset→wall11深度/PD→v4State→联合PPO/AMP/aux→恢复导出"], "critical_interfaces": ["v2硬编码6m/s需v11覆盖；CarryBox runner缺课程需独立序列化", "wall10 critic123/aux0约束需新policy与默认零损失hook", "kick120Hz、左右交错关节与原五末端；不得按FindBox schema读取", "Wall10 env包含箱任务依赖，v11独立reset/terminal，通用Warp相机仅Ball"], "invariants": ["actor558+4x27x48；critic真值隔离；AMP600零球槽；联合Adam5x4/24步保持"], "smallest_change_locus": ["新v11模块、默认关闭辅助hook、注册及train/play分支"], "mandatory_safeguards": ["actor仅558本体与4x27x48米制深度；真值及阶段不进入actor或导出", "AMP专家与策略均零球位置，校验关节/连杆/frame与数据hash", "保留wall11显式PD/扰动/噪声/联合Adam/5x4/24步，辅助头只训练", "partial reset/终止历史/标签按同一时刻配对；恢复课程完整保存", "独立v11契约拒绝跨任务resume；验证模型只进入docs", "课程实际终点5m/s且覆盖参数受限，独立保存恢复并重置首轮，播放冻结课程", "保留kick原有命名关节和wrist_roll/ankle_pitch/head_link末端及rot6，核验实际刚体解析", "辅助标签使用current rollout观测，同次联合optimizer更新CNN/辅助头，导出无反馈", "tick在奖励读取前每步一次，保持足部代理与目标门统计区别", "站姿接地后同步动作延迟FIFO，终止快照用于AMP及timeout bootstrap"], "minimal_tests": ["bash docs/kickball_v11/validate_cpu.sh", "bash docs/kickball_v11/validate_sim.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

已纳入一名只读组合轴专家的七字段审计。采用原足球AMP语义与wall11学习器，head_link和关节映射在真实仿真中核验；速度课程与辅助输入输出独立版本化。
