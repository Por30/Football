# Wall4 4096环境相机位姿性能优化

2026-10-14，用户要求缩短训练耗时。原4096进程2330803已核验身份后停止，最后日志23/40000，最近保存model_0.pt；未保存的后续迭代不能恢复。旧run/日志完整保留。优化验证模型只在本docs目录，正式训练仅恢复原正式checkpoint。

原日志最近10轮采样约23–25秒、网络更新约1.5秒。4096环境×24步=98304样本/迭代，保持40000迭代会采集约39.3亿样本；128环境相同迭代数约1.23亿样本，不能只比较迭代时间而忽略32倍样本量。日志ETA显示可能省略天数，不应按显示的小时数判断总时长。

候选限制在walled专属TiledCamera子类：全量批量读取PhysX拥有的torso Fabric位姿，读取当前局部相机位姿并在GPU组合。每次查询前刷新parent Fabric selection，避免只有physics-step回调而reset/render没有物理步时读取旧storage。相机自身不创建Fabric world变换，避免干扰相机随父体运动。仍保留50Hz、48×27、RTX深度遮挡、安装扰动、延迟/冻结和标签配对；动作、奖励、AMP/PPO参数、4096规模和数据均不变。基线CarryBox-v0/football的camera选择不变。

诊断过程中：最初检查脚本异常被Isaac app.close遮蔽，增加显式traceback记录；第一版直接读取camera Fabric world在首帧偏差约4.57cm，废弃；改为parent×local后部分reset仍偏差约20cm，定位并刷新Fabric selection后通过4环境独立PhysX×直接USD local对照。各次失败日志与receipt保留，未部署这些失败候选。

4环境运动、[3,1]逆序部分reset、只更新选择行、有限值和坐标约定通过；现有真实墙/圆柱深度遮挡、碰撞与平台支撑检查通过。4096基准及保存恢复已通过，正式运行见本页末尾。测试包括22项CPU、真实4环境等价/遮挡及4096原读取/新读取对照与2+2 PPO/AMP保存恢复。计时与cProfile独立进行，防止Python profiler放大原路径开销；初始化不计入稳态。

## 实测结果

| 指标 | 原读取 | 优化读取 |
|---|---:|---:|
| 同规模同动作，48步平均环境步耗时 | 0.9557秒 | 0.7339秒 |
| 上述环境采样吞吐 | 4286 transitions/s | 5581 transitions/s |
| 独立4步profile中相机位姿累计时间 | 1.618秒 | 0.676秒 |

环境步减少23.2%，吞吐提高30.2%。完整2+2次PPO/AMP更新平均21.11秒/轮（首轮包括额外初始化），此前正式最近10轮平均25.63秒；前者短测与正式轨迹并非逐步完全相同，不能把两者当作严格A/B收敛比较。原、新profile中render约2.2秒/4步，成为剩余主要耗时；未删除reset后的渲染，否则可能让新回合首帧深度与标签不一致。

位姿独立参考为PhysX torso×直接USD局部变换；4与4096测试中最终候选最大位置/旋转误差均0（浮点输出），与原getter误差在冻结容差内。4环境pair检查验证同一步缓存一致，延迟/冻结/partialreset配对由原有CPU PairedDepthBuffer回归覆盖，不能单凭同一步getter断言推广为动态全流程证明。

[22项CPU及仿真回执](test_receipts.json)、[4环境位姿](pose4/benchmark.json)、[RTX遮挡/碰撞](geometry/geometry.json)、[4096速度和2+2更新](scale4096/benchmark.json)、[比较摘要](comparison.json)。首次Fabric子相机直读与旧selection候选的失败日志保留，最终使用已通过版本。

## 正式恢复

2026-10-14 14:41 JST：4096环境wall4相机位姿读取优化通过22项CPU、4环境运动/reset/遮挡及4096同规模速度和2+2 PPO/AMP恢复检查；原进程停止后从原正式model_0.pt恢复，新PID2336376。已检查到iteration2，正式后两轮21.16/20.90秒（此前约25.63秒）；同动作环境步耗时减少23.2%。保持4096、48×27/50Hz RTX遮挡、奖励、控制和AMP数据，尚未证明任务收敛。

新run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_14-36-28_wall4_4096_camfast_20261014_143621`。源checkpoint为`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/2026-10-14_14-06-14_wall4_4096_20261014_140607/model_0.pt`，只恢复正式模型，不使用benchmark验证产物。

```bash
tail -n 80 -F /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled4/camera_fast_20261014_143621/train.log
```

[正式进程与参数](launch.json)、[初始迭代及checkpoint核验](formal_health.json)。按20.9秒/轮，40000轮仍约9.7天；训练早期短窗估计随回合/渲染负载变化。旧23轮中未保存部分无法恢复。动作目标范围/参考拾取问题未在本轮调整。
