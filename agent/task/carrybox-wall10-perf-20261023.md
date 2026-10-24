---
task_id: "carrybox-wall10-perf-20261023"
language: "zh-CN"
axes: ["L", "P"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall10.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall10_env_cfg.py", "tests/test_carrybox_wall10_perf.py", "docs/carrybox/wall10_perf_20261023", "docs/carrybox/wall10_20261023/README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall10-perf-20261023.md", "agent/task/carrybox-wall10-perf-20261023.md", "agent/report/carrybox-wall10-perf-20261023.md", "agent/handoff/carrybox-wall10-perf-20261023.md"]
development_modes: ["ML_TRAINING", "SYSTEM_TUNING"]
original_request: "训练时间太长了 你参考本地深度管线的优化方式 正常训练时间一轮在4s左右"
forbidden_scope: ["改动其他任务、共享CNN或仿真安装", "删减AMP/smooth/深度遮挡或降频来冒充提速", "操作正式训练进程或修改正式checkpoint", "原数据或无关清理"]
steps: ["保存当前代码与实际训练耗时，审计本地性能优化", "定位同工作量采样与学习瓶颈", "实现wall10局部等价优化，保留逻辑随机分组与目标函数", "验证loss/gradient/optimizer、深度一致性及真实4096计时", "更新项目入口与四工件，明确100步和24步口径"]
tests: [{"command": "bash docs/carrybox/wall10_perf_20261023/validate_cpu.sh"}, {"command": "bash docs/carrybox/wall10_perf_20261023/validate_learning.sh"}, {"command": "bash docs/carrybox/wall10_perf_20261023/validate_sim.sh"}]
stop_conditions: ["需要修改范围外生产路径", "两次修复后冻结验收仍失败", "GPU出现资源冲突或非有限值故障"]
safeguards: ["保持actor深度/本体，critic独立，AMP/smooth训练端隔离", "保留4096、100步、5x4默认配方，用户明确选择24步时记录调整", "保留256逻辑随机分组、采样分布与联合Adam更新次数", "改变计算批量时检验输出/梯度/一次Adam和旧checkpoint恢复", "保留物理/相机/partial reset/终止/有限值保护"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["wall10 PPO current/mixed CNN, logical256 AMP draws, full-minibatch Adam; wall10 Warp box depth and one-physics-step force"], "critical_interfaces": ["4096x100, 5x4 updates; checkpoint cnn_microbatch256 remains logical random block; exact RNG sequence preserved"], "invariants": ["actor/critic separation, FP32 depth50Hz4x27x48/all occlusion, AMP/smooth coefficients, terminal histories and physical limits unchanged"], "smallest_change_locus": ["wall10-only learning, tensor window sampler and MDP; no shared CNN, camera or RSI changes"], "mandatory_safeguards": ["保持actor深度/本体，critic独立，AMP/smooth训练端隔离", "保留4096、100步、5x4默认配方，用户明确选择24步时记录调整", "保留256逻辑随机分组、采样分布与联合Adam更新次数", "改变计算批量时检验输出/梯度/一次Adam和旧checkpoint恢复", "保留物理/相机/partial reset/终止/有限值保护"], "minimal_tests": ["bash docs/carrybox/wall10_perf_20261023/validate_cpu.sh", "bash docs/carrybox/wall10_perf_20261023/validate_learning.sh", "bash docs/carrybox/wall10_perf_20261023/validate_sim.sh"], "blockers": []}
---

只对wall10做性能修改。普通完整迭代计时排除启动和编译预热；不把24步和100步轮次直接对比。不启动正式长训。
