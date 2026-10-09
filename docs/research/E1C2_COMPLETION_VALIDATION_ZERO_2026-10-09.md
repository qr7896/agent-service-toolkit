# 成功模型补丁的公开自身probe与边界零调用验证

日期：2026-10-09，独立身份 `completion-public-validation-zero-v1`。父付费trial实际1call/19,840tokens，完整JSON、模型生成非空生产patch，独立official F2P1/1/P2P37/37 resolved。一个看过旧DEV，不称30/30/独立泛化或完整语义证明。

先核验paid完整method/输入/生成seal与verified-result，再冻结wrapper源码/协议/旧probe/sweep源码与paid patch SHA。在新的own-probes/boundary子目录复用既有执行器，通过scoped参数接线，不改其源/原目录，不修改模型patch/probe/expectation。

同image/base/optional缺失条件，原control与target各两次；同21个公开派生时间变体在未改base/新模型patch/公开旧版各执行一批。宿主全只读挂载，patch仅写隔离容器层；network none/pull never，资源与90秒/子进程10秒上限保持。不读official断言/Gold，不调用模型，不借其他task版本witness。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_completion_validation_zero
```

只有完整有效运行才报告各阶段完成量与剩余反例；21是同旧DEV合成覆盖，完成不是返回值等价。module/path/version检查在phase driver，child继承同PYTHONPATH而非逐childattestation。原full_issue_trusted/namespace意图仍false，不借官方通过清除未知。started身份不重跑，失败保留并停，不开启canary/TEST/Fresh30/E2或改系统/代理/tunnel/密钥/下载删除。
