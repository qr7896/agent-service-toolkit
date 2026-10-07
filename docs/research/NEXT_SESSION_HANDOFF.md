# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-07。仓库qr7896/agent-service-toolkit。先读[AGENTS.md](../../AGENTS.md)、[当前Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[本轮新结果](E1C2_EXECUTION_PLAN_RESULTS_2026-10-07.md)。

## 1. 最新结果与接线更正

execution-plan-reference-dev-v2：4 Flash请求11,909tokens、retry0，独立Gold attempted4/区分4，机器trusted0。不是完整DEV12/独立成绩/Agent修复。四题API/uncertainty/plan真实产物4/4，代码先提交0c986a5再freeze/run/seal/Gold。

根因是runner内部compiled.configured覆盖外层loop executor。旧obligation/observed/codec付费组件生效解释不成立，原3/4、2/4、2/4分数仍保持。v2在compiled所有者也绑定完整delegate链，inner context和异常恢复有回归。旧五probe零费实际链5/5和1自身类型观测证明接线，不叫新模型生成。

最终1402 passed/4 skipped/33 warnings（60.81秒），Ruff/预算V3/compact preflight ready=true。当前不需要下载。所有旧/v1/v2已started的smoke/freeze/run/Gold/audit禁止重跑或改写；public[data收据](../../data/e1c_evaluation_2_execution_plan_results.json)绑定哈希，raw/Gold/test/key不上传。

## 2. 下一步：期待与行为的质量门槛

witness_grounding_audit全4零费审计：1项期待引用是trace，且数组实际在参数校验失败，未观察到公开guard报错点。其余3项是未分类待语义证据，不是自动通过。因此只有Gold数值gate过，不开第6canary/repair/E2/Fresh30。

先将期待角色检查接在oracle lock前：trace/code-only不能当desired behavior，要求公开自然语言或明确API义务依据，unknown保留，不捏造期待。然后把source-bound生产调用链与自己两次实际trace对应，分别标“API义务候选／原报故障机制未证”；位置不同不自动判无关，Gold消除不自动trusted。

跨仓库有效/错误期待、正常/故障control、共享setup、类型冲突与未知入口正负例验收，再另冻一次同四参考，Gold和语义分账；两gate真过才完整九准入/有限native覆盖，新不重叠canary可信≥2/3、Agent patch/official grade、旧DEV30，最后另授权Fresh30 one-shot。不要再只追加提示或增加预算采样。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_execution_plan_dev.py evals/e1c_evaluation_2_execution_plan_dev_v2.py evals/e1c_evaluation_2_witness_grounding_audit.py tests/test_e1c_evaluation_2_execution_plan_dev.py tests/test_e1c_evaluation_2_execution_plan_dev_v2.py tests/test_e1c_evaluation_2_witness_grounding_audit.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_execution_plan_dev.py tests/test_e1c_evaluation_2_execution_plan_dev_v2.py tests/test_e1c_evaluation_2_witness_grounding_audit.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

无需DeepSeek/tunnel密钥，合成preflight不是sealed TEST实验。依赖安装失败报环境阻塞，不降低断言/timeout/skip；源码与uv.lock可云端运行，本机exact-base/private .codex/镜像/runtime不随Git同步，缺材料报INFRA_BLOCKED。旧bridge白名单未扩、不假称新paid端到端已验、不开放裸Docker daemon、不上传key/raw/Gold。

## 4. 付费、安全与回传

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后独立Gold；原v2不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
