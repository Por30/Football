---
task_id: "carrybox-findbox-video"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
artifact: "TASK"
status: "FROZEN"
development_modes: ["BUILD_TOOLING"]
original_request: "可视化findbox任务用到的数据集 录制成mp4"
allowed_paths: ["scripts/visualize_findbox.py", "scripts/visualize_findbox.sh", "outputs/carrybox/findbox_dataset", "docs/carrybox/dataset_visualization", "projects/carrybox/README.md", "projects/README.md", "agent"]
forbidden_scope: ["修改数据、训练代码或checkpoint", "停止或重启足球进程", "真实设备操作"]
steps: ["核对数据与运行资源", "实现单机器人运动回放和MP4输出", "录制17段并检查画面", "校验视频帧数解码及原始hash并更新项目索引"]
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_dataset"}]
stop_conditions: ["可用资源不足", "帧/关节映射无法确认", "两次范围内修复后验证仍失败"]
safeguards: ["源文件只读", "按名字重排关节并转换四元数", "标记运动学回放及箱体朝向近似", "视频完成后全帧解码核验"]
expert_required: false
expert_brief: null
device_actions: []
real_device_authorized: false
---

全17段合成一个30fps MP4，以原始时间1x回放。RGB渲染仅一台G1，箱子位置使用原记录而yaw借用机器人朝向，支撑台仅辅助示意；AMP未使用这些物体字段。录制完成保留分段时间索引及预览。
