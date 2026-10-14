---
task_id: "AGILE-V2-RECOVERY-20260924"
language: "zh-CN"
axes: ["L", "D", "C"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "agent/handoff/agilekickball-v2.md", "agent/plan/agilekickball-v2.md", "agent/report/agilekickball-v2.md", "agent/task/agilekickball-v2.md", "docs/agilekickball_v2/DESIGN.md", "docs/agilekickball_v2/experiment_route.json", "docs/agilekickball_v2/idea_route.json", "docs/agilekickball_v2/research_card.json", "docs/agilekickball_v2/research_profile.json", "docs/agilekickball_v2/validation/artifacts.json", "docs/agilekickball_v2/validation/receipts.json", "docs/agilekickball_v2/validation/receipts_attempt1.json", "docs/agilekickball_v2/validation/receipts_attempt2.json", "docs/agilekickball_v2/validation/smoke.json", "docs/agilekickball_v2/validation/smoke_attempt2.json", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "tests/test_agilekickball_v2.py"]
task_contract_sha256: "842dc47f58b7211c82622baccfc277ea4d58ab725a705b301ef943ba072baa3c"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "971b1a6a9269f95fd69b0e177e20c39ff7e6076962a055190e3fcfd3ede8ec92", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "c72cf7ddaf9299dedd4a7619d16b7702e98df861fc28b823a18a37bcdb0b2c4c", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v2.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "9c7f81513bdf7036d85c9050a3a2e02e2627efcbc5e6dab3fab2fd3068fc7790", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# AgileKickball v2 工程报告

已新增独立 v2 任务，保持 v0/v1、奖励、策略与合成深度监督接口。实现 0.4–6 m/s 控制步课程、25%–50%挑战+20%全范围覆盖+剩余经验前沿练习、扰动自适应0.2–0.4s连续稳定恢复窗口、5s硬截止、闭合回合联合成功/CDF/streak统计。checkpoint严格预校验，play冻结课程并继续支持ballspeed/visray。

47项回归全部通过（含v0/v1与play边界）；真实CPU 16环境完成1次从零PPO更新。用既有v1权重在0.4–0.8m/s的流程回放1000步，发生117次恢复后发球、103次严格联合成功、1次episode终止，最大连续联合成功10。固定6m/s检查16/16环境在接近脚前可见，平均16.75个可见来球控制帧。这是流程和相机覆盖证据，不是v2高速训练结果或论文效果。

首轮集成测试失败于本地IsaacLab ObservationManager没有get_term_cfg API；改用项目visray已使用的term访问方式，保留失败receipt，重跑通过。最终检查补全全速度覆盖并使短暂恢复后再失稳的旧恢复时间作废，再次执行冻结测试通过；未删测试或放宽通过条件。

候选贡献与对照设计见docs/agilekickball_v2/DESIGN.md。仅做摘要级先验碰撞检查；尚未完成独立种子消融、统一恢复标准评估或实机验证。严格主动回球仍为运动学代理而非接触力真值。恢复调度改变样本分布，长期学习效果和GPU吞吐量仍需正式训练观察。CPU旧策略1000步耗时约12.85秒不代表4096环境GPU训练轮耗时。

没有启动长训练，没有自动commit/push或真实设备操作。训练命令：

```bash
python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-AgileKickball-v2 --num_envs 4096 --max_iterations 50000 --headless --run_name recovery_curriculum_scratch
```
