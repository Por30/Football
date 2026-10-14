---
task_id: "agilekickball-v5-depth"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_agilekickball_v5.sh", "scripts/rsl_rl/smoke_agilekickball_v5.py", "scripts/rsl_rl/smoke_agilekickball_v5.sh", "tests/test_agilekickball_v5.py", "docs/agilekickball_v5", "projects/football/README.md", "projects/README.md", "README.md", "agent", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/ball_metrics.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py"]
artifact: "PLAN"
status: "DRAFT"
---

新增独立v5继承v4回球流程，替换深度为完整场景光线投射。唯一只读专家wall4_perf_review指出旧feedback门控只能解释为有效深度新近度，不能作球可见性。保留数学实现，明确新语义。尚无实机CameraInfo/光学外参与预处理配置，先提供名义profile与可复用部署预处理，实机一致性待标定；小规模验证模型只保存在docs。

实现前专家范围补充：v2 warm-start增加v5目标拒绝；指标按v5 scene_depth标记改名valid_depth，避免误报球可见性。v4默认行为不变。
