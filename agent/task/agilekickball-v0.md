---
task_id: "ENG-AGILEKICKBALL-V0-20260920"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
development_modes: ["SYSTEM_TUNING", "STATE_MACHINE"]
original_request: "以v0项目为基础系列任务 agilekickball 在v0的基础上加上来球速的课程学习 然后给我训练的命令；同时加上合适的reset逻辑，需要连续击球并且恢复平衡之后再发球"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball", "scripts/rsl_rl", "tests", "docs/agilekickball", "agent"]
forbidden_scope: ["改变v0奖励/观测/算法", "引入v2/v3任务设置", "长期训练或真实硬件", "修改旧checkpoint和参考动作"]
steps: ["确认v0课程与reset调用顺序", "新增速度课程及恢复后发球子类", "验证连续稳定、超时、部分reset和真实第二次发球", "交付训练命令和验证工件"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball.sh"}]
stop_conditions: ["测试失败两次后停止盲目重试并诊断", "真实设备或范围外修改需求"]
safeguards: ["只在下一次发球时使用新速度，不改飞行中球速度", "速度单位m/s，按全局控制步推进，不乘并行环境数", "课程上下界及进度有界，原v0不变", "不启动长期训练", "首次reset清空稳定计时、默认站姿RSI=0，连续稳定0.3秒才允许发球", "每球结束不写机器人状态、不清观测历史；只在episode reset重置机器人", "稳定代理包含重力z朝向、倾斜、高度、三维线速度/角速度、关节速度与双脚高度；不是接触力验证的平衡", "稳定中断清零，每次发球和进入等待阶段清零，不重复推进同一步", "球暂存远离机器人，reset清速度与事件；保留球结束本步的miss/success脉冲", "秒计时，不提前发球；5秒超时优先于同tick恢复，reset_buf为真禁止发球", "保留v0跌倒/倾倒/离anchor/自碰/非有限值终止", "60秒episode支持多次发球；smoke确认同episode第二球和默认姿态gate可达", "持续stand/AMP不证明连续击球已学会；只运行离线和小规模仿真验证"]
expert_required: true
expert_brief: {"affected_call_path": ["physics -> termination -> reward tick -> ready _serve; episode reset curriculum -> joints/root -> state reset"], "critical_interfaces": ["父类reset动态调用_serve；termination在reward tick前计算", "父类ball-end的miss pulse不能被同tick新发球清掉"], "invariants": ["仅Agile改变reset与episode长度，v0原配置/奖励/网络不变", "连续稳定、等待超时优先、同episode重复发球不重置robot"], "smallest_change_locus": ["mdp/agilekickball.py子类和专属配置；复用父类发球与奖励"], "mandatory_safeguards": ["首次reset清空稳定计时、默认站姿RSI=0，连续稳定0.3秒才允许发球", "每球结束不写机器人状态、不清观测历史；只在episode reset重置机器人", "稳定代理包含重力z朝向、倾斜、高度、三维线速度/角速度、关节速度与双脚高度；不是接触力验证的平衡", "稳定中断清零，每次发球和进入等待阶段清零，不重复推进同一步", "球暂存远离机器人，reset清速度与事件；保留球结束本步的miss/success脉冲", "秒计时，不提前发球；5秒超时优先于同tick恢复，reset_buf为真禁止发球", "保留v0跌倒/倾倒/离anchor/自碰/非有限值终止", "60秒episode支持多次发球；smoke确认同episode第二球和默认姿态gate可达", "持续stand/AMP不证明连续击球已学会；只运行离线和小规模仿真验证"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball.py", "bash scripts/rsl_rl/smoke_agilekickball.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

用户追加恢复后连续发球要求，合同更新为L+D/T2；复用单个只读专家接口审查。速度课程保留；新增默认站姿reset、连续稳定gate、5秒等待超时和60秒episode。CPU和真实smoke覆盖正常、漏球、部分reset、超时、第二球与teleport脉冲。
