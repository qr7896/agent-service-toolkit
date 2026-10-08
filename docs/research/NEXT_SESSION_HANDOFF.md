# WebCodex 接手：E1-C evaluation_2

日期：2026-10-08。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新环境/模块检索实链结果](E1C2_ENVIRONMENT_MODULE_RESULTS_2026-10-08.md)。

## 1. 当前状态与禁止重跑

最新环境版/模块检索版均completed/seal/gold：4calls/16647tokens与5/23320，新增9/39967。各一个新的同一SK有限候选、Gold各消除1/1；不是两题通过/Agent修复。MM模块函数查询现在成功，normal两0/target两1、Schema自动取得，下一真实请求有source和强制dateutil导入失败条件，prompt SHA匹配实际账本；剩fixture/异常链/旧版本期待unknown，3call cap停止。machine0/Agentrepair0。此前13/53708、16/53212及旧resume独立留存，不拼分。所有started run/gold不可重跑，canary/TEST/Fresh30/repair/E2关闭。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

authority/scope/export仅审计，不改原模型输入。对象observer v1整体unknown且未执行容器，v2以模块全部有界构造器候选记录实际关系，不按with_metaclass猜继承。5条真实记录含2条不对应记录全部保留，DateTime exact与Schema MRO关系出现；runtime关系不证明公开意图，不清除旧严格unknown。两个namespace均完成，不重跑。

[最新公开收据](../../data/e1c_evaluation_2_environment_module_results.json)绑定结果与最终XML SHA，所有更早receipt/负记录保留。原201/255/54/11/39/52及新52/130产物和冻结method SHA保持。raw/probe/Gold/key本机。不得重跑environment-feedback-flash-dev-v1、module-retrieval-flash-dev-v1或任何更早started namespace。

## 2. 当前唯一下一步

最终Ruff/预算V3重点/新专项7项/合成compact preflight通过，完整1660 passed/4 skipped/33warnings（96.77秒），先前XML保留，不报repair rate。

当前下一步先零模型资格主链接线：对最新MM有效probe的公开Foo/Schema/DateTime短名，接已有scope/export/object观察，分别标已证明身份、条件解释和未证明公共namespace意图；错alias/改值/假继承反例仍拒。将qualified属性/字段构造器纳入production依赖，按真实调用/异常路径选有界观察源，不用Schema类型名替代异常链。识别报告旧版本同probe/同条件的实际witness，缺资源明确阻塞，不挪其他task的witness。详见最新结果§3，不继续同类paid补budget或旁路collector。

环境反馈已在environment_dev实际executor返回→compact Human，matching schema/input/image/base/module、offline有效运行，消息zero gate被freeze SHA绑定；不称自然卸载/guard值、不提升unknown。feature request解释已促成新有限候选，但不证明default/增量。模块版保持class/plain retrieve，仅0结果做模块basename顶层定义fallback（最多两原32MiB扫描），origin明确hint/alias未证明。实际匹配和next Human/source/条件SHA证明均过。

现有有限gate故意full_issue_trusted/repair_eligible=false；先补真实行为义务或明确提议受限新协议，不得改False常量、把有限候选改名完整可信来进入canary。研究目标未完成，不能承诺30/30或完美。

protocol_pilot已将policy/strict codec接真实内层；protocol_execution.validate_frontier会在进容器前检查原source-backed rephase是否移出control读取的直接receiver，明确缺失拒绝而不是生成NameError，不编造normal。复杂控制流保守未知/拒绝。三个producer已运行，不能用它们继续付费或改frozen源；未来仅新完整method/namespace、先最终messages/实际hooks正负验收再小额两来源DEV。

自动Source import匹配/overlay+compact messages在acquisition_context.py，内层owner防覆盖，输入不mutate，schema获取未知不认证，cap2symbol/issue+base、1MB/source、host/LF/base/SHA一致。下一轮预算保持小额：先两来源不扩九准入，input估计硬24k/output2k/未来首请求保护/retry0，建议最多6请求/40k且每题24k；先冻结精确命令，实际cap共同约束，不将24k输入当可突破总额。旧50k/80k/本轮20k+40k+40k账本不改，不在当前namespace重试。

之后按真实缺证处理production依赖/fixture作用域/paired receiver/公开期待与剩余义务，另版完整freeze→完整九准入DEV/native分账。可信gate真达成才历史全排除新canary一次≥2/3、Agent patch/official、DEV30/另授权Fresh30。当前无resume/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_environment_dev.py evals/e1c_evaluation_2_module_retrieval_dev.py tests/test_e1c_evaluation_2_environment_dev.py tests/test_e1c_evaluation_2_module_retrieval_dev.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_environment_dev.py tests/test_e1c_evaluation_2_module_retrieval_dev.py tests/test_e1c_evaluation_2_environment_feedback.py
uv run --frozen python -m ruff check evals/e1c_evaluation_2_protocol_pilot.py evals/e1c_evaluation_2_protocol_probe_stage.py evals/e1c_evaluation_2_protocol_execution.py evals/e1c_evaluation_2_protocol_guard_dev.py evals/e1c_evaluation_2_environment_feedback.py tests/test_e1c_evaluation_2_protocol_pilot.py tests/test_e1c_evaluation_2_protocol_probe_stage.py tests/test_e1c_evaluation_2_protocol_execution.py tests/test_e1c_evaluation_2_protocol_guard_dev.py tests/test_e1c_evaluation_2_environment_feedback.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_protocol_pilot.py tests/test_e1c_evaluation_2_protocol_probe_stage.py tests/test_e1c_evaluation_2_protocol_execution.py tests/test_e1c_evaluation_2_protocol_guard_dev.py tests/test_e1c_evaluation_2_environment_feedback.py
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

未来新实验先列精确命令、Flash、次数与≤100,000 tokens，新未开始namespace，retry0、输入隔离、producer seal后才独立Gold；所有原版及三个protocol namespace都不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500，当前没有新canary/repair/E2命令待执行。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
