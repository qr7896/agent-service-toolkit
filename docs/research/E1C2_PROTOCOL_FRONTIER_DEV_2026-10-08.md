# E1C2：正常对照绑定保护与检索停滞修订

## Material Passport

- 日期：2026-10-08；状态：预注册；类型：旧 DEV 两来源的小额方法迭代，不是独立测试。
- 前一阶段：5 次 Flash 调用共20,914 tokens；一条真实 Python probe进入容器，但 source-backed rephase 使正常对照引用未定义 receiver；另一条重复生产检索后停止。0候选/0机器可信，不把格式进步当任务通过。
- 通用修订：真实执行前调用原 source-backed frontier 推导，仅检查被移出公共setup的直接绑定是否被正常control读取；遇到明确缺失即拒绝，反馈要求模型使用源码支持的独立normal receiver。不补写/猜测对象，不放宽生产API/Oracle/行为资格，不改旧编译器或旧结果。复杂控制流只保守拒绝/未知，不称任意Python静态证明。
- 策略说明：两阶段分别执行、setup在两阶段执行；缺陷配置在target；显式禁止在成功检索后重复同query，已有窗口优先用于probe。不是IID规则或人工选文件。

## 命令与预算

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_protocol_guard_dev freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_protocol_guard_dev run
```

`deepseek-flash`、thinking disabled；最多6请求/每题3，总40,000 provider tokens/单题24,000/output2,000/input estimated hard24k/reserve1.4/retry0。使用原已seal生产检索输入，2个旧DEV来源不扩四参考/九准入。新namespace `action-protocol-frontier-flash-dev-v1`，原试验5,997与20,914单列，不清零/合并成成功率。运行前列明精确命令，用户既有每实验≤100k委托范围内执行。API失败不自动重试，不恢复已started namespace。

生成侧只公开issue/生产源/自身运行反馈，无原测试/答案/Gold。无网络容器；无镜像下载或系统变更。只有正常control×2、重复target失败、Controller语义资格实际成立才产生候选；仅有效Python、有限假设、Gold消除均不能升级完整issue证明。本阶段不运行Gold或Agent修复，不打开canary/C5/TEST/Fresh30/E2。若仍失败，封存并按真实原因修通用方法；不承诺30/30完美。
