# L+A 只读组合审查

前两次请求因模型容量不足未执行；第三次由`/root/wall5_asymmetric_review`完成，只读审查，无文件写入。

affected_call_path:
  - Wall5ObservationsCfg → critic_state → 独立critic → PPO rollout/returns/训练快路
  - Wall5._reset_idx → 父类terminal/physics reset → timeout bootstrap
  - schema2/revision14 checkpoint；DepthPolicyExport只复制actor与CNN
critical_interfaces:
  - critic108 = 当前本体93 + pelvis link线速度3 + 箱子局部xyz3 + 旋转前两列6 + 完整尺寸3
  - actor372与depth[4,27,48]；critic[108,512,256,256,1]
  - terminal critic在reset前clone，env_ids顺序一致；timeout只加一次gamma*V
invariants:
  - actor/export不读取特权；value loss不进入CNN/actor/pose head
  - actor与辅助头保留单次CNN；其他CarryBox/football接口不变
  - AMP、RSI、奖励、PPO超参与单位/坐标系保持
smallest_change_locus:
  - 三个wall5生产文件已覆盖；不需要改共享train/play/export
mandatory_safeguards:
  - 停止前核对PID3812053身份，只停目标，保留模型日志，确认资源释放
  - 独立4096 fresh正式run，不resume/warm-start或加载验证模型，不失败自动重启
  - 核验新命令/配置/连续迭代/耗时/schema2/revision14/critic108/有限参数及优化器更新
  - 项目约定仅wall5 critic例外，短测和启动不代表收敛
minimal_tests:
  - 31项CPU已审阅PASS：坐标、输入/梯度隔离、partial reset/timeout/PPO/AMP/恢复/旧契约拒绝
  - 4环境2+1轮短测已审阅PASS：强制timeout、pre-reset、恢复、JIT/ONNX导出、wall4隔离
  - 主实现继续执行冻结verify_launch，检查首checkpoint优化器step与AMP Normalizer count符合fresh
blockers: []
