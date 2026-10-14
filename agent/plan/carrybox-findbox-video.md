---
task_id: "carrybox-findbox-video"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
artifact: "PLAN"
status: "DRAFT"
allowed_paths: ["scripts/visualize_findbox.py", "scripts/visualize_findbox.sh", "outputs/carrybox/findbox_dataset", "docs/carrybox/dataset_visualization", "projects/carrybox/README.md", "projects/README.md", "agent"]
---

回放findbox全17片段并录制MP4；使用现有G1、具名关节映射与xyzw转wxyz。仅可视化，不修改训练/原数据/已有进程。
