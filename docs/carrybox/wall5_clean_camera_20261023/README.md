# Wall5 revision28：干净深度与早期低推扰

wall5 revision28关闭人工相机噪声、丢失、随机延迟/冻结和安装误差；推扰5000轮无扰动，随后10000轮增量爬升。15项CPU及64环境2＋1轮PPO/AMP、深度逐像素/标签/安装位姿、课程边界和严格恢复通过。旧PID2143205已停止，新PID2266428，4096环境从零启动，检查至19轮，近10轮平均3.938秒、最慢3.960秒。正式训练进行中，未验证抖动改善或抓取收敛。

| 配置 | revision27 | revision28 |
|---|---|---|
| 高斯深度噪声 | 0.02m | 0 |
| 距离相关深度噪声 | 0.008–0.03m | 0 |
| 边缘丢失 / 随机孔洞 | 5% / 2% | 0 / 0 |
| 深度随机延迟 | 10%概率延迟1步 | 0，单槽缓存 |
| 短时冻结 | 0.2%概率，最长15帧 | 0 |
| 相机安装位置 / 角度误差 | 0.01m / 0° | 0 / 0 |
| 推扰开始 / 爬升时长 | 1000 / 4000轮 | 5000 / 10000轮 |

推扰强度按有效训练迭代clamp((iter−anchor−5000)/10000,0,1)：0–5000轮为0，10000轮为0.5，15000轮后为1。保持当前COM世界速度加随机增量，原1–3秒事件间隔和最终幅度不变。课程仍以当前进程首次真实iteration为锚点，恢复新进程时沿用原有重新锚定行为。

真实G1相机名义安装、光轴米制0.1–3m、48×27、50Hz、4帧、机器人自身/障碍/地面遮挡保持。actor深度＋本体、critic123、辅助监督、AMP完整15段、RSI固定配额、自碰撞、PD、物理动作延迟0–20ms、奖励和终止保持。本次“减少早期扰动”具体指推迟和放缓外部速度推扰；其他物理随机化保持。

只修改wall5配置与其checkpoint revision；共享深度/AMP/PPO及football、wall3/wall4源码未变。schema仍为2，revision28可严格恢复；rev27完整恢复被拒绝。正式训练未加载旧权重、优化器或Normalizer。

实际仿真中73次捕获检查：actor最新深度与Warp原始光轴深度经既有缺失处理/裁剪后逐元素一致，标签来自当前帧，安装外参无随机误差。单槽连续/重复/partial reset、非零锚点的推扰0/0.5/1和无写入边界通过。两轮更新＋恢复后一轮，策略/CNN/辅助头/critic和AMP优化器均更新且有限；actor/critic恢复输出一致。失败首次测试保存在attempt1_mount_reference，原因是测试基准未包含名义相机坐标转换链；修正参考后保持原容差及生产实现，没有放宽断言。

验证模型仅在本docs目录，不能作为正式训练或任务成功证据。正式首model_0核验全新优化器20步、AMP Normalizer计数61440、配置与已验证契约一致。检查时间：2026-10-23T17:39:29.241386+09:00，当前快照不是训练完成或收敛结论。

- 正式run：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-23_17-35-18_wall5_v28_clean_camera_fresh_20261023_173513`
- 日志：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v28_clean_camera_fresh_20261023_173513.log`
- PID：`2266428`
- 旧run保留：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-23_12-44-38_wall5_v27_stability_fresh_20261023_124434`
- 旧进程最后保存：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-23_12-44-38_wall5_v27_stability_fresh_20261023_124434/model_4800.pt`

查看日志：

```bash
tail -f '/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v28_clean_camera_fresh_20261023_173513.log'
```

正式启动参数（已在运行，无需重复执行）：

```bash
/home/cao/ENTER/envs/ball/bin/python -u scripts/rsl_rl/train.py --task Template-Perceptual-Ball-CarryBox-Walled5-v0 --num_envs 4096 --device cuda:0 --headless --seed 42 --max_iterations 40000 --run_name wall5_v28_clean_camera_fresh_20261023_173513
```

[本轮源码差异](source_changes.patch) · [范围核验](scope_check.json) · [仿真检查](smoke.json) · [正式快照](snapshot.json) · [启动记录](launch.json) · [旧训练退出记录](stopped_run.json) · [测试回执](receipts.json)
