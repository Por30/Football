---
task_id: "carrybox-wall4-after-football"
language: "zh-CN"
axes: ["E", "L", "A"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "等待后台football任务训练成成之后 你启动wall4训练"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.py", "scripts/rsl_rl/smoke_carrybox_walled.sh", "scripts/rsl_rl/queue_wall4.py", "tests/test_carrybox_queue.py", "docs/carrybox/wall4_queue", "projects", "README.md", "agent", "logs/rsl_rl/g1_carrybox_depth"]
forbidden_scope: ["停止或重启既有足球训练", "修改足球或共享训练算法", "使用验证模型初始化正式训练", "真实设备操作", "失败后自动重试长训"]
development_modes: ["BUG_FIX", "TOOLING"]
steps: ["核实足球身份及只读专家建议", "修正运动学reset API并冻结实际训练预检", "验证CPU门控及4环境真实wall训练", "建立单次后台等待器并绑定源码及就绪证据", "足球正常结束后128环境预检通过才启动正式wall4", "保存状态和项目交接"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/smoke_carrybox_walled.sh"}, {"command": "/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/queue_wall4.py --check-only"}]
stop_conditions: ["范围内两次修复后GPU短测仍失败", "需干扰足球才能继续", "足球缺少完整最终checkpoint或有致命结束错误", "源码或数据身份变化", "正式启动状态不明确或重复运行"]
safeguards: ["运动学对象只写pose，动态物体保持state写入", "后台锁和原子状态；PID+starttime+bootid绑定", "最终模型CPU完整加载并检查iteration及finite", "资源不足则等待；128环境预检有timeout且必须检查完成标记", "单次启动意图在Popen前持久化；不自动重启失败训练"]
expert_required: true
expert_brief: {"affected_call_path": ["reset_scene/smoke对运动学刚体完整state写入到PhysX速度API", "独立后台进程只读核验足球完成，再检查wall4就绪"], "critical_interfaces": ["运动学障碍用pose API；动态机器人箱子保留state API", "真实runner.learn跨更新、checkpoint、reset；目标规模128环境"], "invariants": ["actor/critic仅深度和本体，AMP及足球接口不改", "PID消失不等于训练完成；不得停止足球"], "smallest_change_locus": ["walled MDP和smoke中的运动学重置", "独立标准库串行启动器与状态文件"], "mandatory_safeguards": ["运动学对象只写pose，动态物体保持state写入", "后台锁和原子状态；PID+starttime+bootid绑定", "最终模型CPU完整加载并检查iteration及finite", "资源不足则等待；128环境预检有timeout且必须检查完成标记", "单次启动意图在Popen前持久化；不自动重启失败训练"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/smoke_carrybox_walled.sh", "/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/queue_wall4.py --check-only"], "blockers": ["足球缺少完整最终checkpoint或有致命结束错误", "源码或数据身份变化", "正式启动状态不明确或重复运行"]}
device_actions: []
real_device_authorized: false
---

用户已授权等待当前足球正式训练完成后启动wall4。先修复运动学刚体速度API违规，验证实际runner跨PPO更新、保存及reset，再以持久后台串行启动器等待足球最终49999 checkpoint完整性。正式训练采用wall4默认128环境、40000轮、seed42，从头训练。足球运行中只做4环境有界短测；128环境预检在足球完成后执行。只读组合轴专家确认API违规，未证明其为CUDA700唯一根因。不得将静态遮挡审计当作动态训练就绪。
