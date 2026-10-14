---
task_id: "agilekickball-v5-depth"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py", "source/perceptual_ball/perceptual_ball/kickball_depth.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_agilekickball_v5.sh", "scripts/rsl_rl/smoke_agilekickball_v5.py", "scripts/rsl_rl/smoke_agilekickball_v5.sh", "tests/test_agilekickball_v5.py", "docs/agilekickball_v5", "projects/football/README.md", "projects/README.md", "README.md", "agent", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/ball_metrics.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py"]
artifact: "TASK"
status: "FROZEN"
original_request: "同时新建kickballv5 深度图需要和实机保持一致 考虑和机人人自身的遮挡"
development_modes: ["SENSOR_DRIVER", "SIMULATOR_EXTENSION", "ML_TRAINING"]
forbidden_scope: ["改v4奖励或足球critic接口", "停止Wall4或启动v5正式训练", "无标定文件声称实机验收"]
steps: ["审查部署/观测/版本边界", "实现v5网格深度、profile和版本契约", "CPU回归及4环境短训/遮挡/reset/export验证", "记录证据、标定缺口与训练命令"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v5.py -v"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v5.sh"}]
safeguards: ["v4数值行为、ID、奖励与AMP保持；Wall4进程不动", "v5全机身可见mesh与Ball/ground最近交点，光轴米制8帧；无真值mask", "名义安装参数不冒充实机标定；缺标定不能声明实机一致", "版本/深度契约不匹配拒绝resume/play；导出包含相机契约", "只做小规模仿真短测，不启动v5正式训练"]
stop_conditions: ["缺失实机标定时不得声明已完成实机一致性验收", "任一遮挡/恢复/导出检查失败不得启动v5正式训练", "冻结测试失败最多两次范围内修复；不放宽断言"]
expert_required: true
expert_brief: {"affected_call_path": ["v5 scene -> Warp sensor -> observation -> state feedback PPO -> checkpoint/export"], "critical_interfaces": ["OpenCV整数像素中心/光轴米制；历史与reset；新课程key+完整深度契约"], "invariants": ["v4数值行为、ID、奖励与AMP保持；Wall4进程不动", "v5全机身可见mesh与Ball/ground最近交点，光轴米制8帧；无真值mask", "名义安装参数不冒充实机标定；缺标定不能声明实机一致", "版本/深度契约不匹配拒绝resume/play；导出包含相机契约", "只做小规模仿真短测，不启动v5正式训练"], "smallest_change_locus": ["v5配置/MDP/profile；共享sensor增加保持默认值的对象选择与内参"], "mandatory_safeguards": ["v4数值行为、ID、奖励与AMP保持；Wall4进程不动", "v5全机身可见mesh与Ball/ground最近交点，光轴米制8帧；无真值mask", "名义安装参数不冒充实机标定；缺标定不能声明实机一致", "版本/深度契约不匹配拒绝resume/play；导出包含相机契约", "只做小规模仿真短测，不启动v5正式训练"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v5.py -v", "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash scripts/rsl_rl/smoke_agilekickball_v5.sh"], "blockers": ["缺失实机标定时不得声明已完成实机一致性验收", "任一遮挡/恢复/导出检查失败不得启动v5正式训练"]}
device_actions: []
real_device_authorized: false
---

新增独立v5继承v4回球流程，替换深度为完整场景光线投射。唯一只读专家wall4_perf_review指出旧feedback门控只能解释为有效深度新近度，不能作球可见性。保留数学实现，明确新语义。尚无实机CameraInfo/光学外参与预处理配置，先提供名义profile与可复用部署预处理，实机一致性待标定；小规模验证模型只保存在docs。

实现前专家范围补充：v2 warm-start增加v5目标拒绝；指标按v5 scene_depth标记改名valid_depth，避免误报球可见性。v4默认行为不变。
