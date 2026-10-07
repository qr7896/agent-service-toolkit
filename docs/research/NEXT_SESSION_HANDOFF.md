# WebCodex 接手：E1-C evaluation_2

日期：2026-10-07。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新范围与静态export链](E1C2_REFERENCE_SCOPE_RESULTS_2026-10-07.md)。

## 1. 当前状态与禁止重跑

已实现条件引用范围检查与静态重导出链审计：四缓存3显式结构支持/1条件结构支持；两个条件引用链均有静态身份支持，但原资格v3仍2机制候选/1行为候选/1unknown，machine trusted0。新增provider/tokens0/0、Gold读取0，旧Gold4/4及异常对应3/4不改。新增23单测，最终1485 passed/4 skipped/33warnings（84.67秒），Ruff、重点38项与合成preflight过；工程数不是修复率。未完成运行时对象/公开意图对应或完整live方法冻结，不开canary/TEST/C5/Fresh30/private Test500/repair/E2。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

authority仅审计overlay，不改原模型输入。Foo/Schema/DateTime遗漏import的条件结构解释已实现，但没有接受为严格资格证书；两引用链的host LF/base Git已自动核验，运行时对象及公开意图仍未证明。范围审计原source snapshot等原freeze SHA，公开源仅import排序不同；原结果不重跑。

[最新公开收据](../../data/e1c_evaluation_2_reference_scope_results.json)绑定本轮结果与最终XML SHA；raw/probe/Gold/test/key留本机。所有已started audit/run/smoke/Gold禁止重跑、回填或修改旧source。

## 2. 当前唯一下一步

先将实际使用对象与自动派生的静态链对应，另版受限离线instrumentation协议，不手选文件/不改原probe/不用Gold调参；再校准显式请求、同输入API对照、带版本/依赖条件的回归行为义务。SK26289行为支持不叫原机制证明。范围/静态export审计已完成，禁止重复原namespace。

跨repo正负例通过后完整method含资格/observer/双source身份先冻，再同版四参考/九准入DEV/native，Gold/受限候选/语义/原机制分账。可信gate真正达成才历史全排除新canary一次≥2/3、Agent patch/official、小DEV30及最后另授权Fresh30。当前无新paid/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_qualification.py evals/e1c_evaluation_2_qualification_v2.py evals/e1c_evaluation_2_qualification_v3.py tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py tests/test_e1c_evaluation_2_qualification_v3.py evals/e1c_evaluation_2_reference_scope.py evals/e1c_evaluation_2_export_chain.py tests/test_e1c_evaluation_2_reference_scope.py tests/test_e1c_evaluation_2_export_chain.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py tests/test_e1c_evaluation_2_qualification_v3.py tests/test_e1c_evaluation_2_reference_scope.py tests/test_e1c_evaluation_2_export_chain.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

无需DeepSeek/tunnel密钥，合成preflight不是sealed TEST实验。依赖安装失败报环境阻塞，不降低断言/timeout/skip；源码与uv.lock可云端运行，本机exact-base/private .codex/镜像/runtime不随Git同步，缺材料报INFRA_BLOCKED。旧bridge白名单未扩、不假称新paid端到端已验、不开放裸Docker daemon、不上传key/raw/Gold。

## 4. 付费、安全与回传

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后独立Gold；原v2/expectation-v1/report-anchor-v1和两个observer namespace都不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
