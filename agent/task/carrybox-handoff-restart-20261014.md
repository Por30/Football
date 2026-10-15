---
task_id: "carrybox-handoff-restart-20261014"
language: "zh-CN"
axes: ["L", "P", "C"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_walled.py", "tests/test_carrybox_walled.py", "tests/test_carrybox_x2.py", "scripts/rsl_rl/validate_carrybox_handoff.py", "scripts/rsl_rl/validate_carrybox_handoff.sh", "scripts/rsl_rl/benchmark_carrybox_warp.py", "handoff.txt", "docs/carrybox/handoff_20261014", "README.md", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth", "agent/plan/carrybox-handoff-restart-20261014.md", "agent/task/carrybox-handoff-restart-20261014.md", "agent/report/carrybox-handoff-restart-20261014.md", "agent/handoff/carrybox-handoff-restart-20261014.md"]
original_request: "重新改动之后重启训练"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION", "SENSOR_DRIVER"]
forbidden_scope: ["改动足球、共享G1资产、原始数据张量", "特权actor/critic或箱子真值进入AMP", "降低4096规模、深度频率/分辨率/遮挡或跳过验证以满足速度"]
steps: ["只读核验旧训练和源码，冻结合同", "实现handoff奖励/RSI/终止与传感器物理随机化", "CPU单元和数值边界检查", "保存旧进程快照后停止旧训练、GPU小规模与4096完整迭代验收", "正式新run迁移最新正式权重并核验新数据身份与训练日志", "更新差异说明、项目入口与交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/validate_carrybox_handoff.sh"}]
stop_conditions: ["测试两次范围内修复仍失败", "4096完整更新热身后超过6秒或出现非有限值/GPU错误", "GPU有限值/6秒目标未通过则不正式启动", "参考动作可达性未通过则不正式启动"]
safeguards: ["actor/critic只用深度本体，标签配对延迟冻结，AMP纯本体640维", "只迁移策略/辅助头，PPO/AMP/课程重建，严格环境和数据契约", "保留旧正式checkpoint/日志，PID身份匹配后才停止，验证模型不作正式初始化", "深度光轴单位和G1安装不改；50Hz48x27完整遮挡", "只对wall变体生效，不改CarryBox-v0/football", "无命中像素保持far，米域噪声后clamp到0.1–3m，边缘差分不跨边界", "冻结总计15帧含开始帧，深度和标签一致且reset清空，同帧读取幂等", "startup摩擦/默认角/COM，reset质量从默认值缩放，interval设置推扰；实际PhysX验收", "动作参考可达性必须验证；仅wall裁剪由5变9覆盖8.842最大动作及默认角偏移，不改物理关节限制", "严格保持成功指标独立于X2即时standup门控，成功不终止"]
expert_required: true
expert_brief: {"affected_call_path": ["wall cfg → MDP reset/rewards/depth → WalledCarryBoxEnv → CarryBox runner"], "critical_interfaces": ["高度减env_origins，torso世界线速度/局部角速度，G1手Box过滤力和hip/knee独立接触", "startup同步action offset；默认质量缩放；独立即时standup与严格保持统计"], "invariants": ["actor/critic只用深度本体，标签配对延迟冻结，AMP纯本体640维", "只迁移策略/辅助头，PPO/AMP/课程重建，严格环境和数据契约", "保留旧正式checkpoint/日志，PID身份匹配后才停止，验证模型不作正式初始化", "深度光轴单位和G1安装不改；50Hz48x27完整遮挡", "只对wall变体生效，不改CarryBox-v0/football"], "smallest_change_locus": ["wall专属cfg/MDP与tensor helper；原runner warm-start复用"], "mandatory_safeguards": ["actor/critic只用深度本体，标签配对延迟冻结，AMP纯本体640维", "只迁移策略/辅助头，PPO/AMP/课程重建，严格环境和数据契约", "保留旧正式checkpoint/日志，PID身份匹配后才停止，验证模型不作正式初始化", "深度光轴单位和G1安装不改；50Hz48x27完整遮挡", "只对wall变体生效，不改CarryBox-v0/football", "无命中像素保持far，米域噪声后clamp到0.1–3m，边缘差分不跨边界", "冻结总计15帧含开始帧，深度和标签一致且reset清空，同帧读取幂等", "startup摩擦/默认角/COM，reset质量从默认值缩放，interval设置推扰；实际PhysX验收", "动作参考可达性必须验证；仅wall裁剪由5变9覆盖8.842最大动作及默认角偏移，不改物理关节限制", "严格保持成功指标独立于X2即时standup门控，成功不终止"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/validate_carrybox_handoff.sh"], "blockers": ["GPU有限值/6秒目标未通过则不正式启动", "参考动作可达性未通过则不正式启动"]}
device_actions: []
real_device_authorized: false
---


按handoff.txt更新G1 wall3/wall4的RSI比例、完整奖励、双向roll终止及传感器/物理随机化。保留G1四帧深度/本体、无特权critic、纯本体AMP及新版15段数据。新环境契约revision6。验证后4096环境新run从最近正式权重warm-start；不恢复旧PPO/AMP。
专家只读复核已完成。测得拾箱最大abs(action)=8.84195，计默认角±0.01后需8.88195；wall专属裁剪9纳入同次任务契约，不改共享机器人。测试保持两条入口，专家的其他覆盖说明纳入safeguards。
