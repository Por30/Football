# Football结束后启动wall4：2026-10-13记录

用户已授权串行训练。后台等待进程已登记，但**wall4就绪检查仍阻塞，尚未武装正式训练启动**。不是“football结束后一定自动开训”。当前等待器会核验足球最终模型；随后因wall短测未通过而记录BLOCKED并退出，不会绕过验证启动长训。

- 等待器PID：2280644（注册时快照，查看实际进程确认）。
- [实时状态](../../../logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/status.json)、[注册配置与源码hash](../../../logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/config.json)、[后台日志](../../../logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/supervisor.log)。
- 足球PID2056902，原进程start_ticks=249758817；继续运行，未停止或重启。检查时约46700/50000，最终目标model_49999.pt，不是成功率评估。
- 预定wall4：128环境、seed42、40000轮，从头初始化。正式输出为logs/rsl_rl/g1_carrybox_depth/walled4/，不会使用任何smoke模型初始化。

## 本轮修复及验证

运动学wall/platform/cylinder现在仅写pose，避免PhysX禁止的线角速度写入；动态箱子和机器人仍写完整状态。相机安装扰动改为直接写相对torso的local pose，并显式从world相机朝向约定转为OpenGL约定，避免通过滞后的USD父世界变换反算安装位置。walled environment_contract迁移revision由1升为2，checkpoint主schema仍为2。

19项CPU测试通过，覆盖原CarryBox/AMP/walled合同，以及运动学API、PID复用、截断/错误迭代/非有限checkpoint、异常结束日志、资源不足、旧源码/旧就绪报告和重复启动锁。真实GPU短测在三技能初始化、相机local安装边界及墙柱可见性之后，完成第一次PPO更新；下一rollout仍报PhysX convexCoreConvexNphase / CUDA700。挂起进程由本轮工具仅终止自己的测试PID，回执exit137。正式football进程未受该操作影响。

CUDA_LAUNCH_BLOCKING=1诊断曾让wall3完成三轮，但wall4仍失败，不能当作已验证的训练解决方案。最终local-pose版本的标准wall3短测仍失败，wall4后续短测未执行。128环境预检未执行。

[冻结测试回执](test_receipts.json)：CPU PASS；GPU smoke FAIL；启动就绪检查FAIL。失败日志分别保存在pose_only_failure.log、blocking_wall3_pass.log、blocking_wall4_failure.log及walled3/smoke.log。本轮范围内修复次数用尽，停止继续试改，未删除碰撞、关闭RSI或降低验收条件。

## 等待器门控

等待器独立于交互会话，使用flock及原子JSON。足球身份绑定PID、启动ticks、boot ID、cwd、完整argv；原进程退出后须同时有最终49999/50000日志、稳定完整的model_49999.pt、正确v4 revision和有限模型/优化器张量，且无明确致命错误。仅有PID退出不算完成。

然后验证当前源代码/原始动作hash与注册一致、wall3/wall4三轮真实runner就绪报告匹配。通过后才会等待GPU资源，运行一次128环境、默认PPO与20秒episode的有界预检，并按实际显存峰值加余量门控长训。Popen前记录单次启动意图，失败不重启。当前缺少有效就绪报告，因此该后续路径不会执行。

只读查看：

```bash
cat logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/status.json
cat logs/rsl_rl/g1_carrybox_depth/walled4/after_football_20261013/registration.json
ps -p 2056902,2280644 -o pid,etime,args
```

后续需要新的定点GPU故障修复与验证。修好后须按新的源码hash和真实PASS报告重新注册队列，协调本轮等待器，不能手改状态伪造就绪；已有的训练授权不需要重复申请。参考[工程交接](../../../agent/handoff/carrybox-wall4-after-football.md)。
