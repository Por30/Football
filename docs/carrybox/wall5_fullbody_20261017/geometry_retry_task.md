---
task_id: "carrybox-wall5-fullbody-20261017"
language: "zh-CN"
axes: ["E", "P", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "把碰撞体改成全身 并可视化碰撞体结构"
development_modes: ["SIMULATOR_EXTENSION", "MODEL_DEPLOYMENT"]
allowed_paths: ["docs/carrybox/wall5_fullbody_20261017", "source/perceptual_ball/perceptual_ball/carrybox_fullbody_collision.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-fullbody-20261017.md", "agent/task/carrybox-wall5-fullbody-20261017.md", "agent/report/carrybox-wall5-fullbody-20261017.md", "agent/handoff/carrybox-wall5-fullbody-20261017.md"]
forbidden_scope: ["共享G1资产或football/wall3/wall4修改", "未经指令开启自碰撞或改变奖励、相机、PPO、AMP数据", "正式训练启动/停止/重启", "把短测称作收敛或4096规模性能验收"]
steps: ["冻结全身覆盖范围与专属spawn及兼容合同", "补齐7处并替换6处简化体，保持质量/视觉/足部", "从最终碰撞定义生成多视图和可交互结构", "运行CPU覆盖和小环境PhysX接触/状态验证", "记录兼容性、项目入口及交接"]
tests: [{"command": "bash docs/carrybox/wall5_fullbody_20261017/check_geometry.sh"}]
stop_conditions: ["资产变动、非有限物理状态或旧合同被静默接受则失败停止", "GPU可用显存不足4GiB则不启动smoke", "小环境smoke超时600秒停止，不升级为正式训练"]
safeguards: ["New colliders invisible/proxy/convexHull; per-link visible mesh vertex/face digest unchanged", "All physical visual vertices must be contained in final local collider convex hull", "Disable replaced old shapes; feet geometry and reset support unchanged; source USD hash unchanged", "Small PhysX smoke checks body/joint counts,mass/inertia,new head/knee/wrist contacts and finite states/depth", "If self collision is requested, extend validation to adjacent/fixed filtering and RSI overlap/impulses before claiming support", "No formal train start/stop/restart; inspect processes/resources before smoke", "Internal references target same-link visuals only; set API on instance root, never edit instance proxies", "Visualizations show authored hull previews, not a claim of identical PhysX cooked vertices"]
expert_required: true
expert_brief: {"affected_call_path": ["wall5専属spawn -> spawn_walled_robot -> USD -> PhysX/contact sensors", "Warp visual_mesh visibility/purpose filtering", "Wall5 checkpoint_contract -> strict load/warm_start"], "critical_interfaces": ["35 physical visible mesh links; 7 missing colliders + 6 undersized shoulder/knee colliders", "Collision API is on parent Xform; include instance proxies", "Head mesh offset z0.325–0.531m must be preserved"], "invariants": ["No shared USD/football/wall3/4 changes; preserve DOF,mass,COM,inertia,camera,depth/proprio/AMP interfaces", "Self collision remains false unless user explicitly requests otherwise"], "smallest_change_locus": ["wall5 spawn + isolated full-body geometry helper", "wall5 checkpoint migration revision10/profile; legacy only explicit weights-only", "PNG and standalone interactive HTML generated from resulting collision definitions"], "mandatory_safeguards": ["New colliders invisible/proxy/convexHull; per-link visible mesh vertex/face digest unchanged", "All physical visual vertices must be contained in final local collider convex hull", "Disable replaced old shapes; feet geometry and reset support unchanged; source USD hash unchanged", "Small PhysX smoke checks body/joint counts,mass/inertia,new head/knee/wrist contacts and finite states/depth", "If self collision is requested, extend validation to adjacent/fixed filtering and RSI overlap/impulses before claiming support", "No formal train start/stop/restart; inspect processes/resources before smoke", "Internal references target same-link visuals only; set API on instance root, never edit instance proxies", "Visualizations show authored hull previews, not a claim of identical PhysX cooked vertices"], "minimal_tests": ["bash docs/carrybox/wall5_fullbody_20261017/check_geometry.sh", "bash docs/carrybox/wall5_fullbody_20261017/smoke.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

仅重执行原冻结CPU命令；修复绘图facecolors参数。原PhysX命令已PASS，生产代码和该脚本未改，不重复仿真。
