# E1C2：真实环境反馈与公开接口请求，双来源DEV预注册

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；Origin Mode: run。
- 日期：2026-10-08；类型：旧DEV方法迭代，非独立canary；状态：预注册。
- 只使用公开issue、exact-base生产源码、自身offline反馈。旧两来源按固定library顺序、不人工选文件；沿用父sealed production检索输入，不复用评分。
- 问题：把实际强制optional import条件送到下一Human，并澄清公开新增参数请求可以在base失败，能否降低无依据弃权？完整fixture资格不因该反馈升级。

## 精确命令、预算与停止

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_environment_dev freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_environment_dev run
```

`deepseek-flash`（不Pro）、thinking disabled，最多6calls/每题3，总40,000 provider tokens/单题24,000/output2,000/input estimated hard24k/reserve1.4/retry0。共同上限约束、不增加旧账本预算；用户既有单实验≤100k委托，paid前列精确命令。HTTP失败不自动重试，已started namespace不再run；普通agent后续反馈动作不是API失败重试。

新namespace `environment-feedback-flash-dev-v1`；父三阶段费用13/53708单列不重置、不拼分。预检先核对父source/seal及实际旧环境probe，重建实际内层消息验证信息存在；不执行旧probe、不读Gold、不改父输入。40k不是承诺花完，真门槛不足不扩四参考/九准入。

环境投影要求control1/control2/target schema/input/image/base/module一致，network_none/pull_never、非timeout有效运行。记录事实只表明执行器强制导入失败，不称自然卸载/实际guard值/语义证明。缺条件或错记录不提升资格。source-backed normal绑定守卫、锁定quote/Oracle、未知不terminal规则保留。

公开明确请求的新增参数可成为target失败入口；normal用源支持的独立receiver，缺陷构造不放shared setup，不编造API/公共值、期待、不把keyword接受叫default或增量功能。无task-ID特例、无原测试断言、模型不看Gold。容器无网络/只读，无下载或系统修改。

新生成封存后，仅有有限候选才可单独零模型Gold消除检验（`... environment_dev gold`），不把Gold消除授予语义/Agent修复。canary/C5/TEST/Fresh30/privateTest500/repair/E2关闭；真实DEV语义门槛成立再冻结新不重叠canary，不保证完美/30题全过。
