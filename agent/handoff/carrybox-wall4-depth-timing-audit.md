---
task_id: "carrybox-wall4-depth-timing-audit"
language: "zh-CN"
axes: ["P"]
risk_tier: "T1"
status: "DONE"
changed_files: ["scripts/rsl_rl/summarize_carrybox_timing.py", "projects/findbox/README.md", "projects/README.md", "docs/carrybox/depth_timing_20261014/timing.json", "docs/carrybox/depth_timing_20261014/README.md", "docs/carrybox/depth_timing_20261014/test_receipts.json", "agent/plan/carrybox-wall4-depth-timing-audit.md", "agent/task/carrybox-wall4-depth-timing-audit.md", "agent/report/carrybox-wall4-depth-timing-audit.md", "agent/handoff/carrybox-wall4-depth-timing-audit.md"]
task_contract_sha256: "6f3c2965a1a70f964db47464a6b75bd9755c6af8bfc0dbac61427d541189ef95"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/summarize_carrybox_timing.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "14b1e0008735101b4b5506813462eb70fa23c5ef53788083ba3b51622ef9ab3e", "stdout_sha256": "5d2dcddc0a9eb684d15726e3b9411062fe0a81a10360b260607434bfdc9995d0", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

# G1当前深度后端与分项耗时核对

2026-10-14 15:12 JST：本次复读上一轮4096真实profile，并只读当前正式日志；没有再次启动GPU测速，没有停止或重启训练。所有profile记录的源码hash与当前文件一致。当前PID2341959身份吻合，记录到iteration13；最近10轮均值采样15.735秒、学习1.520秒、合计17.255秒。

## 与用户提供X2说明的差异

| 项目 | 用户提供的X2说明 | 本地G1实际代码 |
|---|---|---|
| 深度后端 | MultiMeshRayCasterCamera / Warp | FabricTiledCamera继承TiledCamera / RTX；当时没有迁移X2 ray-cast后端 |
| 挂载 | head_pitch_link | torso_link/CarryDepth，使用G1名义D435安装变换 |
| 更新 | lazy开启，读取才ray-cast | lazy_sensor_update=False，48×27/50Hz，reset重渲染开启 |
| 深度/本体历史 | 各5帧 | 各4帧 |
| critic | 箱子真值 | 与actor相同，只读本体和深度；箱子真值仅监督/奖励/reset |

代码依据：`carrybox_camera.py`的基类，`carrybox_env_cfg.py`的TiledCameraCfg和4帧history，`carrybox_walled_env_cfg.py`的class_type/scene配置，以及`CarryBoxActorCritic`对policy/critic组的强校验。`Fabric`仅指位姿读取，并不意味着使用Warp生成深度。当前本地IsaacLab/PhysHSI/本仓源码路径检索未找到用户所述MultiMeshRayCasterCamera源码，不能把其X2细节当作已在本地执行的实现。

## 已有实测分项

4096环境，4个policy步：

| 调用 | 次数 | 累计host耗时 | 每policy步 |
|---|---:|---:|---:|
| env.step | 4 | 2.587s | 646.9ms |
| sim.render（含场景更新及同步） | 8 | 2.107s | 526.7ms |
| PhysX _step | 16 | 0.248s | 62.1ms |
| camera buffer更新 | 8 | 0.0235s | 5.87ms |
| 深度读取/归一化 | 16 | 0.0152s | 3.80ms |
| 帧标签配对、噪声/延迟/冻结入口 | 16 | 0.0601s | 15.03ms |

camera pose包含在camera buffer中；配对入口包含深度读取和位姿标签计算。这些累计调用是嵌套的，不能相加。cProfile记录host函数耗时，原probe仅在每个env.step后CUDA同步；它没有提供分kernel CUDA时长，不能把render的81.4%解释为纯GPU光线求交占比，也不能将后处理host时间当作精确GPU成本。当前证据足以定位到render调用路径，不能进一步断言内部是光追还是USD场景同步主导。

当前正式日志中learning包含完整PPO、辅助回归和AMP更新；没有拆成仅PPO计算。8轮短测及当前正式日志是独立于profile的完整迭代计时。

## 后续方向与边界

优先核对并移植动态多网格ray-cast后端，而非继续把X2的自遮挡网格数量或lazy行为套到当前RTX训练。迁移需保留地面、移动箱子、平台、墙柱及机器人自遮挡、G1相机坐标/光轴深度、50Hz、reset首帧同步；不能用仅静态地面的RayCaster替代。先保持这些语义再测速，6秒结果不能预先保证。

teacher/student会改变此前用户明确的无特权训练设计；本次没有采用。也未降低深度帧率、删自遮挡或改变网络历史。Warm-start只在契约兼容时使用，且当前已经从同一wall4正式checkpoint恢复；它不能直接降低单轮计算耗时。X2的收敛不证明本地G1已经收敛，动作覆盖问题仍单独待解决。

## 复查命令

```bash
cd /home/cao/perceptual_ball
/home/cao/ENTER/envs/ball/bin/python scripts/rsl_rl/summarize_carrybox_timing.py
```

这是已有计时的汇总工具，不是新GPU profiler。源码hash不一致会拒绝外推；读取最新正式日志会更新快照。[机器可读分项](timing.json)、[执行回执](test_receipts.json)。原始profile：`docs/carrybox/render6s_20261014/scale4096/sample.prof`。正式训练保持运行。
