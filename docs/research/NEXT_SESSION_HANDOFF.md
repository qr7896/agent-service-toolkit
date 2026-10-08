# WebCodex 接手：E1-C evaluation_2

日期：2026-10-08。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新自动补证/context与协议结果](E1C2_ACQUISITION_RESULTS_2026-10-08.md)。

## 1. 当前状态与禁止重跑

新80k批已经completed/seal/gold，16Flashcalls/53212tokens、无budget stop、0candidate/0Gold attempted/machine0；1turn_limit/3abstained因复制setup说明和closed wrapper不支持。旧resume1复用候选结果不拼分。自动source取得/next Human已以cached-delegate实际零调用验证；有效probe未在live触发，所以不声称live补证成功。禁止run/gold任何已封存namespace，不开canary/TEST/Fresh30/repair/E2。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

authority/scope/export仅审计，不改原模型输入。对象observer v1整体unknown且未执行容器，v2以模块全部有界构造器候选记录实际关系，不按with_metaclass猜继承。5条真实记录含2条不对应记录全部保留，DateTime exact与Schema MRO关系出现；runtime关系不证明公开意图，不清除旧严格unknown。两个namespace均完成，不重跑。

[最新公开收据](../../data/e1c_evaluation_2_acquisition_results.json)绑定结果与最终XML SHA，所有更早receipt/负记录保留。原201/109/255及new54产物与冻结method SHA保持。raw/probe/Gold/key本机。不得重跑acquisition-context-zero-v1（missing compiler失败）、zero-resume/paid/gold/action-protocol check或任何更早started namespace。

## 2. 当前唯一下一步

最终Ruff/预算V3/新专项重点40项/合成compact preflight通过，完整1636 passed/4 skipped/33warnings（81.43秒），先前1629等XML保留，不报repair rate。

当前唯一下一步是把action_protocol.policy()/decode()整体接新producer（新source/namespace），先验证实际最终system不含可复制code值/消息包含真实issue/source、actual parse_action调用新decode，而不是旁路check。精确closed type/json_object+action/dict只transport层，原7字段/ref/Oracle不改；ast.parse拒绝说明文字，坏代码不自行修写。

自动Source import匹配/overlay+compact messages在acquisition_context.py，scope/projection/report的inner owner都已防覆盖，输入不mutate，schema获取未知不认证，cap2symbol/issue+base、1MB/source、host/LF/base/SHA一致。新预算input软12k/estimated硬24k/output2k/task软32k-hard48k/batch80k/max16/retry0和未来首请求预留；源/策略/context/预算多个因素不是单因果比较。新试验先完整freeze/精确命令，不覆写旧50k/80k账本，不在当前namespace重试。

之后按真实缺证处理production依赖/fixture作用域/paired receiver/公开期待与剩余义务，另版完整freeze→完整九准入DEV/native分账。可信gate真达成才历史全排除新canary一次≥2/3、Agent patch/official、DEV30/另授权Fresh30。当前无resume/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_acquisition_context.py evals/e1c_evaluation_2_acquisition_check.py evals/e1c_evaluation_2_acquisition_check_resume.py evals/e1c_evaluation_2_acquisition_dev.py evals/e1c_evaluation_2_action_protocol.py tests/test_e1c_evaluation_2_acquisition_context.py tests/test_e1c_evaluation_2_acquisition_check_resume.py tests/test_e1c_evaluation_2_acquisition_dev.py tests/test_e1c_evaluation_2_action_protocol.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_acquisition_context.py tests/test_e1c_evaluation_2_acquisition_check_resume.py tests/test_e1c_evaluation_2_acquisition_dev.py tests/test_e1c_evaluation_2_action_protocol.py
uv run --frozen python -m ruff check evals/e1c_evaluation_2_scoped_resume.py evals/e1c_evaluation_2_dependency_feedback.py tests/test_e1c_evaluation_2_scoped_resume.py tests/test_e1c_evaluation_2_dependency_feedback.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_scoped_resume.py tests/test_e1c_evaluation_2_dependency_feedback.py
uv run --frozen python -m ruff check evals/e1c_evaluation_2_scoped_controller.py evals/e1c_evaluation_2_scoped_dev_trial.py evals/e1c_evaluation_2_feedback_projection.py tests/test_e1c_evaluation_2_scoped_controller.py tests/test_e1c_evaluation_2_scoped_dev_trial.py tests/test_e1c_evaluation_2_feedback_projection.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_scoped_controller.py tests/test_e1c_evaluation_2_scoped_dev_trial.py tests/test_e1c_evaluation_2_feedback_projection.py
uv run --frozen python -m ruff check evals/e1c_evaluation_2_qualified_controller.py tests/test_e1c_evaluation_2_qualified_controller.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_qualified_controller.py
uv run --frozen python -m ruff check evals/e1c_evaluation_2_controller_failure_smoke.py tests/test_e1c_evaluation_2_controller_failure_smoke.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_controller_failure_smoke.py
uv run --frozen python -m ruff check evals/e1c_evaluation_2_qualification.py evals/e1c_evaluation_2_qualification_v2.py evals/e1c_evaluation_2_qualification_v3.py tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py tests/test_e1c_evaluation_2_qualification_v3.py evals/e1c_evaluation_2_reference_scope.py evals/e1c_evaluation_2_export_chain.py tests/test_e1c_evaluation_2_reference_scope.py tests/test_e1c_evaluation_2_export_chain.py evals/e1c_evaluation_2_object_observer.py evals/e1c_evaluation_2_object_observer_v2.py tests/test_e1c_evaluation_2_object_observer.py tests/test_e1c_evaluation_2_object_observer_v2.py evals/e1c_evaluation_2_pair_input_observer.py evals/e1c_evaluation_2_parameter_contract.py tests/test_e1c_evaluation_2_pair_input_observer.py tests/test_e1c_evaluation_2_parameter_contract.py evals/e1c_evaluation_2_behavior_gate.py evals/e1c_evaluation_2_version_witness.py tests/test_e1c_evaluation_2_behavior_gate.py tests/test_e1c_evaluation_2_version_witness.py evals/e1c_evaluation_2_version_resume.py tests/test_e1c_evaluation_2_version_resume.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_qualification.py tests/test_e1c_evaluation_2_qualification_v2.py tests/test_e1c_evaluation_2_qualification_v3.py tests/test_e1c_evaluation_2_reference_scope.py tests/test_e1c_evaluation_2_export_chain.py tests/test_e1c_evaluation_2_object_observer.py tests/test_e1c_evaluation_2_object_observer_v2.py tests/test_e1c_evaluation_2_pair_input_observer.py tests/test_e1c_evaluation_2_parameter_contract.py tests/test_e1c_evaluation_2_behavior_gate.py tests/test_e1c_evaluation_2_version_witness.py tests/test_e1c_evaluation_2_version_resume.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m evals.v3_compact_pilot preflight
uv run --frozen python -m pytest -q
```

无需DeepSeek/tunnel密钥，合成preflight不是sealed TEST实验。依赖安装失败报环境阻塞，不降低断言/timeout/skip；源码与uv.lock可云端运行，本机exact-base/private .codex/镜像/runtime不随Git同步，缺材料报INFRA_BLOCKED。旧bridge白名单未扩、不假称新paid端到端已验、不开放裸Docker daemon、不上传key/raw/Gold。

## 4. 付费、安全与回传

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后独立Gold；原v2/expectation-v1/report-anchor-v1和两个observer namespace都不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
