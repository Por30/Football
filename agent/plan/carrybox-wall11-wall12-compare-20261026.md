---
task_id: "carrybox-wall11-wall12-compare-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "READY"
allowed_paths: ["docs/carrybox/wall11_wall12_compare_20261026", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall11-wall12-compare-20261026.md", "agent/task/carrybox-wall11-wall12-compare-20261026.md", "agent/report/carrybox-wall11-wall12-compare-20261026.md", "agent/handoff/carrybox-wall11-wall12-compare-20261026.md"]
---

比较wall11无辅助监督与wall12辅助监督系数1的现有20000轮正式训练。核验两者配置/数据可比性，读取训练曲线并做最终model19999的相同种子/初态首回合工程回放。结论仅限这两个训练run，分开回归精度与任务效果。
