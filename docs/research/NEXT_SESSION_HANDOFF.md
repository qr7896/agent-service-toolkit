# WebCodex 接手：E1-C evaluation_2

日期：2026-10-07。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新paired输入与规格](E1C2_PAIR_INPUT_CONTRACT_RESULTS_2026-10-07.md)。

## 1. 当前状态与禁止重跑

公共API对照的调用前诊断完成：normal rc0/target rc1，feature_names(ndarray)与max_depth(int)两路typed摘要一致，但分类器对象unknown，all_inputs_match=false。生产参数文档两API均仅明确写list of str，因此ndarray期待存在规格支持缺口，不等于输入非法或任务不是bug。新增provider/tokens0/0、Gold读取0，原probe与旧Gold4/4/资格2机制候选+1行为候选+1unknown保持，machine trusted0。 本轮2新离线诊断容器，非新模型/评分成绩；不开canary/TEST/Fresh30/repair/E2。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

authority/scope/export仅审计，不改原模型输入。对象observer v1整体unknown且未执行容器，v2以模块全部有界构造器候选记录实际关系，不按with_metaclass猜继承。5条真实记录含2条不对应记录全部保留，DateTime exact与Schema MRO关系出现；runtime关系不证明公开意图，不清除旧严格unknown。两个namespace均完成，不重跑。

[最新公开收据](../../data/e1c_evaluation_2_pair_input_contract_results.json)绑定本轮结果与最终XML SHA；raw/probe/Gold/test/key留本机。所有已started audit/run/smoke/Gold禁止重跑、回填或修改旧source。

## 2. 当前唯一下一步

最终Ruff/预算V3重点36项/合成preflight通过，完整1519 passed/4 skipped/33warnings（105.28秒），XML SHA在收据，不报repair rate。

先冻结有限行为资格分支与正负例：显式公共变更请求可覆盖base docs、已有生产文档承诺、比较/回归报告的条件假设分账。source参数事实只取Parameters、不序列化Examples/断言，未来新输入另freeze，不回填原模型。不要先扩展任意对象序列化；只有明确契约需训练状态等证据时再另版加受限投影。scope/export/object/pair-input/parameter-contract诊断全已完成，不重跑。

跨repo正负例通过后完整method含资格/observer/双source身份先冻，再同版四参考/九准入DEV/native，Gold/受限候选/语义/原机制分账。可信gate真正达成才历史全排除新canary一次≥2/3、Agent patch/official、小DEV30及最后另授权Fresh30。当前无新paid/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_qualification.py evals/e1c_evaluation_2_qualification_v2.py evals/e1c_evaluation_2_qualification_v3.py tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py tests/test_e1c_evaluation_2_qualification_v3.py evals/e1c_evaluation_2_reference_scope.py evals/e1c_evaluation_2_export_chain.py tests/test_e1c_evaluation_2_reference_scope.py tests/test_e1c_evaluation_2_export_chain.py evals/e1c_evaluation_2_object_observer.py evals/e1c_evaluation_2_object_observer_v2.py tests/test_e1c_evaluation_2_object_observer.py tests/test_e1c_evaluation_2_object_observer_v2.py evals/e1c_evaluation_2_pair_input_observer.py evals/e1c_evaluation_2_parameter_contract.py tests/test_e1c_evaluation_2_pair_input_observer.py tests/test_e1c_evaluation_2_parameter_contract.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py tests/test_e1c_evaluation_2_qualification_v3.py tests/test_e1c_evaluation_2_reference_scope.py tests/test_e1c_evaluation_2_export_chain.py tests/test_e1c_evaluation_2_object_observer.py tests/test_e1c_evaluation_2_object_observer_v2.py tests/test_e1c_evaluation_2_pair_input_observer.py tests/test_e1c_evaluation_2_parameter_contract.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

无需DeepSeek/tunnel密钥，合成preflight不是sealed TEST实验。依赖安装失败报环境阻塞，不降低断言/timeout/skip；源码与uv.lock可云端运行，本机exact-base/private .codex/镜像/runtime不随Git同步，缺材料报INFRA_BLOCKED。旧bridge白名单未扩、不假称新paid端到端已验、不开放裸Docker daemon、不上传key/raw/Gold。

## 4. 付费、安全与回传

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后独立Gold；原v2/expectation-v1/report-anchor-v1和两个observer namespace都不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
