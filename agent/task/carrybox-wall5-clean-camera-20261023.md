---
task_id: "carrybox-wall5-clean-camera-20261023"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_clean_camera_20261023", "projects/README.md", "projects/findbox/README.md", "logs/rsl_rl/g1_carrybox_depth/walled5", "agent/plan/carrybox-wall5-clean-camera-20261023.md", "agent/task/carrybox-wall5-clean-camera-20261023.md", "agent/report/carrybox-wall5-clean-camera-20261023.md", "agent/handoff/carrybox-wall5-clean-camera-20261023.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "重启一版本训练  去掉相机噪声 减少早期扰动 然后restart training"
development_modes: ["SYSTEM_TUNING", "ML_TRAINING"]
forbidden_scope: ["不修改football、共享相机/AMP/PPO实现、资产或训练数据", "不更改奖励/终止/RSI/PD/动作延迟，不删除旧run，不从旧权重恢复", "不将短测或正式启动等同于抖动或抓取收敛"]
steps: ["冻结旧run及源码，组合轴专家核对感知与契约边界", "仅wall5覆盖噪声参数及推扰课程，升级revision28", "执行既有CPU回归和64环境深度/推扰/更新恢复检查", "检查通过后停旧进程、从零启动4096环境并核对日志与首checkpoint", "记录变化、验证回执与运行快照，更新项目入口"]
tests: [{"command": "bash docs/carrybox/wall5_clean_camera_20261023/validate.sh"}, {"command": "bash docs/carrybox/wall5_clean_camera_20261023/start_and_verify.sh"}]
stop_conditions: ["身份/契约不一致或非有限值停止依赖操作", "每个测试最多两次范围内修复，保留失败回执", "验证通过且旧进程退出前不正式启动；严禁重复启动"]
safeguards: ["旧进程停止前匹配PID、命令和start ticks，保留旧日志和checkpoint", "关闭Gaussian/stereo/边缘/孔洞/延迟/冻结/外参误差；不修改真实遮挡、分辨率、相机安装名义位姿或米制预处理", "推扰仍为增量且保留最大幅度，5000轮后用10000轮爬升，按课程相对锚点", "同版本严格恢复，rev27完整恢复须被拒绝；actor仍无特权，critic123", "正式fresh4096/seed42/max40000，检查更新、Normalizer、有限值及热身每轮6秒内", "keep shared helper/RNG draws unchanged", "diff against this task before_source, preserve existing dirty edits", "validate before identity-matched stop; fresh launch no resume/warm-start"]
expert_required: true
expert_brief: {"affected_call_path": ["wall5 cfg → WarpDepthCamera → captured_pair → corrupt_depth_m → PairedDepthBuffer → actor/paired labels", "reset_camera, additive push curriculum, checkpoint strict restore"], "critical_interfaces": ["11 camera perturbation controls covered; max_delay0 single slot, freeze_max1 count0", "full contract checked before load; schema2/revision28"], "invariants": ["metres optical .1–3m,48×27,50Hz,4frames,real occlusion unchanged", "actor depth/proprio,critic123,AMP15/60 and labels unchanged", "additive COM pushes,interval/final amplitude and other physical randomization unchanged", "curriculum process anchor retained"], "smallest_change_locus": ["only wall5 cfg parameter overrides and wall5 contract revision"], "mandatory_safeguards": ["keep shared helper/RNG draws unchanged", "diff against this task before_source, preserve existing dirty edits", "validate before identity-matched stop; fresh launch no resume/warm-start"], "minimal_tests": ["bash docs/carrybox/wall5_clean_camera_20261023/validate.sh", "bash docs/carrybox/wall5_clean_camera_20261023/start_and_verify.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

仅wall5 revision28降低感知/早期外部推扰难度：关闭全部人工深度扰动与安装误差，保留米制、头部相机、ray-cast、自遮挡与障碍遮挡；推扰5000轮warmup＋10000轮ramp。奖励/PD/动作延迟/RSI/碰撞/终止/AMP/网络保持。短测通过后停止身份匹配的旧进程，4096环境seed42从零训练，保留所有历史模型。