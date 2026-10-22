---
task_id: "carrybox-wall5-grasp-20261022"
language: "zh-CN"
axes: ["E", "L"]
risk_tier: "T2"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/carrybox_fullbody_collision.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/assets/motions/findbox/README.md", "source/perceptual_ball/perceptual_ball/assets/motions/findbox/ground_pickup/README.md", "tests/test_carrybox_grasp.py", "docs/carrybox/wall5_grasp_20261022", "logs/rsl_rl/g1_carrybox_depth/walled5", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall5-grasp-20261022.md", "agent/task/carrybox-wall5-grasp-20261022.md", "agent/report/carrybox-wall5-grasp-20261022.md", "agent/handoff/carrybox-wall5-grasp-20261022.md"]
artifact: "TASK"
status: "FROZEN"
original_request: "核对amp中搬箱子的数据 重新设定合理的奖励距离阈值 鼓励抓取箱子的行为 并且把完整的三段搬箱子pick up的数据集都放进去 然后停掉当前训练 重启新的训练 同时打开g1自碰撞 针对没有去学会搬起来箱子进行优化"
development_modes: ["ML_DATA_PIPELINE", "ML_TRAINING", "SIMULATOR_EXTENSION", "SYSTEM_TUNING"]
forbidden_scope: ["不改football、wall3/4、共享G1资产文件、actor/critic接口、PPO/AMP算法或深度管线", "不删改原始动作张量、旧checkpoint、日志、既有工作区改动", "不从旧权重恢复或把短测作为收敛证据"]
steps: ["核对当前进程并审计完整三段拾箱数据与G1抓取几何", "组合E/L只读专家检查关键不变量，主Agent实现wall5专属数据选择、抓取奖励及自碰撞", "核对三段完整AMP及近箱站立/伸手/双手接触/抬起奖励排序", "运行20环境碰撞/reset及PPO/AMP更新恢复导出短测", "通过后停止身份匹配的旧训练并fresh启动4096环境", "确认正式更新与6秒迭代目标，记录日志命令、限制与后续评估"]
tests: [{"command": "bash docs/carrybox/wall5_grasp_20261022/validate_and_restart.sh"}]
stop_conditions: ["验收失败仅范围内修复最多两次，未通过不启动正式训练", "进程身份不符、源码/数据变动或非有限物理/优化器输出停止验收", "遇需修改共享训练算法/足球/原始数据内容则停止扩展"]
safeguards: ["所有阈值以米和真实G1掌/箱几何审计；奖励只读真值，不泄漏actor", "AMP完整三段且hash不变；地面RSI与高处拾箱AMP用途分开，保持75/5/20", "开启wall5自碰撞，检查默认与RSI穿插/非相邻接触；不全局更改G1", "抓取奖励必须提高真实接近双掌、双手接触与抬升的收益，不能只因近箱站立拿满", "任务契约revision23，旧训练停止前保存进程与模型状态；新训练fresh单次启动", "保留roll0.5、20秒时限、深度米制、critic123、aux1；短测不宣称成功率", "per-hand oriented-box distance, no averaged-hand cheat", "stand/reach/single/bilateral/lift weighted reward increasing", "bilateral Box contact required for lift, force saturation", "self collision physical readback; no blanket limb filtering", "fresh4096 single launch after tests; schema23 and source identity"]
expert_required: true
expert_brief: {"affected_call_path": ["Wall5 runner -> full FindBox AMP", "ground_pickup -> ground-only RSI", "wall5 spawn -> fullbody hull -> PhysX self collision", "wall5 rewards -> PPO task/style mixture"], "critical_interfaces": ["three pickups192/178/129 frames,60Hz ->50Hz; sha256 fixed", "Box .30/.30/.25m; real palm link origins vs rubber-hand COM", "Box-filtered hand forces, oriented bottom clearance"], "invariants": ["actor unchanged,critic123,aux1,depth metres", "RSI75/5/20 ground03 prefix0:32; full AMP independent", "wall3/4 and football unchanged"], "smallest_change_locus": ["wall5 config + tensor helper + mdp", "wall5-only explicit three joint-shell overlap pairs"], "mandatory_safeguards": ["per-hand oriented-box distance, no averaged-hand cheat", "stand/reach/single/bilateral/lift weighted reward increasing", "bilateral Box contact required for lift, force saturation", "self collision physical readback; no blanket limb filtering", "fresh4096 single launch after tests; schema23 and source identity"], "minimal_tests": ["bash docs/carrybox/wall5_grasp_20261022/validate_and_restart.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

wall5当前能接近并站稳，但三段地面回放手箱接触均为零。此次只优化拾箱相关奖励、恢复完整三段AMP并打开wall5自碰撞，使用现有短测/启动守护流程验证后正式从零4096训练。三段中高处起箱动作只进入AMP，RSI仍使用已验证地面片段。
