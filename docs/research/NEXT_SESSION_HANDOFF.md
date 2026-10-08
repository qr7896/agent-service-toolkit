# WebCodex 接手：E1-C evaluation_2

日期：2026-10-08。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[最新真实协议链结果](E1C2_PROTOCOL_EXECUTION_RESULTS_2026-10-08.md)。

## 1. 当前状态与禁止重跑

最新三阶段均completed/seal：2calls/5997tokens、5/20914、6/26797，新增共13/53708、两个旧DEV来源，最后两题abstained。真实Python已进入容器，Marshmallow normal×2=0/target×2=1，实际取得Schema并在下一请求暴露，重组prompt SHA匹配真实ledger。仍0合格候选/machine0/Agentrepair0，本轮未Gold。此前80k批16/53212、旧resume复用候选独立保留，不拼分。禁止run任何已封存namespace，不开canary/TEST/Fresh30/repair/E2。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

authority/scope/export仅审计，不改原模型输入。对象observer v1整体unknown且未执行容器，v2以模块全部有界构造器候选记录实际关系，不按with_metaclass猜继承。5条真实记录含2条不对应记录全部保留，DateTime exact与Schema MRO关系出现；runtime关系不证明公开意图，不清除旧严格unknown。两个namespace均完成，不重跑。

[最新公开收据](../../data/e1c_evaluation_2_protocol_pilot_results.json)绑定结果与最终XML SHA，所有更早receipt/负记录保留。原201/255/54以及新三阶段11/39/52产物和冻结method SHA保持。raw/probe/Gold/key本机。不得重跑三个protocol-stage namespace、acquisition checks/paid/gold/action-protocol check或任何更早started namespace。

## 2. 当前唯一下一步

最终Ruff/预算V3重点/新专项17项/合成compact preflight通过，完整1653 passed/4 skipped/33warnings（87.86秒），先前1636/1642/1648等XML保留，不报repair rate。

当前下一步：把新增environment_feedback.project_environment接真实execute返回→compact反馈→最终Human。它只接受两normal与target记录schema/input/image/base/optional module一致、offline/pull-never、非timeout有效运行；真实旧产物project/compact已零调用过，但尚无future paid接线。此事实是执行器强制导入失败，不是natural uninstall/实际guard值/语义证书。保持unknown/rejected，不把诊断当评分。

同一新方法补明确公开feature request的解释：base签名缺请求参数可作target失败入口，normal用生产支持的独立receiver，target配置不放shared setup，不更改公共值和锁定期待。fixture Foo/Schema关系仍unknown，优先接已有scope/export/MRO观察到qualification主链，不新建旁路collector或硬改unknown。

protocol_pilot已将policy/strict codec接真实内层；protocol_execution.validate_frontier会在进容器前检查原source-backed rephase是否移出control读取的直接receiver，明确缺失拒绝而不是生成NameError，不编造normal。复杂控制流保守未知/拒绝。三个producer已运行，不能用它们继续付费或改frozen源；未来仅新完整method/namespace、先最终messages/实际hooks正负验收再小额两来源DEV。

自动Source import匹配/overlay+compact messages在acquisition_context.py，内层owner防覆盖，输入不mutate，schema获取未知不认证，cap2symbol/issue+base、1MB/source、host/LF/base/SHA一致。下一轮预算保持小额：先两来源不扩九准入，input估计硬24k/output2k/未来首请求保护/retry0，建议最多6请求/40k且每题24k；先冻结精确命令，实际cap共同约束，不将24k输入当可突破总额。旧50k/80k/本轮20k+40k+40k账本不改，不在当前namespace重试。

之后按真实缺证处理production依赖/fixture作用域/paired receiver/公开期待与剩余义务，另版完整freeze→完整九准入DEV/native分账。可信gate真达成才历史全排除新canary一次≥2/3、Agent patch/official、DEV30/另授权Fresh30。当前无resume/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
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
