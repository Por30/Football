# 2026-10-08 诊断与修复证据索引

- `comparison.json` / `scalars.npz` / `training_audit.png`：已完成 v2 与失败 v3 的训练日志审计，episode 原始单位为步。
- `config_differences.json`：实际保存的物理任务配置没有漂移。
- `replay.json`：失败策略、残差关闭和确定性/采样动作的同条件回放。
- `probe.json`：实际状态中的方差截断、梯度和动作 KL 探针；非单因素因果证明。
- `diagnosis.json`：已确认机制、修复和结论边界。
- `receipts.json`：三个冻结检查最终 PASS，前两次失败记录另外保留。
- `smoke.json`：v2 输出/AMP 精确迁移、更新/续训和真实恢复，16 环境 1000 步恢复数为 98、92。
- `scale_smoke.json`：4096 环境 100 次 PPO 更新，24 步、5 epoch、4 minibatch；末轮 episode 1508.17 步约 30.16 s。
- `replay_repaired.json`：修复后 100 轮模型的同条件回放。
- `launch.json` / `verified_start.json`：新的正式后台训练启动和实际运行核验。
- `source_snapshot_manifest.json` / `source_snapshot/`：本轮源码及 SHA256。

新训练使用 v2 预训练权重，不能与 v2 scratch 作为相同初始化预算的论文比较。短测和启动核验只说明恢复能力在检查窗口内存在，不证明 50000 轮长期收敛或创新收益。
