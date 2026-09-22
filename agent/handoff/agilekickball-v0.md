---
task_id: "ENG-AGILEKICKBALL-V0-20260920"
status: "PARTIAL"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/curriculums.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball.py", "tests/test_agilekickball.py", "scripts/rsl_rl/smoke_agilekickball.py", "scripts/rsl_rl/smoke_agilekickball.sh", "docs/agilekickball/README.md", "docs/agilekickball/test_receipts.json", "docs/agilekickball/artifact_validation.json", "docs/agilekickball/validation/smoke.log", "docs/agilekickball/validation/recovery_diagnostics.md", "docs/agilekickball/validation/smoke_model.pt", "agent/plan/agilekickball-v0.md", "agent/task/agilekickball-v0.md", "agent/report/agilekickball-v0.md", "agent/handoff/agilekickball-v0.md"]
task_contract_sha256: "e0009bc5fd5371630128788e6ebc5a230fecc0276e77406b90ce5bf05ed24903"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "13d3b7031c97301d82ae75a11c57184215889070fb07218079dae948071de702", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "32530a01f9c08a4a138d32af43b2a75edeec9c857d7e2a4e3ab966155a4634a0", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball.sh", "result": "FAIL", "exit_code": 1, "executed": true, "receipt_sha256": "efe468104f497b184b60ab479c0f2914d128889428b1d6ea9cb59f1c0ec4e57f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "bd8f6b0fe2db286035751c55333c5908657fa2688908703b4052dd5730eba392", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: "bash scripts/rsl_rl/smoke_agilekickball.sh"
---

# AgileKickball 交接

实现已落地但工程验收PARTIAL。任务入口Template-Perceptual-Ball-AgileKickball-v0；用户要求v0基础、来球速课程、保持机器人连续动力学并在恢复后再发球。实现与命令见docs/agilekickball/README.md。禁止把已有v0/v3配置改成新任务，也不要为测试通过降低恢复门槛。

CPU7项通过，真实smoke仍失败。第一阶段仅课程版本已走到PPO更新，但本版本新增恢复后门控未满足同episode两次发球验收。零动作约0.98秒前倾tipped；测试用踝反馈约1.18秒tipped；最终使用原v0 model_30800.pt只读推理约0.78秒部分环境tipped。具体数据在validation/recovery_diagnostics.md。脚本未直接写机器人状态来扶正、未加外力或修改PD。现有反馈尝试不能扩大为控制器研发。

精确重现：bash scripts/rsl_rl/smoke_agilekickball.sh。下一步应在适合恢复的策略可用后补真实验收，保留连续稳定0.3秒、超时5秒与同episode不reset断言；若修改任务定义，先记录用户授权/新合同。最终测试失败记录绑定当前Task，不得把CPU逻辑通过写成真实动力学通过。

训练命令（未由本Agent启动）：

```bash
python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-AgileKickball-v0 --num_envs 4096 --device cuda:0 --headless --max_iterations 50000 --seed 42 --run_name speed_curriculum
```

恢复训练要显式设置curriculum incoming_ball_speed.params.start_step；当前runner未保存env common_step_counter。原工作区含大量用户修改与未跟踪文件，本轮未提交/清理。验证产物smoke_model.pt若存在，为此前课程阶段流程产物，不是本任务训练好或完整验收的证据。
