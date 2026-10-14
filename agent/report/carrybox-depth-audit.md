---
task_id: "carrybox-depth-audit"
language: "zh-CN"
axes: ["P"]
risk_tier: "T2"
status: "DONE"
changed_files: ["scripts/audit_g1_depth.py", "scripts/audit_g1_depth.sh", "projects/findbox/README.md", "projects/football/README.md", "projects/README.md", "docs/carrybox/depth_audit/README.md", "docs/carrybox/depth_audit/baseline.json", "docs/carrybox/depth_audit/baseline.log", "docs/carrybox/depth_audit/baseline.png", "docs/carrybox/depth_audit/baseline_depth.npz", "docs/carrybox/depth_audit/geometry.json", "docs/carrybox/depth_audit/initial_cpu_render_receipts.json", "docs/carrybox/depth_audit/test_receipts.json", "docs/carrybox/depth_audit/walled3.json", "docs/carrybox/depth_audit/walled3.log", "docs/carrybox/depth_audit/walled3.png", "docs/carrybox/depth_audit/walled3_depth.npz", "docs/carrybox/depth_audit/walled4.json", "docs/carrybox/depth_audit/walled4.log", "docs/carrybox/depth_audit/walled4.png", "docs/carrybox/depth_audit/walled4_depth.npz"]
task_contract_sha256: "be050d4ad207913e3b32262c90ca25eae029c5849a6dc97042c2457a61d60339"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python scripts/audit_g1_depth.py --geometry-only", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "10820eef28883b15c91920ec79a33c6825f40fdab2f56363571c693d4a15e584", "stdout_sha256": "db300d67fb6b1a14d69d3405c34fe49c70ab8d58c575520e25a682e4718eac1c", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/audit_g1_depth.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "6e06547bab3e82ee837f558a648b8e36b5bbecff44ba4a00f10331672d91b270", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

深度审计完成，结果见docs/carrybox/depth_audit/README.md。源URDF、已加载USD的D435 link及FindBox相机名义位置一致：[0.0576235,0.01753,0.42987]m，下俯47.6度；机器人平移/yaw后相对安装保持不变。另一个本地G1 URDF版本安装z低1cm，实机版本/光学外参/CameraInfo及预处理文件未提供，不能宣称具体实机部署已经一致。

冻结模型几何检查与CUDA RTX检查均PASS，baseline/walled3/walled4均完成光轴深度、生产观测逐像素归一化、墙/圆柱前遮挡、移除被遮挡箱子不改变像素、移除遮挡恢复箱子等断言。清晰箱面深度0.875m，墙面0.45m，walled圆柱中心像素约0.32144m；两项遮挡后移除箱子最大变化与恢复误差均为0。原始npz、可视化png及日志保存。

测试初次CPU设备得到零深度失败；一次范围内修复将探针切到与训练一致的CUDA路径，并使审计中的运动学物体移动只写pose，不写非法速度；未改生产reset。保留初次失败回执。最终测试三个变体均成功退出，无残留训练/审计作业。

Football源码核对：名义安装匹配，但解析深度只与球面相交，不含场景/自身遮挡，返回射线距离米，非FindBox的归一化光轴深度。本次没有改变生产相机、资产、足球训练或任务checkpoint。

审计使用1环境静态渲染，walled关闭RSI及传感器随机扰动以验证几何；未执行PPO，不解除此前walled CUDA700训练故障。深度扰动、时序缓存仍沿用已有实现，本轮不宣称实机噪声/时间同步已标定。

如用户提供实际部署目录，继续核对torso到depth_optical_frame变换、CameraInfo、深度对齐/裁剪/缩放/单位以及4帧时序。真实硬件一致性未完成，不因模型检查通过而改写为已标定。CB-006仍为训练集成阻塞。
