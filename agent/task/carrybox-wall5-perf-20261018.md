---
task_id: "carrybox-wall5-perf-20261018"
language: "zh-CN"
axes: ["L", "P", "E", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "训练间间比之前长了是为什么 你排查好原因之后 重新正启动动wall5的训练"
development_modes: ["DEBUG", "OPTIMIZE"]
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/train.py", "tests/test_carrybox_perf.py", "docs/carrybox/wall5_perf_20261018", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-perf-20261018.md", "agent/task/carrybox-wall5-perf-20261018.md", "agent/report/carrybox-wall5-perf-20261018.md", "agent/handoff/carrybox-wall5-perf-20261018.md"]
forbidden_scope: ["更改任务机制、AMP权重/schema、epochs、网络大小、RSI比例、观测/相机/碰撞", "删除数据或历史产物", "改变足球训练行为", "操作实机"]
steps: ["保存实时状态和源文件，停止用户授权重启的wall5", "4096环境实测baseline各阶段耗时", "实现实测支持的最小等价优化", "等价性与4096完整更新/恢复验证", "从正式checkpoint重启4096 wall5并确认持续推进", "更新项目入口和四类工程工件"]
tests: [{"command": "bash docs/carrybox/wall5_perf_20261018/check.sh"}, {"command": "bash docs/carrybox/wall5_perf_20261018/benchmark.sh"}, {"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_perf_20261018/verify_restart.py"}]
stop_conditions: ["数值/契约不等价则停止正式重启并在范围内修复，单项最多两次", "GPU资源不足或仿真致命异常不并发正式训练"]
safeguards: ["AMP对照固定clip IDs、连续starts，包含末帧边界、四元数符号翻转、不同clip长度；检查数值与采样RNG消耗。", "CNN复用比较outputs、总loss、各参数gradients和一次optimizer更新；保留辅助掩码和KL调整顺序。", "RSI合并写入核对joint、root-link velocity、COM velocity、足部间隙、box/hold高度、未reset行不变。不能把link writer换成COM writer。", "GPU profiler累计时间可能将前序异步GPU工作算在item上；区分同步和kernel，保留finite检查。", "正式benchmark单独进程、相同checkpoint/seed/config，排除预热并拆分collection/learning；保留完整更新与保存恢复。", "停训时只有model_0.pt则明确只能恢复model0，未保存迭代丢失；不使用docs验证模型替代正式checkpoint。", "runner.learn(n)为恢复迭代加n；核对总预算，保留原run/checkpoint/log。"]
expert_required: true
expert_brief: {"affected_call_path": ["Wall5 collection/reset/RSI/Warp and CNN/PPO/AMP update"], "critical_interfaces": ["root-link vs COM速度；raw插值后pack60；checkpoint/RNG保持"], "invariants": ["4096x24、5epochs、4minibatches、512/256/256、RSI80/0/20、全部遮挡50Hz"], "smallest_change_locus": ["批量RSI写入、专家raw gather、CNN同批复用"], "mandatory_safeguards": ["AMP对照固定clip IDs、连续starts，包含末帧边界、四元数符号翻转、不同clip长度；检查数值与采样RNG消耗。", "CNN复用比较outputs、总loss、各参数gradients和一次optimizer更新；保留辅助掩码和KL调整顺序。", "RSI合并写入核对joint、root-link velocity、COM velocity、足部间隙、box/hold高度、未reset行不变。不能把link writer换成COM writer。", "GPU profiler累计时间可能将前序异步GPU工作算在item上；区分同步和kernel，保留finite检查。", "正式benchmark单独进程、相同checkpoint/seed/config，排除预热并拆分collection/learning；保留完整更新与保存恢复。", "停训时只有model_0.pt则明确只能恢复model0，未保存迭代丢失；不使用docs验证模型替代正式checkpoint。", "runner.learn(n)为恢复迭代加n；核对总预算，保留原run/checkpoint/log。"], "minimal_tests": ["bash docs/carrybox/wall5_perf_20261018/check.sh", "bash docs/carrybox/wall5_perf_20261018/benchmark.sh", "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_perf_20261018/verify_restart.py"], "blockers": []}
device_actions: []
real_device_authorized: false
---

用户已授权排查后重启。保存旧产物，验证数据与观测边界。性能对照使用同revision13；历史rev9仅作为参考。
