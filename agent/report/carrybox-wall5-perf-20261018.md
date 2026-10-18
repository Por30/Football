---
task_id: "carrybox-wall5-perf-20261018"
language: "zh-CN"
axes: ["L", "P", "E", "A"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-perf-20261018.md", "agent/plan/carrybox-wall5-perf-20261018.md", "agent/report/carrybox-wall5-perf-20261018.md", "agent/task/carrybox-wall5-perf-20261018.md", "docs/carrybox/wall5_perf_20261018/README.md", "docs/carrybox/wall5_perf_20261018/apply_optimizations.py", "docs/carrybox/wall5_perf_20261018/attempt1_candidate.log", "docs/carrybox/wall5_perf_20261018/attempt1_receipts.json", "docs/carrybox/wall5_perf_20261018/baseline.json", "docs/carrybox/wall5_perf_20261018/baseline.log", "docs/carrybox/wall5_perf_20261018/baseline_profile.txt", "docs/carrybox/wall5_perf_20261018/baseline_source/source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "docs/carrybox/wall5_perf_20261018/baseline_source/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "docs/carrybox/wall5_perf_20261018/baseline_source/source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "docs/carrybox/wall5_perf_20261018/baseline_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "docs/carrybox/wall5_perf_20261018/baseline_startup_failure.log", "docs/carrybox/wall5_perf_20261018/benchmark.sh", "docs/carrybox/wall5_perf_20261018/benchmark_profile.py", "docs/carrybox/wall5_perf_20261018/candidate.json", "docs/carrybox/wall5_perf_20261018/candidate.log", "docs/carrybox/wall5_perf_20261018/candidate_profile.txt", "docs/carrybox/wall5_perf_20261018/check.log", "docs/carrybox/wall5_perf_20261018/check.sh", "docs/carrybox/wall5_perf_20261018/comparison.json", "docs/carrybox/wall5_perf_20261018/finish_records.py", "docs/carrybox/wall5_perf_20261018/receipts.json", "docs/carrybox/wall5_perf_20261018/restart.json", "docs/carrybox/wall5_perf_20261018/restart.py", "docs/carrybox/wall5_perf_20261018/rsi_debug.log", "docs/carrybox/wall5_perf_20261018/rsi_debug_after_step.log", "docs/carrybox/wall5_perf_20261018/rsi_debug_fixed.log", "docs/carrybox/wall5_perf_20261018/rsi_equivalence.py", "docs/carrybox/wall5_perf_20261018/run_profile.sh", "docs/carrybox/wall5_perf_20261018/snapshot.json", "docs/carrybox/wall5_perf_20261018/stopped_run.json", "docs/carrybox/wall5_perf_20261018/test_runner.log", "docs/carrybox/wall5_perf_20261018/unchanged_scope.json", "docs/carrybox/wall5_perf_20261018/verify_restart.py", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_perf.py"]
task_contract_sha256: "4cfb24a460e1688b5507fce1e1bab52b313d8420a2473fcba965caf32c2239c3"
tests: [{"command": "bash docs/carrybox/wall5_perf_20261018/check.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "d846ff637f020ac2eb8189609e1e57d1f6d99cc0b6b51e4dbabbcc1f1a5c8d91", "stdout_sha256": "98766e46afa1e39851067f07b0676c5650ccd2c22d0f7ad914a7f3da2a8d3b8e", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash docs/carrybox/wall5_perf_20261018/benchmark.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "a7133b5466fbbcd4368d43fac589fd68babc7815993ce39353f29c6da184f37d", "stdout_sha256": "7c9d8dc416499afbf704a57c39d61711dacc387dad73aba83980d6738cc5e592", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/wall5_perf_20261018/verify_restart.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "e544078775e4957d21361bb44a077312c15624155028aa61e627fb3e63192d1c", "stdout_sha256": "1d4ec86fbe09bc81f91151791575d3dba069fda1243ccba5580438422484438f", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# Wall5 revision13性能排查与正式恢复（2026-10-18）

已完成等价优化、31项CPU检查、4096环境8轮完整更新/严格恢复与真实RSI对照；正式4096 wall5已恢复，检查时间2026-10-18T13:08:59+09:00，PID **3810947**，实际迭代12→15。尚未完成正式长训或证明收敛。

| 同revision13、model0/seed42、4096×24 | 采样 s | 学习 s | 合计 s |
|---|---:|---:|---:|
| 修改前，第2–5轮 | 5.052 | 2.202 | 7.254 |
| 修改后，第2–5轮 | 2.995 | 0.875 | 3.870 |

耗时下降46.6%，吞吐约1.87倍。正式运行最近10轮平均 **3.902s**、最慢 **3.940s**，达到6秒目标。表格为未插入同步计时的完整训练轮；0–1轮预热排除，第6–7轮另开同步profile。两进程均使用24个PyTorch CPU线程、相同控制/仿真/学习配置，GPU单进程。环境创建和物理初始化约5分钟，单独于每轮训练时间。

## 原因与改动

基线细分每轮RSI初始化2.430s、全部reset2.943s、物理步1.456s、深度相机更新0.187s（嵌套阶段不可相加）。48次reset调用了576次root-link写入，反复读取全体连杆质心；624次get_coms共4.20s/两轮。主要新增开销来自RSI逐片段写入，不是深度光线投射。

1. Wall5 RSI保留原随机片段/帧采样顺序，填好所有待reset行后一次提交root-link和joint状态，保留link→COM速度转换、两次kinematics刷新及实际足部接地修正。
2. Wall5 AMP拼接native raw张量，批量gather和插值，再计算旋转/末端/0.7m距离封顶。保留shortest-arc nlerp、连续采样、边界检查和RNG；未用插值后的特征替代原始状态插值。
3. PPO每minibatch只编码一次深度latent，actor/critic/pose head在同一次optimizer step联合反传，保留原act采样的RNG消耗和KL调度、有效标签掩码。

未改变4096环境、24步、5epochs×4minibatches、512/256/256网络、std/entropy、AMP权重和Normalizer、80/0/20 RSI、奖励/终止、全身碰撞、深度分辨率/50Hz/自遮挡/障碍遮挡或数据manifest。actor/critic仍只接收本体与深度；箱子真值只进入AMP/辅助监督。checkpoint仍schema2/environment revision13/AMP config3，严格兼容本次原正式model0。足球使用独立BallRegression/SkillAMP算法，DepthCNNEncoder及足球文件未改；wall3/4默认分支仍按原状态写入和三次CNN forward工作。

## 验证与边界

31项CPU测试覆盖AMP样本/边界/四元数符号/RNG，CNN输出、总loss、各参数梯度和一次Adam更新，以及原CarryBox/walled/ground/AMP契约。4096实际PhysX对512个部分reset环境执行旧/新写入：root/COM/link速度、joint、足部和box/障碍状态最大差值记录于candidate.json；loco 413、hold 99，未reset行保持、RNG一致、脚底未穿地，loco箱底5mm。完整PPO/AMP更新和验证model7严格恢复通过。

首轮验收在训练后的RSI检查处因缺少inference_mode失败；这是检查上下文错误，正式重启被门控阻止。64环境复现了具体PyTorch异常，补上与训练采样一致的inference_mode后通过，并重新完成4096验收。保留attempt1_receipts.json、attempt1_candidate.log和rsi_debug日志。最初计时入口profile.py与标准库重名，已改为benchmark_profile.py，startup失败日志保留。最终3条冻结测试均由run_engineering_tests.py执行，见receipts.json。

旧PID3804340日志止于70轮，但仅model_0.pt写盘，1–70轮未保存更新无法恢复。新正式运行从原正式model_0.pt完整恢复网络、PPO/AMP优化器、Normalizer与RNG；物理在途状态/回合不在checkpoint中，课程照既有规则重新建立进程锚点。原run/log/checkpoint保留，docs下模型仅验证，不作为正式训练或成功率证据。

## 当前正式运行

- PID：3810947
- Run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_13-02-50_wall5_v13_perf_20261018_130246`
- 日志：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v13_perf_20261018_130246.log`
- 恢复来源：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-18_12-27-37_wall5_v13_hold_rsi/model_0.pt`

```bash
tail -f '/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v13_perf_20261018_130246.log'
```

baseline.json/candidate.json提供同配置计时，两个profile.txt提供分项分析；snapshot.json记录正式契约、有限值与持续推进；unchanged_scope.json记录未改共享/配置/相机文件哈希。所有PID/轮次为带时间的快照，下次查看需核对实时状态。

