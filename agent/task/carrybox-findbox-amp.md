---
task_id: "carrybox-findbox-amp"
language: "zh-CN"
axes: ["E", "L", "S"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["ML_DATA_PIPELINE", "ML_TRAINING", "SIMULATOR_EXTENSION"]
original_request: "/home/cao/perceptual_ball/findbox 用这个数据集 接入amp"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py", "tests/test_carrybox_amp.py", "scripts/rsl_rl/smoke_carrybox.py", "docs/carrybox", "findbox/amp_manifest.json", "README.md", "agent"]
forbidden_scope: ["更改原始findbox运动片段", "增加搬运/放下任务阶段", "actor/critic增加特权观测", "长期训练或真实设备操作", "无关踢球改动"]
steps: ["确认并冻结数据schema/采样权重", "接入本体AMP特征与运动库", "集成判别器/奖励/terminal窗口和checkpoint", "执行CPU与RTX集成测试", "更新使用说明及交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/smoke_carrybox.sh"}]
stop_conditions: ["数据映射或fps无法确定", "原范围内两次修复后冻结测试仍失败", "需要真实设备或范围扩张"]
safeguards: ["validate finite shapes/hashes/joint mapping", "recompute per-clip angular/joint velocities", "score and train same post-action terminal-correct windows", "checkpoint discriminator/optimizer/dataset identity; lazy dataset loading for inference"]
expert_required: true
expert_brief: {"affected_call_path": ["findbox -> FindBoxMotionLibrary -> CarryBoxPPO AMP", "CarryBoxEnv amp history -> terminal snapshot -> reward/discriminator"], "critical_interfaces": ["60Hz xyzw source; joint_id named order; 50Hz chronological 10-frame windows"], "invariants": ["actor/critic observation whitelist unchanged", "AMP contains no box or base linear velocity", "no cross-clip/cross-reset windows"], "smallest_change_locus": ["source/perceptual_ball/perceptual_ball/carrybox_amp.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox.py"], "mandatory_safeguards": ["validate finite shapes/hashes/joint mapping", "recompute per-clip angular/joint velocities", "score and train same post-action terminal-correct windows", "checkpoint discriminator/optimizer/dataset identity; lazy dataset loading for inference"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/smoke_carrybox.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

使用64维本体运动帧，10帧窗口；原数据只读，manifest补足60Hz/xyzw和关节顺序。按行走40%、拾起40%、持箱20%平衡采样，不添加搬运阶段。未填满的reset窗口不参与AMP评分/训练。
