---
task_id: "carrybox-findbox-video-20261014"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
status: "DONE"
changed_files: ["docs/carrybox/dataset_visualization/export_clips.py", "docs/carrybox/dataset_visualization/README.md", "docs/carrybox/dataset_visualization/clip_test_receipts_20261014.json", "projects/findbox/README.md", "projects/README.md", "agent/plan/carrybox-findbox-video-20261014.md", "agent/task/carrybox-findbox-video-20261014.md", "agent/report/carrybox-findbox-video-20261014.md", "agent/handoff/carrybox-findbox-video-20261014.md", "outputs/carrybox/findbox_dataset/clips/README.md", "outputs/carrybox/findbox_dataset/clips/carryWith/carrywith1.mp4", "outputs/carrybox/findbox_dataset/clips/carryWith/carrywith2.mp4", "outputs/carrybox/findbox_dataset/clips/carryWith/carrywith3.mp4", "outputs/carrybox/findbox_dataset/clips/index.json", "outputs/carrybox/findbox_dataset/clips/loco_direction/B10_-_walk_turn_left_(45)_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B11_-_walk_turn_left_(135)_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B12_-_walk_turn_right_(90)_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B13_-_walk_turn_right_(45)_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B14_-_walk_turn_right_(135)_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B15_-_walk_turn_around_(same_direction)_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B1_-_stand_to_walk_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B2_-_walk_to_stand_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B2_-_walk_to_stand_t2_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B3_-_walk1_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/loco_direction/B9_-_walk_turn_left_(90)_stageii.mp4", "outputs/carrybox/findbox_dataset/clips/pickUp/pickup1.mp4", "outputs/carrybox/findbox_dataset/clips/pickUp/pickup2.mp4", "outputs/carrybox/findbox_dataset/clips/pickUp/pickup3.mp4", "outputs/carrybox/findbox_dataset/clips/verification.json"]
task_contract_sha256: "fa3a771e7200f491d914764d2bfccfe33a37bd259a001a49d7a50b4ed716af28"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python docs/carrybox/dataset_visualization/export_clips.py --verify-only", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "f3644c99dc64615fcb5e3c8535e1c4033237ee0456fbd6d58cf7837ce4d4e60b", "stdout_sha256": "09a15b562f3c4b96f9a57f5298b9217c098344b5058e64d18d1b532e1952de14", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

当前17段源数据及manifest与2026-10-13录像记录hash一致。复用既有G1运动学录像，按准确帧序新增17段H.264/yuv420p独立MP4，输出位于outputs/carrybox/findbox_dataset/clips/，由README.md逐段链接。完整合辑保留原路径。共2318帧、77.27秒、960×720、30fps。全部帧完整解码并对应比较通过；最大单帧平均绝对像素误差2.314/255，为CRF18再编码误差。抽查拾箱、持箱及转弯画面。

数据、manifest、训练代码、checkpoint及已有完整录像均未改动；未启动仿真或改变训练进程。箱体yaw及支撑台继续为示意。源数据运动学回放不能作为学习成功率证据。

复核命令：`/home/cao/ENTER/envs/ball/bin/python docs/carrybox/dataset_visualization/export_clips.py --verify-only`。项目入口及总看板已更新，交接无待执行步骤。
