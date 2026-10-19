# Wall5 最新 checkpoint play录像（2026-10-20）

本次选择时最新完整模型：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-19_21-59-02_wall5_v17_loco_feedback_fresh_20261019_215857/model_2800.pt`，revision17，iteration 2800。
选定时间：2026-10-20T00:56:00.855343+09:00。录制期间后台可能继续生成新模型，本视频固定使用上述身份。

[观看20秒MP4](../../../outputs/carrybox/wall5_latest_play_20261020/wall5_rev17_model2800_play_20s.mp4) · [关键帧拼图](../../../outputs/carrybox/wall5_latest_play_20261020/contact_sheet.jpg)

单环境、seed42、均值动作、50Hz控制、25fps、1280×720，1000个控制步连续录制。保留自动reset、原传感器噪声、遮挡、碰撞和推扰；没有挑选成功片段。当前固定技能配额在单环境下为loco，因此每次都从空手行走参考起点开始，箱子在地面；没有hold参考起点伪装地面拾箱。旁观相机跟随机器人与箱子中点，放在墙的对侧；右下角为actor实际最新深度历史帧，该旁观相机不进入策略。

严格核对全部checkpoint环境契约并严格加载actor/critic权重；无优化器更新、无AMP学习。按本run锚点0恢复至2800轮：箱子yaw范围2.80°，推扰课程强度0.45。没有使用构造时0°/无推扰的简化环境。

## 观察与验证

已检查0.04、1、2、5、10、15、19.96和20秒画面，机器人与箱子清晰可见。此段空手起点回放能向箱子移动，前两秒接近后主要在箱旁站立；第999步相对首步水平位移约1.33m，距箱约0.41m。箱子仍在地面，没有完成抱起。整段没有倾倒/低高度终止，唯一reset发生在第1000步，是20秒超时；这不能代替多起点稳定行走评估。

完成1次自动reset，窗口末回合已持续0.00秒。记录到严格lift成功标记的完成回合数为0；窗口末回合标记为False。这是一段单环境视频，不是成功率评估。

| 回合 | 时长 | 结束原因 |
|---|---:|---|
| 1 | 20.00s / 1000步 | timeout |
| 窗口末回合 | 0.00s / 0步 | reset后的新起点，未执行动作 |

完整视频解码检查PASS：500帧、25.0fps、20.00秒，约6.20MiB。模型权重、源文件hash及checkpoint均保持不变。原后台训练PID254358在2026-10-20T01:01:37.267176+09:00检查时存活=True；本次未停止或重启训练。并行渲染会暂时共享GPU资源。

[模型选择](selection.json)、[录制配置和回合](recording.json)、[逐步轨迹](trajectory.json)、[视频核验](video_validation.json)、[执行回执](receipts.json)。

首次录像的旁观相机被墙遮挡，解码通过但人工画面检查失败。原视频、轨迹和回执保存在两输出目录的`attempt1_occluded_camera/`。仅调整旁观相机方位重新录制相同seed/模型，追加排除文字/深度角标的主画面检查；没有调整任务或选择性删掉失败回合。

复现入口（已存在的视频不会被覆盖；再次录制需另存目录）：

```bash
cd /home/cao/perceptual_ball
bash docs/carrybox/wall5_latest_play_20261020/record_and_check.sh
```
