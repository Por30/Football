---
task_id: "carrybox-wall13-feedback-20261026"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "TASK"
status: "FROZEN"
original_request: "需要把这个回归信息放进128维的深度特征里 加入到wall13任务 并生成新的说明图"
allowed_paths: ["source/perceptual_ball/perceptual_ball/carrybox_wall13.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall13.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall13_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall13.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/play.py", "tests/test_carrybox_wall13.py", "docs/carrybox/wall13_feedback_20261026", "docs/carrybox/wall13_20261026/README.md", "projects/findbox/README.md", "projects/README.md", "agent/plan/carrybox-wall13-feedback-20261026.md", "agent/task/carrybox-wall13-feedback-20261026.md", "agent/report/carrybox-wall13-feedback-20261026.md", "agent/handoff/carrybox-wall13-feedback-20261026.md"]
forbidden_scope: ["更改wall11/12损失、环境或足球任务/观测接口", "改动AMP数据、奖励、噪声墙柱、RSI和训练配方", "启动正式长训、停止已有进程、隐式迁移旧checkpoint"]
development_modes: ["ML_TRAINING", "MODEL_DEPLOYMENT"]
steps: ["核对共享部署路径与资源并采纳一名P+L专家只读接口审计", "新增wall13融合Actor/PPO/Runner及revision2环境/辅助契约，接入train/play/export", "执行CPU梯度/特权隔离/优化器/旧导出兼容与16环境24步2+1更新恢复导出", "生成并查看中文结构说明图，更新项目与工程交接"]
tests: [{"command": "bash docs/carrybox/wall13_feedback_20261026/validate_cpu.sh"}, {"command": "bash docs/carrybox/wall13_feedback_20261026/validate_sim.sh"}]
stop_conditions: ["两次范围内修复后检查仍失败", "剩余GPU显存不足6000MiB", "必须修改范围外生产模块或停止已有训练"]
safeguards: ["Actor仅本体558和深度4x27x48输入；预测xyz3米制+原始旋转6D进入128维融合，标签/尺寸真值/critic/AMP不得入Actor", "原始CNN128和pred9拼接137，经Linear137→128及ELU；无detach，采样/play/部署/成对PPO路径相同", "current和mixed均独立预测并融合同批latent；每minibatch只有一次2N CNN前向，aux只缓存current并沿用清理", "PPO及策略平滑经fusion回传pose head与CNN；aux只回传pose head/CNN，critic损失只进入独立critic", "fusion在PPO构造前注册，复用wall12 pose解冻/追加一次；Adam三组完整无重复，AMP优化器别名保持，严格恢复参数状态与学习率", "wall13 migration_revision2及环境/AMP auxiliary actor_feedback=True、反馈137→128 ELU/不detach契约一致；拒绝rev1、wall12与篡改反馈契约，禁止隐式迁移", "JIT/ONNX仅flat/depth输入，包含有效pose_head与fusion，不包含critic/AMP/标签；旧wall11/12与足球导出路径保持", "回归损失/对称/同步标签/coef1.0、AMP数据权重、RSI、噪声墙柱、奖励、物理、4096x24/5x4不变", "说明图明确预测9维xyz+rot6，原始rot6不声称已正交化；展示部署路径和训练专用真值监督/梯度", "不启动正式训练、不干预足球PID3814037，16环境有界更新/恢复/导出仅落docs"]
expert_required: true
expert_brief: {"affected_call_path": ["深度→CNN128→pose9→concat137→fusion128→proprio558+Actor686→29", "采样/PPO current+mixed/play/JIT/ONNX共同前向，critic123及AMP600独立"], "critical_interfaces": ["覆盖wall13 _features与paired_outputs；独立box-feedback flag在共享导出拼接本体前融合", "parent wall12已解冻并追加pose一次；fusion预注册；回归标签12维而预测9维"], "invariants": ["Actor686、融合128、Critic123、AMP600保持", "梯度无detach且aux不进入fusion/Actor，critic独立；所有原训练/任务设置保持"], "smallest_change_locus": ["wall13独立Actor/PPO/Runner与纯契约文件、现有wall13 cfg/env revision2", "train/play dispatch及共享export的独立box分支，不修改旧任务/足球模块"], "mandatory_safeguards": ["Actor仅本体558和深度4x27x48输入；预测xyz3米制+原始旋转6D进入128维融合，标签/尺寸真值/critic/AMP不得入Actor", "原始CNN128和pred9拼接137，经Linear137→128及ELU；无detach，采样/play/部署/成对PPO路径相同", "current和mixed均独立预测并融合同批latent；每minibatch只有一次2N CNN前向，aux只缓存current并沿用清理", "PPO及策略平滑经fusion回传pose head与CNN；aux只回传pose head/CNN，critic损失只进入独立critic", "fusion在PPO构造前注册，复用wall12 pose解冻/追加一次；Adam三组完整无重复，AMP优化器别名保持，严格恢复参数状态与学习率", "wall13 migration_revision2及环境/AMP auxiliary actor_feedback=True、反馈137→128 ELU/不detach契约一致；拒绝rev1、wall12与篡改反馈契约，禁止隐式迁移", "JIT/ONNX仅flat/depth输入，包含有效pose_head与fusion，不包含critic/AMP/标签；旧wall11/12与足球导出路径保持", "回归损失/对称/同步标签/coef1.0、AMP数据权重、RSI、噪声墙柱、奖励、物理、4096x24/5x4不变", "说明图明确预测9维xyz+rot6，原始rot6不声称已正交化；展示部署路径和训练专用真值监督/梯度", "不启动正式训练、不干预足球PID3814037，16环境有界更新/恢复/导出仅落docs"], "minimal_tests": ["bash docs/carrybox/wall13_feedback_20261026/validate_cpu.sh", "bash docs/carrybox/wall13_feedback_20261026/validate_sim.sh"], "blockers": []}
device_actions: []
real_device_authorized: false
---

已继承专家七字段审计，主要风险是采样与成对更新路径不一致、重复添加pose参数、辅助契约仍写反馈False、部署漏带融合模块。冻结两条检查，增加干预/梯度/ONNX runtime以验证预测真正进入动作链。
