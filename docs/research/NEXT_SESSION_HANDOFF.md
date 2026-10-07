# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-07。仓库qr7896/agent-service-toolkit。先读[AGENTS.md](../../AGENTS.md)、[当前Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新结果](E1C2_EXPECTATION_RESULTS_2026-10-07.md)。

## 1. 最新状态：期待门槛版3/4，不要重跑

expectation-reference-dev-v1：9 Flash请求30,477tokens、retry0，producer completed/seal后独立Gold attempted3/区分3，machine0；另一项期待被拒后弃答。本版未保留前版execution-plan-v2的4/4，原记录/分数不改，不best-of；成本也未改善。固定12/九准入/screen4，不是完整DEV/独立/Agent修复或30题成绩。

期待角色已在oracle lock前筛查；公开A/B语法、source/import绑定、共享表达式/literal约束与执行后grounding已接线，但复杂/未知语义不获证。原公共Human输入四项逐字不变。两轮错误期待反馈contrast=null，原文并没删，尚不能确定加反馈会恢复。

Controller仅在独立zero诊断派生public normal A，用原缓存自有argument，未知额外参数/影射/source不绑定则拒。两份缓存派生出同一program，各两次normal通过：1旧task/1program/4次运行、模型0/Gold读取0；不是Agent程序、不补到3/4、不表示B应具备A所有能力。main paid未接该派生器。

最终1419 passed/4 skipped/33warnings（113.65秒）、Ruff/预算V3/compact preflight过。代码先提交9648a4f再freeze/live；[收据](../../data/e1c_evaluation_2_expectation_results.json)绑定SHA，raw/probe/Gold/test/key不上传。全部旧/新smoke/freeze/run/Gold/audit已started或封存，禁止重跑/回填，当前无下载需求。

## 2. 当前唯一下一步

先零调用区分明确接口请求、公开回归报告、公开比较报告、unknown。trace/code不当desired behavior，literal期待不捏造。若用A工作/B失败推断B也应完成，先预注册inferred_from_public_comparative_report及源码scope/反例，不称原文明确承诺，不暗改本轮严格口径追回4/4。

将已识别公共prose锚与A/B关系结构化附回拒绝反馈，仍由模型生成真实对照。诊断派生normal只作feasibility，不冒充模型；报告alias/实际共享值/原报机制分别未知，source绑定不自动trusted。先跨仓库正负例与工程门槛，再另冻一次四参考，Gold/语义分账。

两gate过后才完整九准入/有限native，新全历史排除canary可信≥2/3、Agent patch/独立official grade、旧DEV30，最后另授权Fresh30。当前不抽第6canary、不开始repair/E2、不再追加paid采样。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_expectation_dev.py evals/e1c_evaluation_2_public_normal_diagnostic.py tests/test_e1c_evaluation_2_expectation_dev.py tests/test_e1c_evaluation_2_public_normal_diagnostic.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_expectation_dev.py tests/test_e1c_evaluation_2_public_normal_diagnostic.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

无需DeepSeek/tunnel密钥，合成preflight不是sealed TEST实验。依赖安装失败报环境阻塞，不降低断言/timeout/skip；源码与uv.lock可云端运行，本机exact-base/private .codex/镜像/runtime不随Git同步，缺材料报INFRA_BLOCKED。旧bridge白名单未扩、不假称新paid端到端已验、不开放裸Docker daemon、不上传key/raw/Gold。

## 4. 付费、安全与回传

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后独立Gold；原v2/expectation-v1都不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
