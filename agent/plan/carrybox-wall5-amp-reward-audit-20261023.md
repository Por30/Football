---
task_id: "carrybox-wall5-amp-reward-audit-20261023"
language: "zh-CN"
axes: ["L", "C", "E"]
risk_tier: "T2"
allowed_paths: ["docs/carrybox/wall5_amp_reward_audit_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-amp-reward-audit-20261023.md", "agent/task/carrybox-wall5-amp-reward-audit-20261023.md", "agent/report/carrybox-wall5-amp-reward-audit-20261023.md", "agent/handoff/carrybox-wall5-amp-reward-audit-20261023.md"]
artifact: "PLAN"
status: "READY"
---

只读核对用户指定rev22 model6400录像与当前rev28策略，确认AMP实际更新/奖励贡献、接近到抓取的分段奖励与动作抖动。复用现有读取、策略/判别器加载和仿真诊断helper；新诊断产物单独保存，不改任务、数据、权重或训练进程。以源码、日志和受控回放区分已确认缺陷与待验证归因。
