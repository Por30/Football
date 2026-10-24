---
task_id: "carrybox-wall5-amp-reward-audit-20261023"
language: "zh-CN"
axes: ["L", "C", "E"]
risk_tier: "T2"
allowed_paths: ["docs/carrybox/wall5_amp_reward_audit_20261023", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-amp-reward-audit-20261023.md", "agent/task/carrybox-wall5-amp-reward-audit-20261023.md", "agent/report/carrybox-wall5-amp-reward-audit-20261023.md", "agent/handoff/carrybox-wall5-amp-reward-audit-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "在原地抽搐 根本没有走向箱子 /home/cao/perceptual_ball/outputs/carrybox/wall5_play4_rev22_20261021/wall5_rev22_model6400_4robots_high20s.mp4 看一下当时这段效果 码码能走到箱子边上 你排查下下是什么原因的的的 当前amp有没有生效 分段的奖励函数逻辑是否正常"
development_modes: ["MODEL_DEPLOYMENT", "CONTROL_LOOP"]
forbidden_scope: ["不修改生产源码、数据、模型或训练进程", "不把参考持箱当拾取成功；不把跨版本日志当单因素因果"]
steps: ["锁定两模型、录像、正式进程及源码身份", "核对奖励/AMP调用和同轮日志，检查视频行为", "同初态新旧策略诊断回放，记录奖励门控、AMP和动作", "校验并保存有证据的结论和项目入口"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_amp_reward_audit_20261023/analyze.py"}, {"command": "bash docs/carrybox/wall5_amp_reward_audit_20261023/probe.sh"}]
stop_conditions: ["身份/契约不符停止", "显存不足6GiB不运行", "失败最多两次原范围修复，保留失败记录", "初态、契约或有限值不符停止对应配对归因"]
safeguards: ["正式训练和已有产物保持", "新旧策略比较只转移旧权重，明确环境差异", "统一初态、非reset统计、终止AMP替换、dt和权重单位核对", "AMP模型与归一化冻结，训练日志核验独立", "实际执行回执，结论不越过诊断证据", "正式训练和已有产物保持", "区分AMP接入、实际更新、奖励贡献和行为有效性", "统一初态、相同课程、均值动作和冻结AMP；旧模型仅转移权重", "排除reset后污染，核对终止AMP和dt/权重", "多因素改变不能直接指定唯一原因"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["Wall5 task geometry→RewardManager(weight*dt)→PPO _process_amp; parent PPO _update_amp performs optimizer.step"], "critical_interfaces": ["travel XY .8→.6 and reach 3D .98→.9 create a handoff valley; inherited held smoothing/standup do not require bilateral contact", "AMP style clips to zero at D<=-1; input normalization/clamp and .7m box-z cap remain"], "invariants": ["Mixed=.75*task_raw+.125*style; task dt once, AMP no dt; terminal windows before reset; normalization frozen for rollout"], "smallest_change_locus": ["Read-only audit scripts and evidence only"], "mandatory_safeguards": ["正式训练和已有产物保持", "区分AMP接入、实际更新、奖励贡献和行为有效性", "统一初态、相同课程、均值动作和冻结AMP；旧模型仅转移权重", "排除reset后污染，核对终止AMP和dt/权重", "多因素改变不能直接指定唯一原因"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_amp_reward_audit_20261023/analyze.py", "bash docs/carrybox/wall5_amp_reward_audit_20261023/probe.sh"], "blockers": ["初态、契约或有限值不符停止对应配对归因"]}
---

只读核对用户指定rev22 model6400录像与当前rev28策略，确认AMP实际更新/奖励贡献、接近到抓取的分段奖励与动作抖动。复用现有读取、策略/判别器加载和仿真诊断helper；新诊断产物单独保存，不改任务、数据、权重或训练进程。以源码、日志和受控回放区分已确认缺陷与待验证归因。
