---
task_id: "carrybox-wall5-ground-20261017"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "把数据集里抱起箱子的数据只留下箱子在地上的部分 reset的候候箱子也全都是在地上到到地上"
development_modes: ["ML_DATA_PIPELINE", "SIMULATOR_EXTENSION"]
allowed_paths: ["docs/carrybox/wall5_ground_20261017", "source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup", "source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md", "source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_ground.py", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-ground-20261017.md", "agent/task/carrybox-wall5-ground-20261017.md", "agent/report/carrybox-wall5-ground-20261017.md", "agent/handoff/carrybox-wall5-ground-20261017.md"]
forbidden_scope: ["改动原15段/旧快照/足球数据", "改变wall3/4 reset默认行为或共享G1资产", "修改奖励/PPO/相机接口、泄漏特权信息", "启动/停止/重启正式训练或将短测当作收敛"]
steps: ["保留原数据并明确ground profile语义", "实现wall5地面RSI候选与全贴地reset，取消平台/hold初始化", "生成版本化数据profile及checkpoint合同", "CPU数据与边界验证", "GPU四环境reset/更新/恢复短测及项目记录"]
tests: [{"command": "bash docs/carrybox/wall5_ground_20261017/check.sh"}, {"command": "bash docs/carrybox/wall5_ground_20261017/smoke.sh"}]
stop_conditions: ["未明确数据保留语义时暂停依赖它的数据筛选", "所有地面候选无效、非有限物理状态、明显穿插或旧合同静默通过则停止修复", "可用显存不足4GiB不启动smoke；超时600秒停止，不升级训练规模"]
safeguards: ["数据语义答复前不执行依赖选择的数据筛除或裁剪；原15段manifest/PT逐字节保留", "AMP完整拾起片段与RSI离地前连续帧分开处理，不平移高位片段冒充地面动作", "wall5箱底按旋转后extent离地5mm；保留机器人脚底修正，不向下移机器人；partial reset不改存活环境", "hold AMP保留，hold RSI禁用；无有效地面帧时明确失败；不得读取被裁范围外帧", "保留全身碰撞和29DOF、60/50Hz、10帧AMP、深度/本体/监督信息边界；football与wall3/4数据/reset合同不变", "移除wall5平台时同步Warp目标及reset引用", "小环境覆盖全部候选RSI帧的手/前臂/膝/躯干碰撞穿插与初步接触有限值，首reset/自动/partial reset、yaw/tilt、观测历史", "小规模PPO/AMP更新、新checkpoint恢复与旧合同拒绝；不启动正式训练，不停止后台进程"]
expert_required: true
expert_brief: {"affected_call_path": ["wall5 reset -> common initialize_reference/reset_scene -> PhysX/Warp", "wall5 AMP/RSI -> 独立ground profile -> checkpoint身份"], "critical_interfaces": ["box .30x.30x.25; reference z=base_height+.05+box_pos_local.z", "原15段必须保留；ground profile独立，三组AMP仍完整", "地面候选按初始20帧中位箱底±.02m和首次抬升5mm前连续帧"], "invariants": ["所有wall5 reset箱底距各自地面5mm", "机器人脚底修正、partial reset、全身碰撞和无特权策略保持", "wall3/4以及football不切换数据或reset"], "smallest_change_locus": ["wall5配置/契约与纯张量筛帧helper", "common reset仅默认关闭的ground分支和显式reference dataset入口", "独立ground数据profile及映射/manifest文档"], "mandatory_safeguards": ["数据语义答复前不执行依赖选择的数据筛除或裁剪；原15段manifest/PT逐字节保留", "AMP完整拾起片段与RSI离地前连续帧分开处理，不平移高位片段冒充地面动作", "wall5箱底按旋转后extent离地5mm；保留机器人脚底修正，不向下移机器人；partial reset不改存活环境", "hold AMP保留，hold RSI禁用；无有效地面帧时明确失败；不得读取被裁范围外帧", "保留全身碰撞和29DOF、60/50Hz、10帧AMP、深度/本体/监督信息边界；football与wall3/4数据/reset合同不变", "移除wall5平台时同步Warp目标及reset引用", "小环境覆盖全部候选RSI帧的手/前臂/膝/躯干碰撞穿插与初步接触有限值，首reset/自动/partial reset、yaw/tilt、观测历史", "小规模PPO/AMP更新、新checkpoint恢复与旧合同拒绝；不启动正式训练，不停止后台进程"], "minimal_tests": ["bash docs/carrybox/wall5_ground_20261017/check.sh", "bash docs/carrybox/wall5_ground_20261017/smoke.sh"], "blockers": ["用户对完整地面拾起轨迹或仅离地前帧的选择待答，先完成不依赖该选择的reset实现"]}
device_actions: []
real_device_authorized: false
---

一个E/L只读专家已核对三段数据及共享调用路径；采用独立profile保护旧任务。用户答复到来后记录最终选择，测试命令固定。
