# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-07。仓库qr7896/agent-service-toolkit。先读[AGENTS.md](../../AGENTS.md)、[当前Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新结果](E1C2_REPORT_ANCHOR_RESULTS_2026-10-07.md)。

## 1. 最新状态与禁止重跑

report-anchor-reference-dev-v1：6 Flash请求21,400tokens、retry0，producer completed/seal后独立Gold4/4；公共A/B真实正常-目标对照已做，期待是精确prose锚的明确请求或推断完成假设。不是前版严格口径的4/4，不回填原3/4/旧4/4、不best-of。固定12/九准入/screen4分账，machine0、无Agent patch/official resolved。

零模型exception-observation-zero-v2在3/4取得公共异常/缺失keyword对应，另一项未见原报机制，只支持API行为差异。observer只处理精确builtin异常及字符串参数、两production文件/八记录，输出匹配SHA/位置，不输出原始消息/值，不赋予语义trust。

v1在模型probe前source SHA核验失败，失败完整留档未retry；只读确认CRLF host副本/LF container差别，容器等Git base blob。v2原暴露SHA+LF投影+容器有效文件/Git canonical blob双身份，原文件不改、实际非换行差异仍拒；适配旧Python并保留缺dateutil blocker。观察改变filename/timing，不证明全语义等价，也不是对抗任意恶意程序的attestation。

最终1436 passed/4 skipped/33warnings（104.66秒），Ruff/预算V3/compact preflight过；paid代码先commit e220a87。所有旧/新smoke/freeze/run/Gold/audit已started或封存，禁止重跑/修改；[收据](../../data/e1c_evaluation_2_report_anchor_results.json)绑定SHA，raw/probe/Gold/test/key不上传。无下载需求。

## 2. 唯一下一步：受限语义资格校准

先零模型合并公共输入约束、production调用与alias、期待来源、真实异常对应；明确支持的证书scope与unknown，不把3/4对应叫可信率。反例需覆盖：同消息wrong fixture、alias shadow、生产对象改写、shape/参数偏离、仅API兼容而原报机制未证、源码/环境变动。三种类型不能互换：明确公开请求、比较/回归的推断完成假设、未知。

校准跨repo后将observer/双身份/classifier完整冻入新方法，做一次同版四参考/九准入DEV（固定12分母）；受限行为和原报机制分账。可信gate真正过才全历史排除新canary预注册一次≥2/3、Agent patch/独立official、小DEV30，最后另授权Fresh30。当前不抽第6canary、不做repair/E2、不追加paid采样，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_report_anchor_dev.py evals/e1c_evaluation_2_exception_observer.py evals/e1c_evaluation_2_exception_observer_v2.py tests/test_e1c_evaluation_2_report_anchor_dev.py tests/test_e1c_evaluation_2_exception_observer.py tests/test_e1c_evaluation_2_exception_observer_v2.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_report_anchor_dev.py tests/test_e1c_evaluation_2_exception_observer.py tests/test_e1c_evaluation_2_exception_observer_v2.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

无需DeepSeek/tunnel密钥，合成preflight不是sealed TEST实验。依赖安装失败报环境阻塞，不降低断言/timeout/skip；源码与uv.lock可云端运行，本机exact-base/private .codex/镜像/runtime不随Git同步，缺材料报INFRA_BLOCKED。旧bridge白名单未扩、不假称新paid端到端已验、不开放裸Docker daemon、不上传key/raw/Gold。

## 4. 付费、安全与回传

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后独立Gold；原v2/expectation-v1/report-anchor-v1和两个observer namespace都不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
