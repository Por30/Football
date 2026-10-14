---
task_id: "AGILE-V3-STABILITY-FIX-20261008"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/rsl_rl_extensions/state_feedback.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/export.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "tests/test_state_feedback.py", "tests/test_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "scripts/rsl_rl/train_agilekickball_v3.sh", "docs/agilekickball_v3/README.md", "README.md", "scripts/rsl_rl/train.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_feedback_legacy_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3_feedback_legacy.py", "docs/agilekickball_v3/stability_fix_20261008", "agent/plan/agilekickball-v3-stability-fix.md", "agent/task/agilekickball-v3-stability-fix.md", "agent/report/agilekickball-v3-stability-fix.md", "agent/handoff/agilekickball-v3-stability-fix.md", "logs/rsl_rl/agilekickball_v3/2026-10-08_11-48-24_feedback_stable_20261008_v2init", "logs/background/agilekickball_v3_feedback_stable_20261008_114819.log", "logs/background/agilekickball_v3_feedback_stable_20261008_114819.pid", "logs/rsl_rl/agilekickball_v3_smoke/2026-10-08_11-41-58_feedback_stable_scale_smoke"]
task_contract_sha256: "f01896049457022c72b78f95be5c86a9740858f53ed4d4b07c20b1cc57843b05"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_state_feedback.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8a64957c8c0dbaa892b025807418a3d94725b313191624ba19ab65e0dc9d6912", "stdout_sha256": "8b927efc8a89aac73059b2118142b897a7b88c139ca4af262e433663c2751903", "stderr_sha256": "a1490b725d6505bab59ca1bb9746cc84e3ce19ba95736e81974babc9c88af695", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "40a7c83430b33b71e474d48e5d4ce919084def0f3ad38a8ca98453e3cced4c0e", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1d62a83bc8ed2afddb0ddf08e9ab2de07b15492cd74d08f81223147e2124831e", "stdout_sha256": "0ff0c1780e86161b765f8f0bb42944acaa41a6d6e3f8157293b611b0f73d3284", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

当前目标已完成：诊断、修复、验证并后台启动新 v3。PID 1776883，revision feedback_stable_20261008，当前已核验第 67 轮。launch.json 记录 start_ticks 和独立 session；后续先核对进程身份，禁止重复启动/覆盖旧run。DONE 不意味着50000轮训练已完成。

新入口 scripts/rsl_rl/train_agilekickball_v3.sh 默认 --warm_start_v2 源 v2 model_49999.pt，独立新 run；--resume 时脚本不传 warm-start，两者互斥。runner.warm_start_from_v2 先验证版本/形状/finite/AMP及残差零输出，再加载主网络权重，优化器/课程/轮数不迁移。initialization.json 和checkpoint记录 source SHA256。

关键配置：PPO 初始 lr1e-5（adaptive调度），NLL lr1e-4，KL .001，update_encoder=false，smooth logstd[-2,1]，残差上限 .1 raw。ball_distribution 的 detach_features 只用于辅助，PPO仍可更新原encoder。Loss/aux/encoder_updates 应为0，aux/predictor_updates才是新辅助接受数。禁止重新启用旧head-only fallback；拒绝trial后恢复全部本次辅助参数及深拷贝Adam。

旧失败版本可通过 Template-Perceptual-Ball-AgileKickball-v3-StateFeedback-20261006 回放，默认策略/算法保留schema1；旧Outcome任务也保留。新任务课程revision与schema2会拒绝普通resume旧模型，不能把warm-start冒充断点续训。新课程起点由startup参数initial_exposure_steps=60000定义，物理阈值与v2相同。

冻结三命令最终PASS，失败历史保留；100轮4096短训及同条件修复后回放已通过。源文件在 docs/agilekickball_v3/stability_fix_20261008/source_snapshot/。完整证据包括 comparison/config_differences/replay/probe/diagnosis/smoke/scale_smoke/replay_repaired/verified_start JSON。修复后同条件恢复900次与继承v2有关，不足以声称方法提升。

状态命令：tail -n 120 /home/cao/perceptual_ball/logs/background/agilekickball_v3_feedback_stable_20261008_114819.log
进程命令：ps -p 1776883 -o pid,sid,etime,args
模型目录：/home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v3/2026-10-08_11-48-24_feedback_stable_20261008_v2init
关注early episode长度、累计恢复、每6000控制步的课程窗口、预测头更新、NLL主encoder更新是否为0、动作修正幅度、KL及finite。暂未验证长期收敛；保持旧v2基线和所有旧日志。无需恢复本轮工作或再次启动训练。
