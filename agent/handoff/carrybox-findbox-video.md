---
task_id: "carrybox-findbox-video"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
status: "DONE"
changed_files: ["scripts/visualize_findbox.py", "scripts/visualize_findbox.sh", "docs/carrybox/dataset_visualization/README.md", "docs/carrybox/dataset_visualization/test_receipts.json", "projects/README.md", "projects/carrybox/README.md", "outputs/carrybox/findbox_dataset/preview_12.png", "outputs/carrybox/findbox_dataset/latest_preview.png", "outputs/carrybox/findbox_dataset/preview_13.png", "outputs/carrybox/findbox_dataset/preview_09.png", "outputs/carrybox/findbox_dataset/preview_17.png", "outputs/carrybox/findbox_dataset/preview_05.png", "outputs/carrybox/findbox_dataset/verification.json", "outputs/carrybox/findbox_dataset/preview_01.png", "outputs/carrybox/findbox_dataset/findbox_dataset.mp4", "outputs/carrybox/findbox_dataset/preview_04.png", "outputs/carrybox/findbox_dataset/preview_08.png", "outputs/carrybox/findbox_dataset/render.log", "outputs/carrybox/findbox_dataset/preview_02.png", "outputs/carrybox/findbox_dataset/preview_07.png", "outputs/carrybox/findbox_dataset/preview_06.png", "outputs/carrybox/findbox_dataset/preview_03.png", "outputs/carrybox/findbox_dataset/recording.json", "outputs/carrybox/findbox_dataset/preview_16.png", "outputs/carrybox/findbox_dataset/preview_10.png", "outputs/carrybox/findbox_dataset/preview_15.png", "outputs/carrybox/findbox_dataset/preview_11.png", "outputs/carrybox/findbox_dataset/preview_14.png"]
task_contract_sha256: "9509c3be8d4dc8ae2bae8402309ab047dd26fa56985b7513466ebc1ae8ef8636"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_dataset", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "de8cea9f0ee2d7ba99116767bd99ad3787211ddaad32d282c94fd7b991ba1690", "stdout_sha256": "f1e09266ecc9ae8f11f4627bf55d8e4d6af1f0591fc51a4374a68fc30eeeebe5", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

稳定产物为outputs/carrybox/findbox_dataset/findbox_dataset.mp4及recording.json/verification.json。用户可直接查看77.27秒全17片段视频；video不是学成策略表现，boxyaw/support是示意。

复现：bash scripts/visualize_findbox.sh。检查：/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_dataset。本次现有视频已经全帧核验；渲染末尾兼容错误发生在writer关闭之后，已修脚本并从日志补齐元数据，细节见report。无在运行的录制任务，不改变已有足球训练或源数据。
