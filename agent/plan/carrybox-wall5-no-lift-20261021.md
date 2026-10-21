---
task_id: "carrybox-wall5-no-lift-20261021"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "PLAN"
status: "FROZEN"
allowed_paths: ["docs/carrybox/wall5_no_lift_20261021", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-no-lift-20261021.md", "agent/task/carrybox-wall5-no-lift-20261021.md", "agent/report/carrybox-wall5-no-lift-20261021.md", "agent/handoff/carrybox-wall5-no-lift-20261021.md"]
---

只读诊断当前wall5未拾箱：日志近250轮与model回放分开，量化接近/下蹲/手箱接触/离地/奖励分项。保持checkpoint原80/0/20及课程，源码新75/5/20不回退，不操作正式训练。结果用于工程定位，不作为因果实验或总体成功率。
