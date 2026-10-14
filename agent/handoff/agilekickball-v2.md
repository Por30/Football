---
task_id: "AGILE-V2-RECOVERY-20260924"
language: "zh-CN"
axes: ["L", "D", "C"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "agent/handoff/agilekickball-v2.md", "agent/plan/agilekickball-v2.md", "agent/report/agilekickball-v2.md", "agent/task/agilekickball-v2.md", "docs/agilekickball_v2/DESIGN.md", "docs/agilekickball_v2/experiment_route.json", "docs/agilekickball_v2/idea_route.json", "docs/agilekickball_v2/research_card.json", "docs/agilekickball_v2/research_profile.json", "docs/agilekickball_v2/validation/artifacts.json", "docs/agilekickball_v2/validation/receipts.json", "docs/agilekickball_v2/validation/receipts_attempt1.json", "docs/agilekickball_v2/validation/receipts_attempt2.json", "docs/agilekickball_v2/validation/smoke.json", "docs/agilekickball_v2/validation/smoke_attempt2.json", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "tests/test_agilekickball_v2.py"]
task_contract_sha256: "842dc47f58b7211c82622baccfc277ea4d58ab725a705b301ef943ba072baa3c"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "971b1a6a9269f95fd69b0e177e20c39ff7e6076962a055190e3fcfd3ede8ec92", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "c72cf7ddaf9299dedd4a7619d16b7702e98df861fc28b823a18a37bcdb0b2c4c", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v2.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "9c7f81513bdf7036d85c9050a3a2e02e2627efcbc5e6dab3fab2fd3068fc7790", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

# AgileKickball v2 Handoff

当前实现与两条冻结测试均已完成；receipt和Task hash位于frontmatter。设计入口docs/agilekickball_v2/DESIGN.md，主代码mdp/agilekickball_v2.py，独立配置agilekickball_v2_env_cfg.py。最终证据为validation/smoke.json与receipts.json；attempt文件仅保留过程证据，不能代替最终结果。

下一步是用户启动从零长训练，而非恢复旧任务。不要把旧v1流程回放或人为设置课程端点当成v2学会6m/s。观察AgileV2的探索上限、经验前沿、各bin closed/joint_rate/CDF、above_5m_s_serves和连续成功。课程控制步保存与play冻结独立于评测计数；恢复checkpoint不迁移物理开放回合。

论文候选仍需统一固定0.3s测量标准、独立训练种子2×2消融、接触真值校准和全文新颖性审计；未锁定科研结论。当前奖励仍是v1原proxy，联合成功指标更严格。真实深度遮挡和实机未验证。

精确从零训练命令：

```bash
python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-AgileKickball-v2 --num_envs 4096 --max_iterations 50000 --headless --run_name recovery_curriculum_scratch
```
