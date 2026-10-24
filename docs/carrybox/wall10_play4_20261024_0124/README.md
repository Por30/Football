# Wall10最新checkpoint回放：model_1000

wall10 model_1000四机器人同步20秒回放完成，1080p/25fps、seed42均值动作。四格均从loco地面箱起点开始，保留原随机reset、全部失败、本体噪声及力脉冲。各机器人reset为8/7/9/11次，地面起点未形成双手同时接触，未观察到从地面拾箱并保持；末段持箱来自pickup/hold参考起点，最长满足严格保持条件仅0.16秒，全部成功标记为false。

[播放视频（约20.8MB）](../../../outputs/carrybox/wall10_play4_20261024_0124/wall10_model_1000_4robots_20s_preview.mp4) · [完整原码率录像](../../../outputs/carrybox/wall10_play4_20261024_0124/wall10_model_1000_4robots_20s.mp4) · [关键帧拼图](../../../outputs/carrybox/wall10_play4_20261024_0124/contact_sheet.jpg)

2026-10-24 01:26 JST锁定当时最新完整正式checkpoint：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled10/2026-10-24_00-12-57_wall10_24step_fresh_20261024_001253/model_1000.pt`，SHA256 `52960b8d52e8879ba716915686506b972f1a56aa23507327e33f518d3473c732`。schema2、wall10 revision1、rollout24。严格核对环境契约并严格加载策略权重，录制前后权重与四个wall10生产源码hash一致。无需加载AMP优化器即可进行均值动作推理。

维持wall10完整任务设置；仅设4环境、缩小PhysX容量并配置旁观相机及直射照明。高位镜头基准5.8米、焦距20mm，四机同一物理时刻采集。actor实际米制深度逐像素核验，渲染不推进物理。预览与原视频均为500帧、25fps、20秒、1920×1080，全部解码通过；预览只降低编码码率，无剪裁时间、变速或补帧。

已检查初始画面、0.04/1/2/5/10/15/19.96/20秒拼图及5/10/20秒原分辨率帧。扩大20mm旁观视野后机器人与箱子完整可见，起点类型、reset和米制深度角标清楚；压缩预览末帧已另行查看。前段有接近、伸手、前倾和多次失稳，后段出现参考持箱。仅描述本次单seed录像，不能作为总体成功率或与wall5的同条件评估。

排除reset行，地面起点共3428个控制步样本，双手同时接触0次，箱底最高离地约2.55mm。31个已结束的default/loco回合全部失败；参考起点的持箱不能计为地面抓起。完整分组与回合证据见[行为记录](behavior.json)、[逐机器人记录](per_robot_behavior.json)、[轨迹](trajectory.json)。

录制结束后核对正式PID2402395仍在运行，日志到iteration1161（核对时间2026-10-24T01:35:57.404919+09:00），未停止、恢复或修改正式训练。此状态是快照，后续操作须重新核对。

首次脚本适配遗留配置类名造成启动失败，已修正并保存到attempt1_config_name；第二次录制预览发现标题遮住机器人2头部，主动中断并将完整中断材料保存在attempt2_framing，随后扩大旁观视野并补光，用同一模型、seed和任务设置重录。最终冻结检查PASS，原录像及预览均完整。

复现入口：`bash docs/carrybox/wall10_play4_20261024_0124/record_and_check.sh`（输出保护要求使用新的保存目录，现有视频不会覆盖）；预览编码见[prepare_video.py](prepare_video.py)。[模型选择](selection.json) · [录制记录](recording.json) · [原视频检查](video_validation.json) · [预览检查](delivery.json) · [测试回执](receipts.json)。
