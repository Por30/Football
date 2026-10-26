---
task_id: "carrybox-wall12-20261025"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "新建wall12 加上这个深度信息回归箱子位姿的模块"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall12_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall12.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/train_carrybox_walled.sh", "scripts/rsl_rl/play_carrybox_walled.sh", "tests/test_carrybox_wall12.py", "docs/carrybox/wall12_20261025", "projects/README.md", "projects/findbox/README.md", "agent/plan/carrybox-wall12-20261025.md", "agent/task/carrybox-wall12-20261025.md", "agent/report/carrybox-wall12-20261025.md", "agent/handoff/carrybox-wall12-20261025.md"]
forbidden_scope: ["修改wall10/11或足球生产模块、共享CNN/AMP/资产/动作数据", "启动正式长训、停止或重启已有进程", "将箱子标签或回归输出直接输入actor/部署策略"]
development_modes: ["ML_TRAINING", "ML_DATA_PIPELINE"]
steps: ["核对训练/观测链路和资源并完成感知学习接口审计", "新增独立wall12配置、标签、回归损失和联合学习器", "执行CPU定向与16环境24步2+1更新/恢复/导出短测", "核对旧任务兼容并更新项目与工程记录"]
tests: [{"command": "bash docs/carrybox/wall12_20261025/validate_cpu.sh"}, {"command": "bash docs/carrybox/wall12_20261025/validate_sim.sh"}]
stop_conditions: ["两次范围内修复后检查仍失败", "需要范围外生产改动", "GPU资源不足或与现有正式任务冲突"]
safeguards: ["actor558+4x27x48、critic123、AMP600及wall11物理/奖励/噪声/墙柱/24步/5x4保持", "仅增加训练端相机光学坐标xyz米制+旋转6D回归，coef1.0；标签匹配最新深度帧并detach", "可变长方体姿态按实际尺寸允许的旋转对称处理，禁止把非方形箱90度旋转当等价", "全部有效配对帧监督；复用current CNN latent，避免额外CNN前向，pose head与CNN同一Adam更新", "独立schema2环境与辅助契约，拒绝wall11严格resume，导出仅本体/深度输入", "保留工作区足球v11未提交修改和现有wall10辅助hook；低显存16env短测，不启动正式训练", "标签/深度两种读取顺序均由同一次capture生成；每env每controlstep缓存，partial reset独立失效；terminal仍保存重置前深度", "相机光学旋转6D为前两列，候选R@S；24个proper signed permutations按实际尺寸1e-6绝对/1e-5相对容差筛选4/8/24对称", "全部配对帧指原T-1更新索引，监督current而非mixed/next；标签不按距离/可见性/前后过滤、不裁剪且detach", "pose head解冻后加入既有policy Adam组，三组参数无重复，学习率/pose优化器状态严格恢复", "回归日志包含位置/姿态/加权辅助loss；JIT/ONNX图只含CNN与actor"]
expert_required: true
expert_brief: {"affected_call_path": ["wall12 capture/target → rollout → current CNN latent/pose head → auxiliary hook → joint Adam", "wall12 config/register/train/play → existing export"], "critical_interfaces": ["12维相机系xyz3+rot6+实际尺寸3标签，9维预测，rotation按前两列展开", "pose head原本冻结排除于Adam；必须解冻并补入原policy组"], "invariants": ["actor558+depth4x27x48、critic123、AMP600保持", "标签与最新带噪帧配对；无特权actor反馈；原24步前23步学习"], "smallest_change_locus": ["4个wall12独立模块与入口追加，复用wall10已有aux hook，保留足球修改"], "mandatory_safeguards": ["actor558+4x27x48、critic123、AMP600及wall11物理/奖励/噪声/墙柱/24步/5x4保持", "仅增加训练端相机光学坐标xyz米制+旋转6D回归，coef1.0；标签匹配最新深度帧并detach", "可变长方体姿态按实际尺寸允许的旋转对称处理，禁止把非方形箱90度旋转当等价", "全部有效配对帧监督；复用current CNN latent，避免额外CNN前向，pose head与CNN同一Adam更新", "独立schema2环境与辅助契约，拒绝wall11严格resume，导出仅本体/深度输入", "保留工作区足球v11未提交修改和现有wall10辅助hook；低显存16env短测，不启动正式训练", "标签/深度两种读取顺序均由同一次capture生成；每env每controlstep缓存，partial reset独立失效；terminal仍保存重置前深度", "相机光学旋转6D为前两列，候选R@S；24个proper signed permutations按实际尺寸1e-6绝对/1e-5相对容差筛选4/8/24对称", "全部配对帧指原T-1更新索引，监督current而非mixed/next；标签不按距离/可见性/前后过滤、不裁剪且detach", "pose head解冻后加入既有policy Adam组，三组参数无重复，学习率/pose优化器状态严格恢复", "回归日志包含位置/姿态/加权辅助loss；JIT/ONNX图只含CNN与actor"], "minimal_tests": ["bash docs/carrybox/wall12_20261025/validate_cpu.sh", "bash docs/carrybox/wall12_20261025/validate_sim.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

已纳入一名P+L只读专家七字段审计。独立尺寸感知姿态loss；显式配对capture缓存；冻结两条验收命令，保留当前共享辅助hook及足球改动。
