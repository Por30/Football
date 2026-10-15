---
task_id: "agilekickball-v5-randomization"
language: "zh-CN"
axes: ["C", "P", "A"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/kickball_randomization.py", "source/perceptual_ball/perceptual_ball/kickball_randomized_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v5.py", "tests/test_agilekickball_v5_randomization.py", "scripts/rsl_rl/smoke_agilekickball_v5.py", "scripts/rsl_rl/smoke_agilekickball_v5.sh", "scripts/rsl_rl/smoke_agilekickball_v5_randomization.sh", "docs/agilekickball_v5/README.md", "docs/agilekickball_v5/randomization", "README.md", "projects/README.md", "projects/football/README.md", "agent"]
artifact: "PLAN"
status: "DONE"
---

为v5增加训练域随机化。唯一只读专家wall4_perf_review已核对ImplicitActuator、官方事件与capture生命周期；保留既有相机profile，将随机化合同另列。GPU只做4环境短测，不停Wall4、不启动正式训练，不声称已验证真机效果。

实现与固定测试已完成，证据写入随机化验证目录，未启动正式训练。
