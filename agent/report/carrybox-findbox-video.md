---
task_id: "carrybox-findbox-video"
language: "zh-CN"
axes: ["S"]
risk_tier: "T1"
status: "DONE"
changed_files: ["scripts/visualize_findbox.py", "scripts/visualize_findbox.sh", "docs/carrybox/dataset_visualization/README.md", "docs/carrybox/dataset_visualization/test_receipts.json", "projects/README.md", "projects/carrybox/README.md", "outputs/carrybox/findbox_dataset/preview_12.png", "outputs/carrybox/findbox_dataset/latest_preview.png", "outputs/carrybox/findbox_dataset/preview_13.png", "outputs/carrybox/findbox_dataset/preview_09.png", "outputs/carrybox/findbox_dataset/preview_17.png", "outputs/carrybox/findbox_dataset/preview_05.png", "outputs/carrybox/findbox_dataset/verification.json", "outputs/carrybox/findbox_dataset/preview_01.png", "outputs/carrybox/findbox_dataset/findbox_dataset.mp4", "outputs/carrybox/findbox_dataset/preview_04.png", "outputs/carrybox/findbox_dataset/preview_08.png", "outputs/carrybox/findbox_dataset/render.log", "outputs/carrybox/findbox_dataset/preview_02.png", "outputs/carrybox/findbox_dataset/preview_07.png", "outputs/carrybox/findbox_dataset/preview_06.png", "outputs/carrybox/findbox_dataset/preview_03.png", "outputs/carrybox/findbox_dataset/recording.json", "outputs/carrybox/findbox_dataset/preview_16.png", "outputs/carrybox/findbox_dataset/preview_10.png", "outputs/carrybox/findbox_dataset/preview_15.png", "outputs/carrybox/findbox_dataset/preview_11.png", "outputs/carrybox/findbox_dataset/preview_14.png"]
task_contract_sha256: "9509c3be8d4dc8ae2bae8402309ab047dd26fa56985b7513466ebc1ae8ef8636"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/visualize_findbox.py --verify-only --output outputs/carrybox/findbox_dataset", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "de8cea9f0ee2d7ba99116767bd99ad3787211ddaad32d282c94fd7b991ba1690", "stdout_sha256": "f1e09266ecc9ae8f11f4627bf55d8e4d6af1f0591fc51a4374a68fc30eeeebe5", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

已录制全部17段FindBox动作，输出outputs/carrybox/findbox_dataset/findbox_dataset.mp4，960×720、30fps、2318帧、77.27秒。使用当前G1按名字映射关节和xyzw→wxyz，RGB运动学回放，不运行策略或接触动力学。箱体位置来自记录，yaw和支撑台是标明的示意。检查了拾起中间帧和站立/持箱画面。

全帧解码、帧数/尺寸/帧率和源数据hash检查PASS。首次录制视频正常close后detach API兼容错误，已修复代码，recording.json从完整17段日志恢复，verify核对全部输出帧；未重复渲染既有成片。足球进程2056902仍存在，未停止或重启。项目索引已更新。
