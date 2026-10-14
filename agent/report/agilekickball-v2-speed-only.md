---
task_id: "AGILE-V2-SPEED-ONLY-20260925"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "agent/handoff/agilekickball-v2-speed-only.md", "agent/plan/agilekickball-v2-speed-only.md", "agent/report/agilekickball-v2-speed-only.md", "agent/task/agilekickball-v2-speed-only.md", "docs/agilekickball_v2/DESIGN.md", "docs/agilekickball_v2/speed_only_20260925/REPORT.md", "docs/agilekickball_v2/speed_only_20260925/audit_latest.py", "docs/agilekickball_v2/speed_only_20260925/before/DESIGN.md", "docs/agilekickball_v2/speed_only_20260925/before/agilekickball_v2.py", "docs/agilekickball_v2/speed_only_20260925/before/agilekickball_v2_env_cfg.py", "docs/agilekickball_v2/speed_only_20260925/before/smoke_agilekickball_v2.py", "docs/agilekickball_v2/speed_only_20260925/before/smoke_agilekickball_v2.sh", "docs/agilekickball_v2/speed_only_20260925/before/test_agilekickball_v2.py", "docs/agilekickball_v2/speed_only_20260925/checkpoint_version.json", "docs/agilekickball_v2/speed_only_20260925/latest_training.json", "docs/agilekickball_v2/speed_only_20260925/v1_comparison.json", "docs/agilekickball_v2/speed_only_20260925/validation/artifacts.json", "docs/agilekickball_v2/speed_only_20260925/validation/receipts.json", "docs/agilekickball_v2/speed_only_20260925/validation/receipts_attempt1.json", "docs/agilekickball_v2/speed_only_20260925/validation/smoke.json", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "tests/test_agilekickball_v2.py"]
task_contract_sha256: "748084aad17300f020e3ce043afcfbeba24be649931490863c7784caf1145a22"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "971b1a6a9269f95fd69b0e177e20c39ff7e6076962a055190e3fcfd3ede8ec92", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "38a53d6e5934ecd4e5cc47f8efd1d28f20af69c1f7c73004960a1456a1686ce7", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v2.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "9c7f81513bdf7036d85c9050a3a2e02e2627efcbc5e6dab3fab2fd3068fc7790", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

最新旧schema3训练40982轮平均回合1.35秒，恢复发球0；同轮数v1为43.73秒、窗口恢复发球份额92.71%。实际失败以离锚点/跌倒/倾倒为主，不是等满恢复超时。最新进程未加载schema4，不将其当作schema4失败证据。

v2现为schema5、revision=v1_speed_only_20260925，直接继承v1物理球流程和全部奖励/终止/观测/动作/网络/PPO；仅改速度课程。保留v1曝光起步与距离，近期恢复>=80%、kick代理>=60%、曝光>=60000、窗口>=128发球后解锁扩展至6m/s；恢复<=50%或无有效样本暂停扩展。严格schema预验证，play冻结与ballspeed覆盖，跨环境数量恢复课程；resume丢弃部分统计窗口。

58项回归通过。首次浮点精确等值失败，修正bootstrap乘除次序为v1顺序后重跑通过，没有放宽断言。真实CPU16环境4次新策略PPO更新、checkpoint/freeze/override、高速视野检查通过。1000控制步回放：成熟v1策略在v1与新v2中均150次恢复发球、0终止；旧v2最新40800策略在新v2中0恢复、254失败。6m/s在16/16环境接近脚前可见。

详细数据及限制见docs/agilekickball_v2/speed_only_20260925/REPORT.md；设计见docs/agilekickball_v2/DESIGN.md。该验证不证明新策略从零收敛或高速踢球能力；v1即时kick奖励仍可能被钻空子，不能单看reward。当前没有长训练，不自动启动，不修改v0/v1，不commit/push。旧schema4源代码/测试归档before，历史结果保留。

用户可执行（不要加--resume）：

```bash
python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-AgileKickball-v2 --num_envs 4096 --device cuda:0 --headless --max_iterations 50000 --seed 42 --run_name v1_speed_only_20260925_scratch
```

启动输出revision=v1_speed_only_20260925，TensorBoard AgileV2/schema=5。确认新目录，旧运行日志不能表示新代码。优先观察episode长度、recent_recovered_serve_share与实际连续球；速度上限不等于掌握速度。
