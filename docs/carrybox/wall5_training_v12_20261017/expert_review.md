# 有界专家复核

一个E/P/L/C组合轴只读专家核对真实13段数据、本地PhysHSI G1源码及当前IsaacLab数据/写入接口。未修改代码或扩展任务。

- 五末端link顺序、root-relative/world-aligned语义、base_height与ankle_pitch的定义完成独立URDF FK核对；记录掌/头最大约3.86mm源数据细差。
- 指出原PT Euler角差分不是正确的角速度，改用已有四元数最短弧差分；root rot6使用x/z列。
- Normalizer只更新原始expert/policy，不能复制源训练器“归一化后再次更新统计”的反馈错误。
- 实现复核发现初始化仍以COM速度写入并替换z，初版直接状态注入测试没覆盖该路径。主实现已增加wall5-only link速度选项，并补真实initialize_reference速度对照：walk_forward第80帧误差约1.19e-7m/s、pickup03第31帧约4.47e-8m/s。
- 未发现Normalizer/归一化坐标梯度罚/paired mask/shared默认路径的其他阻断问题；最终状态以新smoke.json与receipts为准。

仅4环境工程验收；无长期训练因果或收敛结论。接触probe只证明传感器有效，末端残差必须单列，不宣称全骨架完全一致。
