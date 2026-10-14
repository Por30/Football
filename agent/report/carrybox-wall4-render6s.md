---
task_id: "carrybox-wall4-render6s"
language: "zh-CN"
axes: ["P", "A"]
risk_tier: "T2"
status: "PARTIAL"
changed_files: ["README.md", "agent/handoff/carrybox-wall4-render6s.md", "agent/plan/carrybox-wall4-render6s.md", "agent/report/carrybox-wall4-render6s.md", "agent/task/carrybox-wall4-render6s.md", "docs/carrybox/performance_20261014/launch.json", "docs/carrybox/render6s_20261014/README.md", "docs/carrybox/render6s_20261014/attempt2_test_receipts.json", "docs/carrybox/render6s_20261014/attempt3_test_receipts.json", "docs/carrybox/render6s_20261014/baseline4/attempt1.log", "docs/carrybox/render6s_20261014/baseline4/depth_frames.pt", "docs/carrybox/render6s_20261014/baseline4/result.json", "docs/carrybox/render6s_20261014/baseline4/run.log", "docs/carrybox/render6s_20261014/baseline4/runtime.json", "docs/carrybox/render6s_20261014/before_launch.json", "docs/carrybox/render6s_20261014/before_timing.json", "docs/carrybox/render6s_20261014/comparison.json", "docs/carrybox/render6s_20261014/depthfast4/depth_frames.pt", "docs/carrybox/render6s_20261014/depthfast4/result.json", "docs/carrybox/render6s_20261014/depthfast4/run.log", "docs/carrybox/render6s_20261014/depthfast4/runtime.json", "docs/carrybox/render6s_20261014/fabric4/attempt2_run.log", "docs/carrybox/render6s_20261014/fabric4/attempt3_run.log", "docs/carrybox/render6s_20261014/fabric4/run.log", "docs/carrybox/render6s_20261014/formal_health.json", "docs/carrybox/render6s_20261014/geometry/geometry.json", "docs/carrybox/render6s_20261014/geometry/run.log", "docs/carrybox/render6s_20261014/launch.json", "docs/carrybox/render6s_20261014/resume_checkpoint_health.json", "docs/carrybox/render6s_20261014/scale4096/profile.txt", "docs/carrybox/render6s_20261014/scale4096/result.json", "docs/carrybox/render6s_20261014/scale4096/run.log", "docs/carrybox/render6s_20261014/scale4096/runtime.json", "docs/carrybox/render6s_20261014/scale4096/sample.prof", "docs/carrybox/render6s_20261014/scale4096/train/events.out.tfevents.1791957656.cao.2341092.0", "docs/carrybox/render6s_20261014/scale4096/train/model_0.pt", "docs/carrybox/render6s_20261014/scale4096/train/model_3.pt", "docs/carrybox/render6s_20261014/scale4096/train/model_6.pt", "docs/carrybox/render6s_20261014/scale4096/verification_model.pt", "docs/carrybox/render6s_20261014/source_hashes.json", "docs/carrybox/render6s_20261014/test_receipts.json", "docs/carrybox/render6s_20261014/test_receipts_attempt1.json", "logs/rsl_rl/g1_carrybox_depth/walled4/camera_fast_20261014_143621/status.json", "logs/rsl_rl/g1_carrybox_depth/walled4/depth_fast_20261014_150357/status.json", "projects/README.md", "projects/findbox/README.md", "scripts/rsl_rl/benchmark_carrybox_render.py", "scripts/rsl_rl/benchmark_carrybox_render.sh", "scripts/rsl_rl/train_carrybox_walled.sh", "source/perceptual_ball/perceptual_ball/carrybox_camera.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_walled_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_camera.py"]
task_contract_sha256: "581a35b88b2768ac44a974f420509badded724b587c72d1a20f2b3c4aa11aa0b"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_carrybox*.py -v", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "92f70112e537d24b924ce67a25ba6bc941f6e81f0943e1b23723badcdbb5cfe4", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "09a9901d10d85138df82dd7f7fc1638bec5110e4e1a129176109618fbf350d43", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/benchmark_carrybox_render.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "47a151fa20ba412b0d85024b068c09e7ce02c4c6837adb2aa1d3462629c3a03f", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

# Wall4 4096完整迭代性能排查（2026-10-14）

目标<=6秒/轮尚未达成。本次4096×24、PPO 4 epochs×4 minibatches及完整AMP验证8轮，热身后17.317–17.692秒、均值17.434秒；旧正式run末10轮均值21.052秒。时间下降约17.2%，但不同轨迹的窗口比较不是严格逐轨迹A/B。2026-10-14 15:09 JST：正式wall4 4096环境已从原正式model_0.pt恢复，PID2341959，检查到iteration2；后两轮17.62/17.42秒，schema2/revision4、策略与AMP有限值检查通过。6秒目标未达，训练尚未完成或证明收敛。

## 实际修改与限制

- 仅walled使用的FabricTiledCamera缓存固定安装局部位姿；reset安装setter更新所选行，world/from_view setter使缓存失效，初始化清空缓存。父体世界变换每帧仍从Fabric读取，保留selection刷新。
- walled RenderCfg使用performance并关闭direct lighting、shadow、DL denoiser和AA。实际运行设置已dump，AA op=0、cache=false。renderer/hydra waitIdle、同步annotator和reset重渲染保留。
- 当前训练没有直接写camera._view或USD变换的旁路；未来这种直接写入必须同步失效mount缓存。
- actor/critic仍只有深度与本体，辅助真值仅用于监督；分辨率48×27、50Hz、深度扰动/延迟、奖励、动作范围、终止、原始FindBox数据均未改。足球和Isaac系统安装未修改。

## 验证与失败记录

22项CPU检查通过；4环境运动/逆序partial reset用PhysX torso×直接USD local独立验证相机位姿；baseline与depthfast三组全深度图（箱子可见、墙遮挡、圆柱遮挡）max误差均0。geometry验证真实碰撞和遮挡一致；4096完成4轮训练、保存加载、再4轮，参数有限，schema2/revision4兼容。[原样测试回执](test_receipts.json)、[深度对照](depthfast4/result.json)、[geometry](geometry/geometry.json)、[4096结果](scale4096/result.json)。这些是工程运行证据，不是收敛或独立拾箱成功率。

第一次失败是canonical遮挡用例被此前运动/倒地机器人自身遮挡；测试重置到原geometry相同默认姿态后通过，未放宽阈值。其后FSD候选先因缺少population扩展加载失败；显式启用已安装delegate后，4.5 physxstageupdate明确报告不支持FSD物理仿真并禁用physics。静态插件/配置键存在不能推出物理训练可用。已撤回全部FSD参数，失败日志及回执保留于fabric4/attempt*和attempt*_test_receipts.json。生产修正为加载依赖、撤回不支持的FSD两次。

## 剩余瓶颈

[独立4步profile](scale4096/profile.txt)：总2.588秒，8次render累计2.107秒（约81%）；16物理子步0.250秒；相机pose读累计0.018秒，前版约0.676秒。缓存消除了重复CPU局部位姿遍历，RTX render仍占主导，折算24步的渲染调用约12.64秒（这是profile换算，完整迭代实测见上）。

每控制步正常渲染一次；4096环境几乎每步有部分reset，因此再渲染一次，保证reset后的相机/箱子/障碍首帧同步。删除第二次渲染会改变观测时间语义，没有采用。用户提供X2说明使用ray-cast，本地为RTX；下一步若坚持<=6秒，需单独验证动态mesh ray-cast深度路径，覆盖机器人自遮挡、箱子/墙/圆柱/平台、移动刚体、相机标定和reset首帧。这一后端迁移本次未实现，不能承诺倍率。当前Isaac Sim4.5不能使用FSD绕过。

动作目标范围与pickUp参考不一致的已知收敛风险仍未处理；性能优化不代表搬箱成功率改善。

## 正式运行

启动时间2026-10-14T15:03:57.781970+09:00，PID 2341959，状态RUNNING，15:09已核验iteration2。从原正式model_0.pt恢复；旧run未保存的19轮不能恢复。未使用docs内验证模型。

```bash
cd /home/cao/perceptual_ball
tail -n 100 -F logs/rsl_rl/g1_carrybox_depth/walled4/depth_fast_20261014_150357/train.log
```

[启动身份](launch.json)、[耗时比较](comparison.json)、[源文件hash](source_hashes.json)。不要重复启动，实际进程以/proc与日志核对。

[正式恢复验收](formal_health.json)、[恢复来源模型核验](resume_checkpoint_health.json)。

工程状态PARTIAL因为用户<=6秒目标未达；冻结验证全部PASS。本次小范围候选已到停止条件，正式恢复已实测验证。进一步提速优先单独验证动态ray-cast后端（需要覆盖动态遮挡与首帧同步），本次未实施，未承诺倍率。禁止重复启动或将docs验证模型作为正式恢复来源。
