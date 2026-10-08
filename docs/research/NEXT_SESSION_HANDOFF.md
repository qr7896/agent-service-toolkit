# WebCodex 接手：E1-C evaluation_2

日期：2026-10-08。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新resume完整结果](E1C2_SCOPED_RESUME_RESULTS_2026-10-08.md)。

## 1. 当前状态与禁止重跑

授权resume-only已complete/seal/gold，原trial仍INTERRUPTED。新增7calls/29996tokens，累计10/43702，旧账本前缀复制保守累计，不重试旧3请求/probe。四screen终局：1复用子义务候选Gold消除过、2预算stop、1重复control失败stop；新生成合格候选0、machine0，不是四题全过/Agent repair。新router shadow三MM1252 feedback恢复Schema源建议，unknown不升级、未接live。禁止run/gold任何已封存namespace；不开canary/TEST/Fresh30/repair/E2。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

authority/scope/export仅审计，不改原模型输入。对象observer v1整体unknown且未执行容器，v2以模块全部有界构造器候选记录实际关系，不按with_metaclass猜继承。5条真实记录含2条不对应记录全部保留，DateTime exact与Schema MRO关系出现；runtime关系不证明公开意图，不清除旧严格unknown。两个namespace均完成，不重跑。

[最新公开收据](../../data/e1c_evaluation_2_scoped_resume_results.json)绑定结果与最终XML SHA；[原中断收据](../../data/e1c_evaluation_2_scoped_dev_results.json)和所有更早记录保留。原109文件、新seal255产物、原更早201产物与全部method SHA保持。raw/probe/Gold/test/key留本机；所有started namespace禁止重跑/改源，含resume、resume-zero、gold-discrimination、dependency-feedback-zero。

## 2. 当前唯一下一步

最终Ruff/预算V3/新专项重点36项/合成compact preflight通过，完整1615 passed/4 skipped/33warnings（79.10秒），先前1611等XML保留，不报repair rate。

当前唯一下一步是新producer接已验dependency route并实际执行有界production-symbol检索，恢复Scope/窗口/SHA，不按taskID人工选文件。只有新source/namespace才可改接线，禁止再run当前scoped_resume或router audit。MM1252缺旧版本执行证据仍保持；三原缺证反馈修复仅shadow，不能声称live效果。

同时用两预算停止真实上下文做零调用reserve验收：SK15351+11985>task24000，MM31757+10154>protected41520。先压重复诊断而不丢必需source/unknown/rejected/原期待，再真实prior-action消息，不在previous probe时错说检索完成，不把换input得到pass当bug修复。原50000额度仅余6298，不自动追加或改run_id清零；新实验先列精确命令/Flash/调用数/完整新预算，不能重跑old namespace。

之后按真实缺证处理production依赖/fixture作用域/paired receiver/公开期待与剩余义务，另版完整freeze→完整九准入DEV/native分账。可信gate真达成才历史全排除新canary一次≥2/3、Agent patch/official、DEV30/另授权Fresh30。当前无resume/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
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
