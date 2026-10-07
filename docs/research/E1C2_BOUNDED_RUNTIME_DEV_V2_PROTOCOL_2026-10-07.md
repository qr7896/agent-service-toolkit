# 受限运行反馈旧DEV v2：仅修typed动作兼容，不改旧结果

**后续核验修正：** 实际12份回复的type值是固定`json_object`格式标记，不是retrieve/probe动作名。本版codec因此尚未兼容这些回复；只完成合成/真实零调用smoke，没有budget freeze/run/评分。保留本版方法与smoke，不作为live入口；正确格式归一化另立[v3](E1C2_BOUNDED_RUNTIME_DEV_V3_PROTOCOL_2026-10-07.md)。下文是最初typed-action假设，不能视为已解决格式问题。

继承[完整v1方法](E1C2_BOUNDED_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md)的source-only/无网络/两次控制/oracle锁定/selection-before-grader与所有关闭门槛。v1已完成12请求24976tokens，全部raw JSON含明确type标记，canonical单键parser拒绝；三题turn_limit、candidate0、grader attempted0，原freeze/state/ledger/全部响应保持不变。不是3个软件任务失败，也不是input echo。

新增codec只允许两种严格等义typed形态：`{"type":"retrieve","retrieve":"Owner.method"}`（read/abstain_reason同理）；`{"type":"probe",七个原B字段}`归一为`{"probe":原七字段}`。type与fields必须一致、无额外字段；shell/echo/额外execution/缺字段/路径绕过仍拒绝，原字符串/源码/quote/oracle/assertion一字不改。不按task ID补规则，不接受错误schema中的代码拼接。

新namespace `bounded-runtime-dev-v2`与`bounded-runtime-zero-smoke-v2`。方法/实际invoke双冻结预算：Flash、最多12请求/每题4、整批60000/每题20000/输出2000、temp0/nonthinking/retry0；source/input/prompt/三题选择规则不变，预算降低，不把v1调用重试或回填成v2。先codec单测及原工程重点、真实跨两仓库零调用smoke→新method/预算freeze→展示唯一精确run，再使用用户单实验≤100000授权边界。v1费用单列，新轮费用单列，不合并best-of。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v2 smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v2 preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v2 run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v2 gold
```

各one-shot入口已经开始就不能自动重跑。真provider异常停，预算耗尽按固定分母保留budget_stop；重复检索无信息增益停。三题screen仍不是全DEV12、独立canary或修复成绩；语义审查/四参考/全旧DEV仍必须另验。新版codec让controller支持模型自然产出的严格typed动作，不能据此声称复现质量提升。首轮异常和新轮所有negative保留，TEST/C5/Fresh30/repair/E2关闭。
