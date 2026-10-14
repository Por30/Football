---
task_id: "AGILE-V3-STABILITY-FIX-20261008"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_outcome_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3_outcome.py", "tests/test_state_feedback.py", "tests/test_agilekickball_v3.py", "tests/test_agilekickball_v3_outcome.py", "tests/test_contact_outcome.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "README.md", "logs", "scripts/rsl_rl/train.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_feedback_legacy_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3_feedback_legacy.py", "docs/agilekickball_v3/stability_fix_20261008", "agent/plan/agilekickball-v3-stability-fix.md", "agent/task/agilekickball-v3-stability-fix.md", "agent/report/agilekickball-v3-stability-fix.md", "agent/handoff/agilekickball-v3-stability-fix.md"]
---

失败run完成50000轮但恢复为0；实际环境配置无漂移。同条件回放关闭残差仍失败。真实512个状态中位置logstd全部硬截断，NLL对encoder梯度为归一化MSE的1368.6倍。修复直接切断NLL到主encoder的路径，减小预测头更新/动作修正，使用平滑保守方差；从v2显式初始化保留恢复能力。保留物理任务，验证后按用户授权后台重新训练。
