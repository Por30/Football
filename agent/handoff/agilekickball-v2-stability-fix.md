---
task_id: "AGILE-V2-STABILITY-FIX-20260924"
language: "zh-CN"
axes: ["L", "D"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "agent/handoff/agilekickball-v2-stability-fix.md", "agent/plan/agilekickball-v2-stability-fix.md", "agent/report/agilekickball-v2-stability-fix.md", "agent/task/agilekickball-v2-stability-fix.md", "docs/agilekickball_v2/DESIGN.md", "docs/agilekickball_v2/stability_fix_20260924/before/DESIGN.md", "docs/agilekickball_v2/stability_fix_20260924/before/agilekickball_v2.py", "docs/agilekickball_v2/stability_fix_20260924/before/agilekickball_v2_env_cfg.py", "docs/agilekickball_v2/stability_fix_20260924/before/smoke.json", "docs/agilekickball_v2/stability_fix_20260924/before/smoke_agilekickball_v2.py", "docs/agilekickball_v2/stability_fix_20260924/before/smoke_agilekickball_v2.sh", "docs/agilekickball_v2/stability_fix_20260924/before/test_agilekickball_v2.py", "docs/agilekickball_v2/stability_fix_20260924/stopped_training.json", "docs/agilekickball_v2/stability_fix_20260924/validation/artifacts.json", "docs/agilekickball_v2/stability_fix_20260924/validation/receipts.json", "docs/agilekickball_v2/stability_fix_20260924/validation/receipts_attempt1.json", "docs/agilekickball_v2/stability_fix_20260924/validation/smoke.json", "scripts/rsl_rl/smoke_agilekickball_v2.py", "scripts/rsl_rl/smoke_agilekickball_v2.sh", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v2_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v2.py", "tests/test_agilekickball_v2.py"]
task_contract_sha256: "25fc99e7fe309f0a1cc1804b0a5d438f135d2f30c37804d19c8f0471295aa6cb"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v2.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "971b1a6a9269f95fd69b0e177e20c39ff7e6076962a055190e3fcfd3ede8ec92", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "01481148dad910d5f1d62e2211b21b89efe6a5bdfe3d14abde8da3f57dfecb96", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v2.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "9c7f81513bdf7036d85c9050a3a2e02e2627efcbc5e6dab3fab2fd3068fc7790", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

# v2稳定性修正完成

旧后台训练PID3618949已SIGINT停止并验证退出；显存释放。当前不运行新长训练。v0/v1和网络PPO保持原样，修正仅作用于v2。主设计见docs/agilekickball_v2/DESIGN.md，旧代码/旧测试/旧验证已归档before目录。

慢球0.4–0.8m/s始终近距离0.5–0.7m发球，6m/s对应2.06–2.26m。距离使用真实采样速度且只计数一次。恢复回到球结束后连续稳定0.3s、最少等待0.4s、等待满5s超时；取消自适应峰值驻留和outbound硬超时。准备站立倍率仅近球时减弱。主动kick、稳定回球再发、非时间上限失败的事件原始奖励为+2/+8/-8（AMP任务混合后+1.5/+6/-6）。被动反弹不获kick/return奖励，也不免miss。联合成功脉冲跨same-tick serve保留且只支付一次。

探索上限仍按原节点达到6m/s；未掌握时挑战5%、全范围10%、其余练习，随着联合成功增加挑战。schema4/config stable_return_v2拒绝旧v2直接resume。

49项单元回归通过，含v0/v1/play回归。真实CPU16环境完成4次新策略PPO更新，checkpoint/freeze/override通过。同一0.4–1.45m/s分布下1000步回放：成熟v1策略186次恢复再发、181次严格联合成功、平均任务奖励0.17228/环境步；旧v2坏策略0次恢复再发、215次失败被罚、平均任务奖励-0.10421。固定6m/s来球16/16环境在接近脚前可见。上述是流程与奖励排序验证，不是新v2从零长训练能力证明，不承诺必然学会5m/s以上。

从零训练命令（用户执行，不自动启动）：

```bash
python scripts/rsl_rl/train.py --task Template-Perceptual-Ball-AgileKickball-v2 --num_envs 4096 --device cuda:0 --headless --max_iterations 50000 --seed 42 --run_name stability_fix_scratch
```

不要加--resume，不要把已停止旧run日志当作新版本结果。后续以新run的近距离连续联合成功、失败率和实际高速成功率评估学习；如需调整，应保持每项对照而非同时扩大多个课程变量。
