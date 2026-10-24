---
task_id: "carrybox-wall11-20261024"
language: "zh-CN"
axes: ["L", "P", "E"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "新建wall11 加上深度噪声和圆柱和墙壁的干扰 然后你说明以下整个wall11的训练流程和观测"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall11.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall11.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall11_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/play_carrybox_walled.sh", "tests/test_carrybox_wall11.py", "docs/carrybox/wall11_20261024", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall11-20261024.md", "agent/task/carrybox-wall11-20261024.md", "agent/report/carrybox-wall11-20261024.md", "agent/handoff/carrybox-wall11-20261024.md"]
forbidden_scope: ["修改wall10生产模块/其他任务/共享CNN或AMP", "停止或重启现有训练、启动wall11正式长训", "修改原始动作数据或正式checkpoint"]
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION", "ML_DATA_PIPELINE"]
steps: ["核对wall10和运行资源，冻结局部改动边界", "实现wall11噪声缓存、随机碰撞障碍及独立配置/注册", "执行CPU和低显存GPU短测，核对几何/重置/终止/学习/恢复/导出", "同步项目入口、流程观测说明和工程回执"]
tests: [{"command": "bash docs/carrybox/wall11_20261024/validate_cpu.sh"}, {"command": "bash docs/carrybox/wall11_20261024/validate_sim.sh"}]
stop_conditions: ["两次范围内修复后验收仍失败", "需修改范围外生产代码", "GPU显存不足或与正式训练冲突"]
safeguards: ["保留actor558+4x27x48/critic123/AMP600，phase和障碍真值不进入actor，aux0", "障碍保护范围覆盖实际robot全连杆碰撞外延、箱体与平台；墙厚和柱半径纳入净空", "墙局部X径向、长边切向；增大柱环同步增大墙半径", "直接对原始米制深度加噪，同步terminal；reset仅失效选中行并在sim.forward后捕获", "独立wall11日志、checkpoint契约，拒绝wall10严格恢复", "保留wall10 PID2402395和生产文件，只16env24步2+1更新，不启动正式wall11"]
expert_required: true
expert_brief: {"affected_call_path": ["wall11 registration/config/env -> wall10 control/reset/reward/AMP/runner", "raw Warp optical depth with walls/cylinders -> corruption cache -> actor/terminal"], "critical_interfaces": ["super后恢复cylinder0-2且加入camera.object_names；Box仍变尺寸解析相交", "schema2、独立variant/noise/layout契约；locked dynamic obstacles使用tensor pose同步碰撞和深度"], "invariants": ["wall10目标/RSI/奖励/控制/5x4保持；wall11默认24步", "cache逐env逐controlstep，partial reset和terminal不跨回合"], "smallest_change_locus": ["三个wall11新模块，registration与shell允许11；复用所有学习器和共享资产"], "mandatory_safeguards": ["保留actor558+4x27x48/critic123/AMP600，phase和障碍真值不进入actor，aux0", "障碍保护范围覆盖实际robot全连杆碰撞外延、箱体与平台；墙厚和柱半径纳入净空", "墙局部X径向、长边切向；增大柱环同步增大墙半径", "直接对原始米制深度加噪，同步terminal；reset仅失效选中行并在sim.forward后捕获", "独立wall11日志、checkpoint契约，拒绝wall10严格恢复", "保留wall10 PID2402395和生产文件，只16env24步2+1更新，不启动正式wall11"], "minimal_tests": ["bash docs/carrybox/wall11_20261024/validate_cpu.sh", "bash docs/carrybox/wall11_20261024/validate_sim.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

专家只读审计已纳入七字段合同。布局采用保守全身保护盘；机器人连杆碰撞外延0.5m将在真实资产上核验。噪声采用已有corrupt_depth_m的中等米制参数，不增加随机延迟/冻结/安装偏移。
