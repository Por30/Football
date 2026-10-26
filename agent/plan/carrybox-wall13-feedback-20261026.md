---
task_id: "carrybox-wall13-feedback-20261026"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "PLAN"
status: "READY"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall13.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall13.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall13_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall13.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "tests/test_carrybox_wall13.py", "docs/carrybox/wall13_feedback_20261026", "docs/carrybox/wall13_20261026/README.md", "projects/findbox/README.md", "projects/README.md", "agent/plan/carrybox-wall13-feedback-20261026.md", "agent/task/carrybox-wall13-feedback-20261026.md", "agent/report/carrybox-wall13-feedback-20261026.md", "agent/handoff/carrybox-wall13-feedback-20261026.md"]
---

将wall13从仅辅助监督升级为显式位姿反馈：CNN原始128维与同源预测9维合并，经137→128融合后输入Actor，部署保留回归头和融合层。训练/部署端到端一致，其他设置继承wall12。生成中文SVG/PNG/Mermaid说明图。P+L T2由既有wall12_contract专家完成只读审计，无阻塞。
