---
task_id: "carrybox-wall5-training-v12-20261017"
language: "zh-CN"
axes: ["E", "P", "L", "C"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "用户要求将G1 wall5与X2对照建议应用wall5：60维含箱相对位置AMP与Normalizer、可见范围辅助mask及coef0.05–0.1、roll>=0.8及跌倒罚、adaptive KL.01/entropy.01/std1/5epoch/MLP512256256、loco.8；资产PD与限制单独验证。"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION"]
allowed_paths: ["AGENTS.md", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/carrybox_raycast.py", "source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "tests/test_carrybox_wall5.py", "tests/test_carrybox_ground.py", "tests/test_carrybox_raycast.py", "tests/test_carrybox_training_v12.py", "docs/carrybox/wall5_training_v12_20261017", "agent/plan/carrybox-wall5-training-v12-20261017.md", "agent/task/carrybox-wall5-training-v12-20261017.md", "agent/report/carrybox-wall5-training-v12-20261017.md", "agent/handoff/carrybox-wall5-training-v12-20261017.md"]
forbidden_scope: ["修改原始数据、football/wall3/4训练行为、共享G1资产PD", "向actor/critic泄漏箱子真值", "正式训练启动或停止后台football", "将短测写成收敛或因果证据"]
steps: ["核对专家/live坐标与旧数据", "实现wall5 60D与可恢复Normalizer", "可见监督mask和PPO/终止/RSI配置", "CPU合同/共享回归验证", "4环境PPOAMP保存恢复与传感器短测", "工件与项目说明"]
tests: [{"command": "bash docs/carrybox/wall5_training_v12_20261017/check.sh"}, {"command": "bash docs/carrybox/wall5_training_v12_20261017/smoke.sh"}]
stop_conditions: ["GPU空闲<4096MiB", "设备错误或测试两次范围内修复后仍失败", "出现数据破坏或影响正式football"]
safety_boundaries: ["无实机动作", "4env GPU最多600s；不操作后台正式训练"]
expert_required: true
expert_brief: {"affected_call_path": ["wall5 60D AMP/Normalizer/PPO与配对监督；共享默认保持"], "critical_interfaces": ["五末端palm/pitch_ankle/mid360；root link原点；世界位移旋转到pelvis；角速度四元数差分；tan x/normal z去yaw旋转"], "invariants": ["actor/critic仅depth+proprio；ground13数据不可变；RSI 0..31；全身碰撞保持"], "smallest_change_locus": ["wall5 helpers与配置；共享PPO hook与opt-in Warp hits"], "mandatory_safeguards": ["Normalizer raw统计持久化；mask与延迟冻结配对；fall排除timeout/旧flag；revision12拒绝旧模型；保留端点FK残差3.86mm记录"], "minimal_tests": ["bash docs/carrybox/wall5_training_v12_20261017/check.sh", "bash docs/carrybox/wall5_training_v12_20261017/smoke.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

测试命令冻结；用户本次明确授权箱子相对位置进入训练专用AMP。专家已只读核验13段坐标/末端/速度，不复制源Euler速度和归一化反馈错误。
