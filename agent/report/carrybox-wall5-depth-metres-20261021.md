---
task_id: "carrybox-wall5-depth-metres-20261021"
language: "zh-CN"
axes: ["P", "L"]
risk_tier: "T2"
artifact: "REPORT"
status: "DONE"
changed_files: ["agent/handoff/carrybox-wall5-depth-metres-20261021.md", "agent/plan/carrybox-wall5-depth-metres-20261021.md", "agent/report/carrybox-wall5-depth-metres-20261021.md", "agent/task/carrybox-wall5-depth-metres-20261021.md", "docs/carrybox/wall5_depth_metres_20261021/README.md", "docs/carrybox/wall5_depth_metres_20261021/artifact_validation.json", "docs/carrybox/wall5_depth_metres_20261021/audit.json", "docs/carrybox/wall5_depth_metres_20261021/before.json", "docs/carrybox/wall5_depth_metres_20261021/before_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "docs/carrybox/wall5_depth_metres_20261021/before_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "docs/carrybox/wall5_depth_metres_20261021/before_source/source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "docs/carrybox/wall5_depth_metres_20261021/cpu.log", "docs/carrybox/wall5_depth_metres_20261021/cpu_pass", "docs/carrybox/wall5_depth_metres_20261021/expert_brief.json", "docs/carrybox/wall5_depth_metres_20261021/exported/manifest.json", "docs/carrybox/wall5_depth_metres_20261021/exported/policy.onnx", "docs/carrybox/wall5_depth_metres_20261021/exported/policy.pt", "docs/carrybox/wall5_depth_metres_20261021/finish.py", "docs/carrybox/wall5_depth_metres_20261021/launch.json", "docs/carrybox/wall5_depth_metres_20261021/launch.py", "docs/carrybox/wall5_depth_metres_20261021/launch.sh", "docs/carrybox/wall5_depth_metres_20261021/receipts.json", "docs/carrybox/wall5_depth_metres_20261021/restart.log", "docs/carrybox/wall5_depth_metres_20261021/smoke.json", "docs/carrybox/wall5_depth_metres_20261021/smoke.log", "docs/carrybox/wall5_depth_metres_20261021/smoke.py", "docs/carrybox/wall5_depth_metres_20261021/smoke.sh", "docs/carrybox/wall5_depth_metres_20261021/smoke_model.pt", "docs/carrybox/wall5_depth_metres_20261021/smoke_pass", "docs/carrybox/wall5_depth_metres_20261021/snapshot.json", "docs/carrybox/wall5_depth_metres_20261021/source_receipt.py", "docs/carrybox/wall5_depth_metres_20261021/start_and_verify.sh", "docs/carrybox/wall5_depth_metres_20261021/stop.py", "docs/carrybox/wall5_depth_metres_20261021/stopped_run.json", "docs/carrybox/wall5_depth_metres_20261021/validate_and_restart.sh", "docs/carrybox/wall5_depth_metres_20261021/validated_sources.json", "docs/carrybox/wall5_depth_metres_20261021/verify.log", "docs/carrybox/wall5_depth_metres_20261021/verify.py", "projects/README.md", "projects/findbox/README.md", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/carrybox_wall5_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_wall5.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/carrybox_walled.py", "tests/test_carrybox_depth_metres.py"]
tests: [{"command": "bash docs/carrybox/wall5_depth_metres_20261021/validate_and_restart.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "442393f5ec1e400f788931f2642883c7517ab841c888bc84a05ccb451b9b31fa", "stdout_sha256": "455e4d3523f0cbaf03e48ffdd34c2df919b5e95aec573bf7d8733d4f9e7abb63", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
task_contract_sha256: "8bf7b9ada3e58ae2af65fd0caad4e751bdc106966415b2731247bf0f2ed4098c"
---

# wall5 米制深度与噪声修正（revision21）

2026-10-21T13:49:46.006048+09:00 状态快照：代码、36项CPU回归、20环境更新/恢复/导出及4096正式启动验收通过。正式训练进行中，尚未评估稳定行走或拾箱成功率。

| 项目 | revision20 | revision21 |
|---|---|---|
| actor深度输入 | 光轴米值除3 | 光轴米值，直接输入 |
| 合法值/未命中 | [0.1/3,1]，未命中1 | [0.1,3]m，未命中3m |
| Gaussian标准差 | 0.06m | 0.02m |
| 立体噪声sigma参数 | 0.024–0.09m | 0.008–0.03m |

噪声数值采用用户最新对照。旧handoff.txt第205/210行显式乘3，当前修改按最新更正仅覆盖wall5；本机没有原始X2环境源码，未声称独立复算X2噪声或全部训练差异。边缘阈值0.15m、边缘/孔洞概率、相机安装/FOV/48×27分辨率/50Hz、4帧历史、延迟/冻结、机身/墙/圆柱遮挡和全部物理设置保持。

米制分支直接读取Warp distance_to_image_plane，NaN/±inf填3并裁剪，再在米制上加噪；缓存和CNN不再除3。可见性同步使用[0.1,3)和nearest Box hit，丢失像素即使保有Box ID也不参与监督。捕获时将深度、光学位姿、visibility整体配对，再延迟/冻结；同一步部分reset不污染幸存环境。

新增env.depth_contract，既有play导出调用自动写入manifest.metadata.depth_contract。导出网络接受与训练相同的米制深度；不再在部署侧除3。契约包括光轴定义、单位/裁剪/未命中、输入形状、历史顺序与噪声。checkpoint升revision21，严格load/default play拒绝旧归一化契约；显式weights-only仍为既有绕过接口，不代表单位兼容。本次没有使用它或恢复旧权重。

用户同时列出critic和辅助监督差异；异步询问范围后，按已告知的建议方案只调整深度及噪声。critic保持108=93本体+3机体线速度+3箱位置+6旋转+3尺寸，独立MLP。handoff的X2 proprio含额外末端位置15维，不能仅为对齐维数补零。当前rot6是相对骨盆旋转的前两列，CPU交叉积重建测试确认与完整相对旋转一致；没有原始X2代码可核验它取哪两列。辅助仍coef0.1、只监督可见且在深度范围内的捕获帧，避免要求深度编码器从看不见的箱子恢复无界真值。它们是保留的G1设计差异，不标为X2完全对齐。

revision20头高校正、无early_failure、独立多原因终止记录、RSI75/5/20、roll0.5、骨盆/近箱阈值、AMP/PPO/数据不变。wall3/4仍是归一化深度及原噪声；football源码未修改。

验证结果：36项CPU通过，覆盖1.5m输入值、非有限/裁剪/miss、两种单位、遮挡/边缘/孔洞、延迟/冻结/同step部分reset、噪声物理标准差、critic旋转和导出隔离。20环境实际Warp无噪声读回逐像素完全相等，范围0.272807–3m；23384个像素大于1m。实际配方PPO/AMP更新2轮、保存严格恢复后再1轮，参数有限；revision20严格恢复被拒绝；JIT导出并重新加载推理与内存actor一致，ONNX文件及manifest也已生成。ONNX本次仅导出，未独立执行ONNX Runtime。pilot均在docs下，不能作为正式训练/成功率证据。

旧PID1042917已停止，最后日志138轮；旧checkpoint `/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_13-29-36_wall5_v20_headfix_fresh_20261021_132931/model_0.pt` 及日志保留，之后未保存的尾部迭代没有恢复。新PID1046327，4096环境、seed42、40000轮，fresh，无resume/warm-start。已检查到日志迭代15，近10轮平均3.828s，最慢3.880s。首模型确认schema2/revision21、米制/noise/.1辅助系数、108维critic、原头高校正和全新优化器step20/AMP count61440。

正式目录：`/home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/2026-10-21_13-43-49_wall5_v21_depth_metres_fresh_20261021_134344`

```bash
tail -f /home/cao/perceptual_ball/logs/rsl_rl/g1_carrybox_depth/walled5/launch_wall5_v21_depth_metres_fresh_20261021_134344.log
```

[范围及数值审计](audit.json)、[只读专家核对](expert_brief.json)、[CPU日志](cpu.log)、[真实仿真结果](smoke.json)、[正式启动快照](snapshot.json)、[测试回执](receipts.json)。

