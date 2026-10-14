---
task_id: "carrybox-findbox-video-20261014"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["BUILD_TOOLING"]
original_request: "/home/cao/perceptual_ball/findbox  可视化这几段数据集 录制成mp4"
allowed_paths: ["docs/carrybox/dataset_visualization", "outputs/carrybox/findbox_dataset/clips", "projects/findbox/README.md", "projects/README.md", "agent/plan/carrybox-findbox-video-20261014.md", "agent/task/carrybox-findbox-video-20261014.md", "agent/report/carrybox-findbox-video-20261014.md", "agent/handoff/carrybox-findbox-video-20261014.md"]
forbidden_scope: ["更改原始数据、manifest、训练代码或checkpoint", "停止、重启或启动训练", "覆盖已有完整录像及历史校验记录"]
steps: ["核对当前17段数据与已有录像记录的hash和文件集合", "从匹配的完整录像按精确帧数导出17段独立MP4", "全帧解码核对覆盖、帧序、尺寸和帧率", "保存验证回执并更新项目索引"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/dataset_visualization/export_clips.py --verify-only"}]
stop_conditions: ["源数据与录像身份不匹配", "片段边界或帧率无法核对", "两次范围内修复后校验仍失败"]
safeguards: ["全部数据只读", "复用已核对hash的G1运动学录像", "仅CPU解码和编码且线程数限制为2", "完整解码核对输出帧数及其与原录像的逐帧对应"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

复用既有17段完整录像，按recording.json的video_frames顺序精确拆分。仅处理本地视频与文档，不启动仿真。验收17段覆盖全部源文件、所有帧可解码、分段图像与原录像对应。
