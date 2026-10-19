# Wall5 revision14 model11000 play录像

用户指定模型：`logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_00-37-11_wall5_v14_asymmetric_fresh_20261019_003706/model_11000.pt`。

录像输出：[`wall5_rev14_model11000_play_20s.mp4`](../../../outputs/carrybox/wall5_play11000_20261019/wall5_rev14_model11000_play_20s.mp4)。单环境、均值动作（标准play）、seed42、连续20秒、50Hz控制／25fps编码、1280×720。自动reset、传感器噪声、障碍物和原推扰保持；不跳过失败、不拼接挑选成功回合。画面标注时间、RSI初始化技能、reset次数；右下角是actor实际读取的最新深度历史帧，近处亮、远处暗。

当前生产源码已是revision15；本次独立录制脚本通过包内别名加载 `docs/carrybox/wall5_push_20261019/before/` 保存的revision14配置与环境类，严格比较完整checkpoint环境契约并严格加载全部actor/critic权重。保持旧直接设速度推扰、地面/default 0.5/average，未将当前1.0/multiply增量推扰混入旧模型播放。课程以本run锚点0重建至11000轮（箱yaw范围12°，推扰满强度），不是默认构造时0°/无推扰。

这是独立推理视频，不更新策略、优化器或AMP，也不修改checkpoint、数据或后台训练。视频中如果显示RSI hold，表示直接从参考持箱姿态初始化，不能算从地面找箱并拾取成功。完整配置、模型及归档源码hash、完成回合和窗口末存活年龄写入 `recording.json`；逐步机器人/箱子轨迹在 `trajectory.json`。

复现命令（先核对GPU资源；现有视频不会被覆盖）：

```bash
bash docs/carrybox/wall5_play11000_20261019/record_and_check.sh
```

该脚本先严格回放录制，然后完整解码MP4，核对500帧、25fps、20秒、分辨率和非静止画面；回执与最终观察结论随录制结束写入。

## 验证与观察结果

实际录制：完成2个回合，loco 10步（tipped，pitch=1.225rad）；loco 10步（tipped，pitch=1.151rad）。窗口结束仍处于hold起点回合，已经持续980步（19.60秒），未完成回合。这段视频未展示从地面找箱并完整抱起的成功流程。

MP4完整解码通过：500帧、25fps、20.00秒、1280×720，文件约3.98MiB。初始、2秒、10秒与最终画面人工检查，机器人和箱子保持可见；[关键帧拼图](../../../outputs/carrybox/wall5_play11000_20261019/contact_sheet.jpg)。详见[录制元数据](recording.json)、[视频检查](video_validation.json)、[测试回执](receipts.json)。

2026-10-19T12:31:41.896746+09:00正式PID4038923存活=True；未停止或重启。当前生产源码仍revision15，本视频使用独立归档revision14。
