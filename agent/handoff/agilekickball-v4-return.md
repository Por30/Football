---
task_id: "AGILE-V4-RETURN-20261012"
language: "zh-CN"
axes: ["E", "L", "D"]
risk_tier: "T2"
status: "DONE"
changed_files: ["source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v4_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v4.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/rsl_rl_extensions/runner.py", "scripts/rsl_rl/train.py", "scripts/rsl_rl/train_agilekickball_v4.sh", "scripts/rsl_rl/smoke_agilekickball_v4.py", "scripts/rsl_rl/smoke_agilekickball_v4.sh", "tests/test_agilekickball_v4.py", "agent/plan/agilekickball-v4-return.md", "agent/task/agilekickball-v4-return.md", "agent/report/agilekickball-v4-return.md", "agent/handoff/agilekickball-v4-return.md", "docs/agilekickball_v4/README.md", "docs/agilekickball_v4/return_to_sender_20261012", "logs/rsl_rl/agilekickball_v4", "logs/rsl_rl/agilekickball_v4_smoke"]
task_contract_sha256: "d462ccfe5a7c0776711e2ccc420fffe31daa9cfe0a8fd7dcbad4040799e0bfb1"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v4.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "dd895161e70cf24168e576e63c5c1f79320403fdd25863cdb31e75fcb12f1e00", "stdout_sha256": "40062128c6201f1932fee91113de98f8f5a356ef10884e9f5a5d2bd2b4f3e57c", "stderr_sha256": "1bffd318c782531160a7798eaa55c507f6b3daf1e6023b9fdd06a480ff241f67", "runner": "run_engineering_tests.py"}, {"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_state_feedback.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "8a64957c8c0dbaa892b025807418a3d94725b313191624ba19ab65e0dc9d6912", "stdout_sha256": "d9929d5eb3ac84745ae25b709f62c07195ad73b114f227645401548e1ce37e34", "stderr_sha256": "0035126ec959250819e13e43a658402d7bb0af7f5f2ed14c17b30b0cac160508", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v4.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "5aea10875fd201e05e0d1d79f027628734ae1622e073a92ae060879f011b43af", "stdout_sha256": "74e834b04dedc41470f0bb06b2e623658390026f45e293fd7af5d2ea606ad81b", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "HANDOFF"
resume_command: null
---

v4 `return_to_sender_20261012` 已建立，原 v2/v3 配置文件 hash 保持一致。每轮发球点定义反向目标门，半宽 0.6→0.2 m；有效脚击球代理、单向线段插值穿越、球高/速度阈值防错误计分。奖励替换径向返回为源点质量，加入单次目标命中；保留 v3 网络、观察、空间边界、恢复条件及训练稳定设置。独立目标指标和完成轮次分母避免用 kick proxy 冒充回传成功。

完整加载最新 v3 model_49999.pt（含预测头/反馈/归一化/AMP），优化器、计数、速度及方向课程新建。167 项状态/旧 v3 回归与 12 项反馈测试通过；真实 CPU 仿真 3 个 PPO 更新、精确初始化、恢复/回放/课程冻结通过；4096 环境 100 轮正式入口短训通过。首轮 smoke 因测试复用 inference normalizer 缓存失败；仅将 play 验证改为新建 runner，第二次冻结检查全部通过，首轮失败回执保留。正式启动第一次在模拟器开始运行前发生原生 malloc 堆错误，未进入任务更新；无 OOM 或残留训练进程证据，日志保留在 formal_start_attempt1.log。资源检查后保持全部任务参数不变做一次重启；原生错误根因尚未确定，不能宣称已根治。

正式训练 PID 2056902，run `logs/rsl_rl/agilekickball_v4/2026-10-12_13-48-41_return_to_sender_20261012_v3init`，核验已到 iteration 15，checkpoint 有限，记录新版本和 v3 初始化来源。目标 50000 次迭代、4096 环境、seed42。启动/测试/source snapshot 证据均在 docs/agilekickball_v4/return_to_sender_20261012；运行日志 `/home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v4/train_20261012.log`。

已完成的是任务实现和训练启动，正式训练仍在后台运行。短测不证明已收敛或学会精确回传。0.2 m 是最终目标门半宽，不是已经达到的实际误差；接触采用脚邻近速度变化代理。原路返回落实为回到发球点附近，不是逐点反演轨迹。

下一步只读监控 `tail -n 120 /home/cao/perceptual_ball/logs/rsl_rl/agilekickball_v4/train_20261012.log`。不要重复启动。完成后用固定球速、固定 ±0.2m 门、完成轮次分母做回传评估；当前指标为训练分布，需区分课程半宽和固定门命中。若进程意外终止，只可使用同 v4 checkpoint 执行 `bash scripts/rsl_rl/train_agilekickball_v4.sh --resume --checkpoint <v4模型绝对路径>`；脚本自动去掉 warm-start。
