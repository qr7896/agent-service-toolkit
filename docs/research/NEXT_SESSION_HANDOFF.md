# WebCodex 接手：E1-C evaluation_2

日期：2026-10-09。先读[AGENTS.md](../../AGENTS.md)、[Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md)、[DEV v2最新真实结果/下一步](E1C2_PAIR_DEV_V2_RESULTS_2026-10-09.md)；[冻结快照](E1C2_PAIR_DEV_V2_READINESS_2026-10-09.md)和[前版分账](E1C2_FRESH_PAIR_RESULTS_2026-10-09.md)仅供追溯，不按旧待授权命令重跑。

## 0. 本次更新后的唯一下一步

v1已按精确授权执行：Flash3请求/15,764tokens；原2外壳拒绝/1同值无改动，原resolved0/3，没有候选实际进入原评分容器。另立zero解码后唯一保留模型patch被真实official评分：目标0/1、回归37/37。原公开probe正常/目标各两次在patch下完成，说明单条症状覆盖不足，不是任意工程数可以代替修复。v1/所有started zero目录禁止重跑，原method/输入/response/ledger/seal/result不改。

公开派生21个时间变体在base6/patch11/公开旧版21完成，10个漏修条件；未读取评分断言设计算子。不是21新task、返回值证明或通用完备覆盖。新v2已自动补3个生产global（包括regex/条件重赋值上下文），证据两组输入4自产base失败/旧公开版完成反例，严格组不输入base已有测试，Gold/新官方断言始终隔离。新decoder只兼容固定json_object元字段，raw与代码字符串保留，未知键/无改动不作成功。

v2已精确授权实跑：3calls/20,385，standard patch与前版字节相同，official F2P0/1/P2P37/37；两个证据组无改动，原0/3。无JSON拒绝，却没利用反例修复。v1/v2与所有started zero禁止重跑，不改源/成绩。

thinking8k已按精确授权执行：1call/13,708，实际enabled/high、8k全部reasoning、length截断/JSON0；没有实际候选评分，效果未测。原raw固定cells3有错误，freeze/实际1；zero独立verified-result标不一致、不改旧文件。不能称三个失败/能力无效，不保存reasoning正文。

completion已精确授权实跑：Flash1call/19,840，reasoning13,897/最终235，完整模型patch，official F2P1/1/P2P37/37 resolved。strict模型无现成断言/Gold，shared准备读base对象，旧full可信/namespace意图不提升。verified cells1，原legacy raw3保留。只能报一个看过DEV的真实修复，不报30/30、独立泛化或完整from-issue链。

zero验证原normal/target各两次完成；后续两wrapper前置失败分别由alias输入回查和dispatch目录混用导致，原目录/源不改不重跑。v3 dispatch/execution分离已完成首次21变体：base6、newpatch21、公开旧版21，10旧条件反例消失；原own×4不重播，21非新task/值等价。

已fresh issue-first重新检索两个旧library reference、各4窗口，不使用old effective windows/probe/成功patch定位。初漏SK IsolationForest本体，新通用backtick限定名resolve→base blob补3窗口，SK7/MM4；BaseBagging/BaseForest未resolve保留unknown。输入补证仅检索产物，需要下一whole method重建canonical/hash及最终messages，不能直接作为新的paid入口。

**最新真实执行：** fresh配对链已精确授权完成，4Flash calls/39,970tokens，pair执行2/2、原official1/2；MM新patch F2P1/1/P2P37/37。SK被type=json_object元字段拒绝，另立codec_zero无模型解码，代码字符串不改、自产post×4通过、F2P1/1/P2P19/19。原系统1/2不回填，full_issue_trusted false，两来源都是旧DEV；[报告](E1C2_FRESH_PAIR_RESULTS_2026-10-09.md)/[收据](../../data/e1c_evaluation_2_fresh_pair_results.json)。

以下两个命令已经完成，仅标识历史执行，**不得重跑**：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fresh_pair_pipeline run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fresh_pair_codec_zero
```

实际wire Flash enabled/high、每次20k、HTTP300、retry0；预算100k未扩大，余量不能再次消费已用满的4calls授权。原/zero source与全部seal/result/ledger字节核验保留，评分在全生成seal后，未回流模型。没有Gold/现成断言/旧patch输入actor。Cloud缺本机source artifact/镜像报INFRA_BLOCKED，不扩bridge白名单或上传私有材料。

**最新已完成：** DEV v2已正式接codec/条件检查，DEV12重新输入准备9ready/3缺source/issue；随后按精确授权运行SK26289/MM1359两题，3Flash calls/42,666tokens，原同版1/2。MM1359新模型patch F2P1/1/P2P76/76；SK quote不连续/非原文，生成门槛拒绝，未执行probe/repair，不包装成测试失败。全生成seal后评分，原source/results/ledger不改；不能拼前版最好成绩。

以下v2 paid命令已经授权完成，**不得重跑**：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_pair_dev_v2 run
```

Flash enabled/high、实际3calls全部completed/finish stop，100k预算未扩，MM repair19,556generated/19,494reasoning接近20k，不盲扩额度。原授权unused第4次不能挪到新身份自动retry；v2 prepare/paid已started完成，不能改frozen源/分数。两个最近批次7calls/82,636仅局部费用，不是项目全部费用/一个100kcohort。

**下一唯一工作：** 接`evals/e1c_evaluation_2_issue_anchor_codec.py`的调用前registry（公开投影issue最多12片/每片300 chars/ID/hash/offset），让新模型只选issue_anchor_id；解码为确切原文后复用原pair/namespace校验，normal/target代码字符串不改。5专项已有真实静态codec接线；当前仅原型，不是新完整live freeze，不事后修正SK引用。下一完整caller/schema/messages/registry与预算freeze后才列精确新付费命令。仍须公开义务/正常对照/环境资格核算，ID可追溯不等于语义可信或覆盖完整。不能直接抽canary/TEST/Fresh30/E2。

优先零模型检查：

```bash
uv run --frozen python -m ruff check evals/e1c_evaluation_2_pair_dev_v2.py evals/e1c_evaluation_2_issue_anchor_codec.py tests/test_e1c_evaluation_2_pair_dev_v2.py tests/test_e1c_evaluation_2_issue_anchor_codec.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_pair_dev_v2.py tests/test_e1c_evaluation_2_issue_anchor_codec.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
```

原completion/fresh_pair/v2 paid run已完成，旧zero/codec_zero/v2 prepare也已started/完成或失败，**不可重跑**。Cloud先执行源码单测；缺private父源/seal/镜像报INFRA_BLOCKED，不上传Gold/凭证，不扩白名单/开裸Docker。v2本机实际provider/容器评分已验，不称远程tunnel新入口已验；当前无待授权新live命令。

此后同版两来源从issue运行完整自动链，计入定位/probe成本→九准入固定12→完整freeze→新不重叠canary→另授权Fresh30/E2。标准组成功不称“不读断言”；严格组未通过也如实报告。不能保证30/30或一周完美。下方保留上轮历史交接细节，仅第0节是当前执行待办。

最新10新版/5anchor专项、重点34、全1784passed/4skipped/33warnings（68.72秒），Ruff/合成compact preflight过。[最新收据](../../data/e1c_evaluation_2_pair_dev_v2_results.json)绑定paid/prepare/seal/XML，旧readiness/成功收据保留，工程数非repair rate。frozen方法/协议不原地改，不上传raw/probe/Gold/key；后续保持Flash，不直接抽canary/TEST/Fresh30/E2。

## 1. 上轮状态与禁止重跑（历史说明）

最新public-release-witness-zero-v1已完成0calls/0tokens：用户下载的2.19.3官方包SHA核验，14生产Python仅只读挂载；同normal/target各两次旧版rc0，对比既有base正常两0/目标两1，四次实际version/path/manifest/probe/optional条件均核验。报告旧版执行witness支持，不是canonical Git/新样本/完整意图/修复。此前Controller异常对应true、scope/object保持；machine0/Agentrepair0。所有旧费/成绩分账、started namespace不重跑，canary/TEST/Fresh30/repair/E2关闭。

资格器检查已知fixture结构、alias/对象修改、production源绑定、期待锚、原probe观察、normal/target。17单测与四内存alias反例通过，静态反例不是四个新runtime故障。v1未暴露依赖被误拒留档，v2缺证unknown、已暴露真正SHA变化仍拒；增量赋值/删除等未知。

历史authority/scope/export审计未改当时模型输入；本轮新Controller已接scope/export/object反馈，不能回填旧结果。旧对象observer v1整体unknown且未执行容器，v2以模块有界构造器候选记录关系，不按with_metaclass猜继承；旧5条记录含2不对应记录保留。新旧运行关系都不证明公开意图，不清除strict unknown；所有已启动观察namespace不重跑。

[最新公开收据](../../data/e1c_evaluation_2_release_witness_results.json)绑定四运行结果/总freeze/result/XML SHA，旧receipt保留。八个原generation seal与父zero结果、新release source/method/protocol保持。raw/probe/wheel/Gold/key本机；release/source-evidence及更早started namespace均不重跑。

## 2. 上轮严格协议背景（已由第0节新协议接续）

最终Ruff/预算V3重点32/新专项13项/合成compact preflight通过，完整1680 passed/4 skipped/33warnings（103.79秒），旧XML保留，不报repair rate。

属性依赖/自动2源异常观察/scope-export-object已在source_evidence_controller实际主链挂载；旧strict unknown/rejected保留，summary到compact Human。限定4引用/1MB source，外部helpers不误补；新反馈projection使用实际selected proof，不把运行关系当namespace意图证书。

旧资源已由用户下载且零模型发行源码counterfactual完成，**不需要再下载/运行旧witness**。release_witness.py固定wheelSHA、zip原始路径/重复/symlink/budget检查、AST version声明，host不import/install；四个controller-owned driver在原readonly/offline image先核验实际版本/path/源manifest、原probe和阻断再运行。不是旧Git snapshot或Gold，不回填之前local-source-unavailable记录。

当前下一步是资格口径明确：默认完整门槛继续保留省略import的作者namespace意图/未覆盖义务unknown；若用户明确选择另立有限机制协议，必须新预注册条件/反例、机制/完整覆盖/official repair分账、整体method与预算冻结、先旧DEV验收，再独立canary。未答不能默认为有限协议，不能把release witness通过直接叫完整可信或启动repair/E2。Cloud缺本机素材报INFRA_BLOCKED，不扩tunnel白名单/开裸Docker。

用户已被问资格范围选择，未答时保持完整门槛；明确另立有限机制协议也须预注册/与完整可信分账，不能回填现结果或直接开canary/TEST/Fresh30。省略public import的意图仍未证，不用MRO/Gold消除称完整证明。

环境反馈已在environment_dev实际executor返回→compact Human，matching schema/input/image/base/module、offline有效运行，消息zero gate被freeze SHA绑定；不称自然卸载/guard值、不提升unknown。feature request解释已促成新有限候选，但不证明default/增量。模块版保持class/plain retrieve，仅0结果做模块basename顶层定义fallback（最多两原32MiB扫描），origin明确hint/alias未证明。实际匹配和next Human/source/条件SHA证明均过。

现有有限gate故意full_issue_trusted/repair_eligible=false；先补真实行为义务或明确提议受限新协议，不得改False常量、把有限候选改名完整可信来进入canary。研究目标未完成，不能承诺30/30或完美。

protocol_pilot已将policy/strict codec接真实内层；protocol_execution.validate_frontier会在进容器前检查原source-backed rephase是否移出control读取的直接receiver，明确缺失拒绝而不是生成NameError，不编造normal。复杂控制流保守未知/拒绝。三个producer已运行，不能用它们继续付费或改frozen源；未来仅新完整method/namespace、先最终messages/实际hooks正负验收再小额两来源DEV。

自动Source import匹配/overlay+compact messages在acquisition_context.py，内层owner防覆盖，输入不mutate，schema获取未知不认证，cap2symbol/issue+base、1MB/source、host/LF/base/SHA一致。下一轮预算保持小额：先两来源不扩九准入，input估计硬24k/output2k/未来首请求保护/retry0，建议最多6请求/40k且每题24k；先冻结精确命令，实际cap共同约束，不将24k输入当可突破总额。旧50k/80k/本轮20k+40k+40k账本不改，不在当前namespace重试。

之后按真实缺证处理production依赖/fixture作用域/paired receiver/公开期待与剩余义务，另版完整freeze→完整九准入DEV/native分账。可信gate真达成才历史全排除新canary一次≥2/3、Agent patch/official、DEV30/另授权Fresh30。当前无resume/canary命令，不抽第6批、不开始repair/E2，不保证完美。

## 3. Cloud可先执行的无模型检查

```bash
uv sync --frozen --group dev
uv run --frozen python -m ruff check evals/e1c_evaluation_2_release_witness.py tests/test_e1c_evaluation_2_release_witness.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_release_witness.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -m ruff check evals/e1c_evaluation_2_source_evidence_controller.py evals/e1c_evaluation_2_source_evidence_zero.py tests/test_e1c_evaluation_2_source_evidence_controller.py
uv run --frozen python -m pytest -q tests/test_e1c_evaluation_2_source_evidence_controller.py tests/test_e1c_evaluation_2_reference_scope.py tests/test_e1c_evaluation_2_export_chain.py tests/test_e1c_evaluation_2_object_observer_v2.py
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

未来新实验先列精确命令、Flash、次数与完整cohort预算，新未开始namespace，retry0、输入隔离、producer seal后才独立评分；所有已started身份不能“再试”。不使用Pro，不开sealed TEST/C5/Fresh30/SERBench私有Test500。第0节v2 run已完成，无待运行live/canary/E2命令。

本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，备份与负结果全保留。旧IPC授权已消费，任何新修改需明确限定授权；大文件交用户终端直连、不走VPN，当前无下载需求。

回传diff、实际hook证据与源SHA、工程数、paid ledger、Gold/语义/各固定分母、未过gate和下一步；不承诺完美/30题全过，不把Gold/回归称repair。日志只写[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，两Roadmap保持单一当前入口。旧快照/Git历史保留，不按历史“下一步”操作。
