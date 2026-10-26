---
task_id: "carrybox-wall11-wall12-compare-20261026"
language: "zh-CN"
axes: ["L"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
original_request: "看一下wall11 12的对比 有无aux头效果是否改善"
allowed_paths: ["docs/carrybox/wall11_wall12_compare_20261026", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall11-wall12-compare-20261026.md", "agent/task/carrybox-wall11-wall12-compare-20261026.md", "agent/report/carrybox-wall11-wall12-compare-20261026.md", "agent/handoff/carrybox-wall11-wall12-compare-20261026.md"]
forbidden_scope: ["修改任何生产代码、checkpoint、训练数据或已有评估工件", "启动正式训练或停止/重启其他进程", "把相关帧当独立回合、把参考持箱起点当从地面成功", "根据单个训练seed声称普遍因果收益"]
development_modes: ["MODEL_DEPLOYMENT"]
steps: ["核验两次run配置、数据、最终模型和指标语义", "提取全训练曲线及末1000轮统计并检查有限性", "顺序回放两个最终模型，各64环境x2种子x20秒，仅统计每env首回合", "校验配对初态并按地面/参考起点汇总，保存曲线、结论和工程记录"]
tests: [{"command": "bash docs/carrybox/wall11_wall12_compare_20261026/analyze.sh"}, {"command": "bash docs/carrybox/wall11_wall12_compare_20261026/evaluate.sh"}, {"command": "bash docs/carrybox/wall11_wall12_compare_20261026/summarize.sh"}]
stop_conditions: ["同一问题两次范围内修复后仍失败", "GPU剩余显存不足6000MiB", "发现其他实质配置差异无法归因于aux"]
safeguards: ["均比较model19999；actor均值动作、原噪声墙柱/域随机化/终止，aux不在推理动作路径", "种子12345和67890，各64环境首回合；配对检查机器人/箱体/障碍/域随机化/actor初始观测", "地面起点按from_ground真值；持续双手持箱0.5秒和任务严格连续2秒成功分别报告", "终止前采样，首次reset后忽略，最多1000控制步；参考起点单列", "训练success_fraction是累计值，末段均值不可直接称最终成功率；单seed正式run不作多seed因果结论", "已有足球PID3814037保持运行，短测只读模型，所有产物落docs"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

冻结三条检查：日志/契约分析、配对回放、初态与汇总验证。工程比较不更改策略或任务，不追加训练。
