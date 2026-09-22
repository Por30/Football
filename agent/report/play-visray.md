---
task_id: "ENG-PLAY-VISRAY-20260922"
language: "zh-CN"
axes: ["P"]
risk_tier: "T2"
status: "DONE"
changed_files: ["agent/handoff/play-visray.md", "agent/plan/play-visray.md", "agent/report/play-visray.md", "agent/task/play-visray.md", "docs/play_visray/README.md", "docs/play_visray/receipts.json", "docs/play_visray/smoke.json", "docs/play_visray/smoke.log", "docs/play_visray/summary.md", "docs/play_visray/visray.png", "scripts/rsl_rl/cli_args.py", "scripts/rsl_rl/depth_ray_visualizer.py", "scripts/rsl_rl/play.py", "scripts/rsl_rl/smoke_play_visray.py", "scripts/rsl_rl/smoke_play_visray.sh", "tests/test_play_visray.py"]
task_contract_sha256: "8e6c6c23552c7cba0fc0bbe93c535736d4afa254ccf5d5d2bb946a12da58153d"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_play_visray.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "818d97039fbc13253909369a2f600424b10263246dcc9f9a28261700e190b3f6", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "0a7487dd447ed39892a423a22370611e100bf0b90f72781bde8e794e93941693", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_play_visray.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "eb53140c952e2f431bc54ddc3061142478b394230e1138874ab7b672e0ed9b14", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

play新增默认关闭的--visray开关，可与--ballspeed并用。只在开启时导入debug_draw，绘制绿色稀疏像素射线和全部深度端点；球面返回使用明亮大点，远量程使用淡绿小点。可视化复用当前实例化感知项ray方向、安装偏移、躯干位姿与最后历史帧，不调用观测、不消耗RNG、不写入策略/物理/课程。退出finally清理图元。仅支持即时synthetic_ball_depth_image，延迟子类明确报错防止时刻错配。

五项CPU测试与真实Isaac仿真smoke通过。实际加载用户model_25000.pt，v0、4环境、ballspeed0.4–3、20控制步，稳定显示5184点/288线；确认历史和RNG未改变，清理后图元为0。截图为[720, 1280, 3]，绿色像素10018，非空场景校验通过。截图visray.png已用图像工具检查。首次截图因RGB annotator懒加载是黑帧，补渲染预热；随后发现Gym OrderEnforcing不转发recompute参数，修正为直接从base环境读取；最终有绿色像素断言，未把空白截图当作显示成功。

原训练与reward文件未更改。不启动长训练、不控制用户其他进程。GUI交互未由人手测试；验证是实际离屏渲染、计数与截图检查。解析深度只与球相交，远端点是最大量程边界，不代表地面/机器人点云；debug draw射线可穿过机身/地面。这是现有感知模型的准确显示。默认使用debug_draw全局点/线接口，与另一个清空相同接口的调试层不能并用。

用户完整命令与解释见docs/play_visray/README.md。删去--visray关闭。复核用bash scripts/rsl_rl/smoke_play_visray.sh；截图smoke需--enable_cameras，用户普通GUI播放不需要此附加参数。

