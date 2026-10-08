# 保留模型补丁的公开自身probe零调用诊断

日期：2026-10-08；身份 `three-arm-public-patch-probe-zero-v1`。仅支持上一后验解码诊断中唯一非空候选。先核验原producer seal、后验转译seal/patch SHA和原方法；不编辑原补丁、原probe或旧结果。

新目录冻结源码/协议、候选patch、原normal/target probe以及依赖阻断器。四次在同镜像/base、相同原optional缺失条件运行：正常两次、目标两次；每次先原base身份检查，再`git apply --check/apply`模型补丁，运行完全相同的公开issue派生probe。容器临时层可写以施加补丁，但所有宿主挂载只读、无网络/no-pull、cap-drop/资源限制保持；无评分材料挂载/读取、无Gold、无provider。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_patch_probe_zero
```

每次90秒上限，超时保留诊断并停止，不自动retry。结果回答“模型补丁能否让原自身probe通过”，不回答全部公开义务或官方测试正确性。即使自身probe通过但official失败，必须报告覆盖缺口，不按评分断言人工补规则，不把局部症状完成当完整修复。若自身probe也失败，则下一轮应加入公开probe失败trace驱动的自动补源/自验证闭环；还须新method/预算freeze与精确付费授权。当前不开canary/TEST/Fresh30/E2，不改系统或删除数据。
