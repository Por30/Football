---
task_id: "carrybox-g1-reset-20261015"
language: "zh-CN"
axes: ["E", "L", "C"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_x2_rewards.py", "source/perceptual_ball/perceptual_ball/carrybox_warp_camera.py", "tests/test_carrybox_g1_reset.py", "docs/carrybox/g1_reset_20261015", "logs/rsl_rl/g1_carrybox_depth/walled4", "README.md", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-g1-reset-20261015.md", "agent/task/carrybox-g1-reset-20261015.md", "agent/report/carrybox-g1-reset-20261015.md", "agent/handoff/carrybox-g1-reset-20261015.md", "tests/test_carrybox_walled.py"]
artifact: "TASK"
status: "FROZEN"
original_request: "排查站立易reset，确保X2交接的相机和构型正确适配G1，再后台重启wall4正式训练"
development_modes: ["ML_TRAINING", "SIMULATOR_EXTENSION", "CONTROL_LOOP"]
forbidden_scope: ["修改足球或共享G1资产", "放宽失败阈值掩盖倾倒", "特权actor/critic", "声称短测证明收敛"]
steps: ["复现站立reset并记录终止前状态", "核对G1坐标相机关节和RSI", "只修复有证据的问题且wall3/wall4共用", "CPU与仿真/4096完整迭代验证", "后台启动4096环境wall4并核对日志checkpoint", "更新管理记录"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v"}]
stop_conditions: ["同一测试两次修复仍失败", "仿真非有限状态或资源不足", "无证据支持放宽终止阈值"]
safeguards: ["无特权输入与纯本体AMP不变", "保留G1物理硬限制与默认严格checkpoint契约", "启动前核对实际进程与资源", "不得将资产名义相机标定等同实机实测", "先记录终止前roll/pitch/root/head及旧模型身份", "三技能核验RSI请求/读回、脚底、相机变换与动作目标", "fresh短测确认loco形成AMP窗口，4096完整迭代不超过6秒后启动", "正式后台启动无旧checkpoint或warm-start且不并发重复启动", "不能将开环站姿或短训当作站立收敛、实机标定结论"]
expert_required: true
device_actions: []
real_device_authorized: false
expert_brief: {"affected_call_path": ["FindBoxMotionLibrary→RSI状态写入→tipped/fallen；G1 D435挂载→Warp光轴深度；fresh PPO/AMP训练"], "critical_interfaces": ["xyzw数据转wxyz，再由IsaacLab转PhysX xyzw；G1命名关节映射；torso安装和真实head COM"], "invariants": ["策略/价值只用深度本体；wall3/wall4仅障碍不同；不无证据增加failure penalty"], "smallest_change_locus": ["先保留revision7已有适配，诊断脚本区分旧策略控制和状态错误；仅有明确新证据时修改wall共同MDP"], "mandatory_safeguards": ["先记录终止前roll/pitch/root/head及旧模型身份", "三技能核验RSI请求/读回、脚底、相机变换与动作目标", "fresh短测确认loco形成AMP窗口，4096完整迭代不超过6秒后启动", "正式后台启动无旧checkpoint或warm-start且不并发重复启动", "不能将开环站姿或短训当作站立收敛、实机标定结论"], "minimal_tests": ["/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "bash docs/carrybox/g1_reset_20261015/validate.sh"], "blockers": []}
---

仅补齐旧mock后复查冻结CPU命令；生产代码和已通过GPU验收未变。
