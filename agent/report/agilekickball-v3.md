---
task_id: "AGILE-V3-20260927"
language: "zh-CN"
axes: ["L"]
risk_tier: "T2"
status: "DONE"
changed_files: ["README.md", "agent/handoff/agilekickball-v3.md", "agent/plan/agilekickball-v3.md", "agent/report/agilekickball-v3.md", "agent/task/agilekickball-v3.md", "docs/agilekickball_v3/README.md", "docs/agilekickball_v3/validation/artifacts.json", "docs/agilekickball_v3/validation/receipts.json", "docs/agilekickball_v3/validation/receipts_attempt1.json", "docs/agilekickball_v3/validation/smoke.json", "docs/agilekickball_v3/validation/smoke.log", "docs/agilekickball_v3/validation/smoke_attempt1.log", "scripts/rsl_rl/smoke_agilekickball_v3.py", "scripts/rsl_rl/smoke_agilekickball_v3.sh", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/__init__.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/agilekickball_v3_env_cfg.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/agilekickball_v3.py", "source/perceptual_ball/perceptual_ball/tasks/manager_based/perceptual_ball/mdp/kickball_state.py", "tests/test_agilekickball_v3.py"]
task_contract_sha256: "26f97379400e0f1a87ee96161ed9bffd3ac4a0f699631cb760eabc8a3f90cbb3"
tests: [{"command": "/home/cao/ENTER/envs/ball/bin/python -m unittest discover -s tests -p test_agilekickball_v3.py", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "2c2cdedcfd922b65a901ff9fbcdfea89ab151033175e669e47945355a8beed98", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "6399d6aa8e467d2095f39bdb5a078403bfac244631e91c94f13f08ff8eb826bc", "runner": "run_engineering_tests.py"}, {"command": "bash scripts/rsl_rl/smoke_agilekickball_v3.sh", "result": "PASS", "exit_code": 0, "executed": true, "receipt_sha256": "1d62a83bc8ed2afddb0ddf08e9ab2de07b15492cd74d08f81223147e2124831e", "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "runner": "run_engineering_tests.py"}]
artifact: "REPORT"
---

新增独立Template-Perceptual-Ball-AgileKickball-v3，revision=wide_serve_20260927。继承v2速度课程、奖励、恢复、观测与PPO，只调空间参数组：随60000平均来球曝光，发球距离0.5–0.7→1.3–3m，横向目标偏移±0.25→±0.75m；机器人离锚点终止半径0.6→1.2m，球离锚点结束半径3→4m。anchor保持episode初始站位，发球角度±0.35rad。共享代码仅将两项常量改为可选实例属性，旧任务默认值不变。

冻结回归和真实CPU16环境短测均PASS。覆盖v3/v2/v1课程、部分reset、旋转/平移下发球几何、3m发球不会立即结束、4m球边界、1.2m移动边界、旧checkpoint权重加载前拒绝、play冻结与续训恢复。真实仿真完成2次新策略PPO/辅助/AMP更新，全部loss有限，并验证3m、6m/s发球首步有效。环境和runner配置比对确认除startup、移动终止和实验名称外沿用v2；git diff --check通过。

首次短测在同一runner完成推理再切回续训时遇到inference normalizer tensor原地写入错误。验证脚本改为正常进程恢复方式：新建runner后加载optimizer与课程，重跑通过；未改变训练算法或放宽断言，首次失败日志及receipt保留。

实现完成，未启动长训练。v3独立checkpoint键并用config记录空间版本；默认从零训练，v2 checkpoint不能直接resume。短测不证明策略已学会宽范围高速接球。站立奖励和后方0.3m球结束规则仍沿用v2，机器人允许移动更远但仍有回位软激励。完整参数和启动命令见docs/agilekickball_v3/README.md。
