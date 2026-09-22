---
task_id: "ENG-AGILE-V1-20260921"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["STATE_MACHINE", "SYSTEM_TUNING"]
original_request: "在v0 基础上新建v1任务 进一步提高课程 成功率上去了就进入下一段 提高速度上线 0。4到5。0米每秒"
allowed_paths: ["source/perceptual_ball/perceptual_ball", "scripts/rsl_rl", "tests", "docs/agilekickball_v1", "agent"]
forbidden_scope: ["更改v0训练行为或旧checkpoint", "重构视觉/网络/奖励", "长期训练和真实硬件"]
steps: ["新增独立v1状态与配置注册", "实现不可重复单球结算及挑战窗口晋级", "checkpoint保存恢复与play冻结，支持跨任务checkpoint初始化", "CPU边界及真实仿真采样/加载/学习smoke", "交付训练命令和校验工件"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v1.sh"}]
stop_conditions: ["两次失败后停止盲目重试并诊断", "超过16环境1000控制步或2轮PPO更新验证预算", "真实硬件或范围外改动"]
safeguards: ["v0行为不变；v1网络/输入/奖励/恢复gate沿用v0", "下限0.4，上限逐级0.8/1.2/1.6/2/2.5/3/3.5/4/4.5/5，仅改未来发球", "stage0所有球为challenge；后续50%采样概率不能替代挑战样本数量要求", "每球保存stage/challenge/速度，幂等结算，终止优先，旧stage结果不计新stage窗口", "统计整个控制步提交批次，可超出窗口下限但不丢弃、不重复使用或挑选成功样本", "驻留为累计控制步，保存checkpoint，晋级清窗口及连续达标数，失败窗口清连续数", "回球位移沿击球时冻结向外方向，参考候选击球位置；足部位置和速度使用body_link世界系", "候选使用父tick更新前速度跳变或父success脉冲，足部主动运动代理不是实际接触传感器", "完成恢复再冻结成功；跌倒、episode超时、恢复超时的开放球计失败", "checkpoint仅保存课程窗口不保存物理开放球；旧在途样本标为运行截断，校验schema、配置和计数关系", "v0权重加载到v1课程从stage0开始；play恢复阶段但冻结窗口与晋级", "固定1.3–2m发球距离；测实际5m/s发球不宣称5m/s成功踢球", "仿真只验证采样/加载/更新链路；构造状态晋级与自然学习成功率分开报告"]
expert_required: true
expert_brief: {"affected_call_path": ["v1 reset/tick/serve -> 单球结算 -> 窗口 -> 晋级 -> checkpoint/play"], "critical_interfaces": ["父reset动态_serve，父tick内部可能重发，先结算旧球", "runner不能用v0曝光课程覆盖v1阶段", "termination在tick前，稳定成功不能覆盖终止失败"], "invariants": ["v0行为不变；v1网络/输入/奖励/恢复gate沿用v0", "下限0.4，上限逐级0.8/1.2/1.6/2/2.5/3/3.5/4/4.5/5，仅改未来发球", "stage0所有球为challenge；后续50%采样概率不能替代挑战样本数量要求", "每球保存stage/challenge/速度，幂等结算，终止优先，旧stage结果不计新stage窗口", "统计整个控制步提交批次，可超出窗口下限但不丢弃、不重复使用或挑选成功样本", "驻留为累计控制步，保存checkpoint，晋级清窗口及连续达标数，失败窗口清连续数", "回球位移沿击球时冻结向外方向，参考候选击球位置；足部位置和速度使用body_link世界系", "候选使用父tick更新前速度跳变或父success脉冲，足部主动运动代理不是实际接触传感器", "完成恢复再冻结成功；跌倒、episode超时、恢复超时的开放球计失败", "checkpoint仅保存课程窗口不保存物理开放球；旧在途样本标为运行截断，校验schema、配置和计数关系", "v0权重加载到v1课程从stage0开始；play恢复阶段但冻结窗口与晋级", "固定1.3–2m发球距离；测实际5m/s发球不宣称5m/s成功踢球", "仿真只验证采样/加载/更新链路；构造状态晋级与自然学习成功率分开报告"], "smallest_change_locus": ["v1 state/config/注册；共享采样helper和ready helper；runner课程分派"], "mandatory_safeguards": ["v0行为不变；v1网络/输入/奖励/恢复gate沿用v0", "下限0.4，上限逐级0.8/1.2/1.6/2/2.5/3/3.5/4/4.5/5，仅改未来发球", "stage0所有球为challenge；后续50%采样概率不能替代挑战样本数量要求", "每球保存stage/challenge/速度，幂等结算，终止优先，旧stage结果不计新stage窗口", "统计整个控制步提交批次，可超出窗口下限但不丢弃、不重复使用或挑选成功样本", "驻留为累计控制步，保存checkpoint，晋级清窗口及连续达标数，失败窗口清连续数", "回球位移沿击球时冻结向外方向，参考候选击球位置；足部位置和速度使用body_link世界系", "候选使用父tick更新前速度跳变或父success脉冲，足部主动运动代理不是实际接触传感器", "完成恢复再冻结成功；跌倒、episode超时、恢复超时的开放球计失败", "checkpoint仅保存课程窗口不保存物理开放球；旧在途样本标为运行截断，校验schema、配置和计数关系", "v0权重加载到v1课程从stage0开始；play恢复阶段但冻结窗口与晋级", "固定1.3–2m发球距离；测实际5m/s发球不宣称5m/s成功踢球", "仿真只验证采样/加载/更新链路；构造状态晋级与自然学习成功率分开报告"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v1.py", "bash scripts/rsl_rl/smoke_agilekickball_v1.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

已采用单个只读L+D专家审查。窗口计数用固定最小4096/1024，整步批次完整计入，驻留限制避免大并行快速连跳。v1课程成功严格于v0奖励代理，但不改变奖励函数。首选从既有v0已学权重开始v1；也提供从头命令。
