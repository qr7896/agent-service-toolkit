# E1-B Autonomous Editor 未完成测试日志

> **2026-09-20 live-readiness update:** 12-task independent replacement cohort、真实 metadata admission、exact config/preregistration 与五件套 dry-run 已完成。dry-run 为 0 calls / 0 tokens，run=`e1b-8bbc8ba900559ce6`，package=`0f6846…f4d7`。当前 `READY_FOR_EXACT_COMMAND_AUTHORIZATION`；真实模型尚未启动。详见 `E1B_REPLACEMENT_PILOT_PREREGISTRATION.md` 与 `WEBCODEX_HANDOFF_2026-09-20.md`。
>
> replacement-cohort metadata template、curator README、one-shot preregistration、offline operator checklist 与 post-run reporting template 已建立。模板不含真实 held-out task content；下一未完成项仍是独立 curation process 提供真实 content-neutral metadata/attestations，而不是在 tuning context 自行构造 cohort。

> 更新：2026-09-20；状态：v2=0/4、v3=1/4、v4=2/4、v5=2/4。v5=8 calls / 5,707 tokens，provider ledger 对账一致，协议有效但 `freeze_ready=false`。原 6 条 TEST 未执行，但 fixture confidentiality 已破坏；replacement held-out protocol 已建立且未打开 outcome。

## 已完成前置

- E1-B 10/10 Base-Fail + Gold-Pass；与原始20条形成30-task executable pool。
- prospective split 已冻结：DEV 4 / TEST 6，source-commit overlap=[]。
- Gold source/label/grader 编辑阶段不可见；strict JSON patch、写路径/测试保护、sandbox、独立 pytest grader 已实现。
- deterministic DEV plumbing 已跑通；最近 harness + async adapter：11 passed in 15.75s。
- run_dev_with_editor 已取消隐式 full-workspace evidence；runlog 已绑定 model/prompt/split/tasks/config hashes。
- DeepSeek V4 Flash DEV one-shot：随后只补跑剩余 state-version-29 一次，现 4/4 DEV 均获得模型调用；第 4 条单次 22,860 tokens，累计 31,276 tokens，sealed TEST 调用数=0。

## P0：真实模型 DEV

- [x] Provider/model=`deepseek/deepseek-v4-flash`，仅运行 DEV，sealed TEST 未调用。
- [x] 已记录 temperature=0、seed=null、prompt SHA、iterations=1、write budget 与 sandbox policy。
- [x] DEV evidence protocol=`declared-seed-read-v1`；只读取任务公开声明的 setup paths，不读取 Gold/test content。
- [x] 已记录 calls、wall time、parse/model failure、files written、F2P/P2P、resolved 与 token usage。
- [x] resume 逻辑通过 22 项测试，且确认不会覆盖前三条真实结果；只补跑第 4 条 DEV 一次。
- [x] 第 4 条 state-version-29 已调用但未修复成功、未重试；单次 22,860 tokens，累计 31,276。
- [x] budgeted DEV v2 已真实完成：4 calls / 2,305 tokens，budget_status=within_limit，parse/model/budget failure 均为 0；deterministic audit 为 valid_failed_dev、freeze_ready=false，4 DEV resolved=0。
- [x] R10 v3 已真实完成：4 DEV / 8 calls / 5,311 tokens，parse/model/budget failure=0；1/4 resolved，deterministic audit=`valid_partial_dev`、`freeze_ready=false`，不冻结。
- [x] R10 v4 已真实完成：4 DEV / 8 calls / 5,789 tokens，parse/model/budget failure=0；2/4 resolved；相对 v3 新增 config-code-budget 成功、无 resolved regression；audit=`valid_partial_dev`、`freeze_ready=false`。
- [x] R10 v5 已真实完成：4 DEV / 8 calls / 5,707 tokens，2/4 resolved；0 parse/model/budget failure，ledger completed=8 且 token=5,707 完整对账；相对 v4 无新增 resolved、无 resolved regression，audit=`valid_partial_dev`、`freeze_ready=false`。
- [x] v6 offline contract representation/extraction 已完成：公开 DEV statement 被确定性拆为 target/preservation/named values/default identity transition；contract audit 4/4 valid，独立 runner/result/ledger 已建立，零调用 preflight 4/4 reserve-fit 且 artifact paths 不存在；focused 41 passed、Ruff clean、full suite 460 passed / 4 skipped。
- [x] v6 live DEV 已按精确授权执行一次：4 DEV / 8 calls / 5,912 tokens，0 parse/model/budget failure，ledger 8 completed calls / 5,912 tokens 完整对账；resolved=1/4。audit=`valid_regressed_dev`、`protocol_valid=true`、`freeze_ready=false`；config-code-budget 发生 1→0 regression，cross-module 与 state-version 仍失败。
- [x] v5↔v6 offline failure-delta 已完成：config regression 被归类为 participant-coverage failure（v5 覆盖 config+runtime，v6 漏 config）；cross-module 两文件均覆盖但 pending preservation 失败；state-version 单文件覆盖但 target/legacy preservation 均失败。因此不存在一个“共同缺文件”解释，必须拆成 Coverage Gap 与 Behavioral Preservation Gap。
- [x] v7 Contract Coverage Gate offline 候选已实现并强化为 runner-level invariant：`required_participants` 从公开 `setup_files` 确定性产生；proposal/final patch 在 apply/grade 前必须通过 `require_patch_coverage`，缺 participant fail-closed 为 `contract_coverage_failure`。新增 future v7 deterministic audit/freeze-gate 脚本，artifact 不存在时拒绝审计。zero-call preflight 4/4 reserve-fit，最大 review proxy=3,846<4,000，result/ledger 不存在；focused 46 passed、Ruff clean、full suite 465 passed / 4 skipped。
- [x] v7 live 已授权并完成。首次 invocation 因 runner 误用 v4 ledger 在 provider 前 fail（0 calls/0 tokens），保留 provenance、不计结果；修复后以 fresh v7b identity 运行：4 DEV / 8 calls / 5,797 tokens / 2/4 resolved，0 parse/model/budget/coverage failure；audit valid_partial_dev，v5→v7b improved=[] / regressed=[]。config 恢复成功；cross-module 与 state-version 仍失败且 coverage 均完整。
- [x] behavioral-preservation gap 的下一层 offline 原型已实现为 `e1b_behavior_witness_v8.py`：从公开 behavioral contract 的显式 target/preserved values 生成 lexical witness audit，可在 `failed/pending`、`version 1/version 2` 等显式状态缺席时 fail-closed；4 个专门测试通过，Ruff clean。该 gate 明确只是必要条件，不证明语义正确，当前不接入 live runner，以免未经 DEV live 校准就引入 false reject。
- [x] v7 已证明两个剩余失败 coverage complete，因此继续离线把 lexical Behavior Witness 升级为 `e1b_state_transition_v8.py`：公开 contract → canonical change/identity obligations → guarded-state witness audit；裸字符串不算显式 transition witness，缺 obligation 可 fail-closed。新增 5 个专项测试，相关 focused 17 passed，Ruff clean。
- [x] 新增 `e1b_state_transition_audit_v8.py`：只审 public DEV problem statements + v7 result metadata，provider_calls=0；明确记录 v7 artifact 不保存 patch body，因此不从 patch hash、grader 或 gold 猜测 transition verdict。cross-module 提取 failed/change + completed/identity；state-version 提取 version:1/change + version:2/identity。
- [x] v8 static necessary-condition candidate 的边界与 schema 已冻结到 `E1B_V8_STATE_TRANSITION_GATE_SPEC.md` / `e1b-state-transition-v1`：PASS/FAIL 均不等价于 semantic correctness；明确记录 helper/table/alias 等 false reject 与 syntactically guarded-but-wrong 等 false accept 风险。新增 truthiness-collapse rejection、deterministic patch ordering 与 schema tests。
- [x] v8 zero-call offline preflight 已实现：4 DEV、schema_valid=true、result/ledger 均不存在、ready_for_runner_freeze=true、`live_authorized=false`、provider_calls=0；focused 9 passed，Ruff clean。
- [x] v8 runner integration/result schema 已离线冻结：独立 run/ledger/result；result schema=`e1b-r10-v8-result-v1`；proposal/final patch 均按 Coverage→State-Transition 顺序在 apply/grade 前 fail-closed；coverage 与 transition failure 分类分离；zero-obligation task vacuous pass；proposal/final transition audit 持久化。新增 deterministic v8 audit/freeze script。
- [x] v8 live-runner zero-call preflight：ready=true，4/4 proposal/review reserve-fit，result/ledger=false，provider_calls=0，live_authorized=false；runner/gate focused 14 passed，Ruff clean；full suite 483 passed / 4 skipped / 33 warnings。
- [x] v8 gate failure 分类已从脆弱的 error-string matching 改成 typed `CoverageGateFailure` / `TransitionGateFailure`；coverage 先于 transition，proposal gate failure 天然发生在 review/apply/grade 之前，final gate failure 发生在 apply/grade 之前。
- [x] v8 audit synthetic coverage：允许 proposal gate 导致总 calls<8，只要求 started=completed=summary calls 且 tokens 对账；schema mismatch、ledger call mismatch、token mismatch 均 protocol invalid；freeze 仍严格要求 4/4 + no regression。runner+audit focused 10 passed；full 488 passed / 4 skipped / 33 warnings。
- [x] 修复 v8 intermediate persistence：统一 `build_report()`，中间/最终 result 都携带 v8 result schema + execution metadata，不再在 task 间隙留下 v0-shaped artifact。
- [x] v8 audit 加入 per-row schema/gate artifact + row-call/ledger/summary 三方对账。该测试实际发现原 synthetic fewer-call fixture 的 row model_calls 与 summary 不一致，现已 fail-closed；proposal-stage rejection 可缺 final artifacts，成功 row 必须四类 gate artifacts 完整。focused 12 passed；full 490 passed / 4 skipped / 33 warnings。
- [x] v8 live 已按精确授权执行一次且不重跑：4 DEV / 6 calls / 5,391 tokens / 0 resolved；0 parse/model/budget failure；audit=`valid_regressed_dev`、`protocol_valid=true`、`freeze_ready=false`。相对 v7b improved=[]，async-propagation 与 config-code-budget 从 1→0；config proposal 被 Coverage Gate 因缺 `config/retrieval.json` 拒绝；state-version proposal 被 State-Transition Gate 因缺 `identity:version:2` witness 拒绝；cross-module 通过静态 gate 但 pending preservation 仍失败，形成明确 false-accept boundary。详见 `RESULTS_E1B_R10_V8.md`。
- [x] v8 post-run observability 修复：历史 result 保持不变；未来 typed gate exception 会携带 deterministic rejected audit 并写入 `rejected_gate_audit`。full non-model regression 490 passed / 4 skipped / 33 warnings。
- [ ] 不再针对这 4 个重复 DEV 调 v8。若继续 semantic verifier，另开 v9/新版本，仅用 public/synthetic cases 设计并先冻结 spec。
- [x] v8 rejection observability 已加专项测试：Coverage/Transition typed exception 均携带 deterministic `audit`；未来 rejection row 可持久化 `rejected_gate_audit`。v8 audit 同时加入 completion semantics：未来 artifact 可显式 `run_complete=true`；历史已完成 v8 不改 artifact，以 4-row legacy completion evidence 兼容审计。
- [x] v9 offline semantic-preservation prototype 已新开版本，未修改 frozen v8：`e1b_semantic_preservation_v9.py` + `E1B_V9_SEMANTIC_PRESERVATION_SPEC.md`。使用 Python AST 将简单 `name == constant` 分支的单一 action 粗分为 identity/change；identity obligation 若被 destructive remap、change obligation 若仍 identity、重复 guard、多语句/非 Python/语法不支持均 fail-closed。zero obligations 不声称 semantic success。当前仅 synthetic/public generic tests，无 provider/live runner。
- [x] 最新验证：v8 observability/audit + v9 focused 22 passed；Ruff clean；full non-model suite 500 passed / 4 skipped / 33 warnings。
- [x] v9.1 `e1b-semantic-effect-v1` 已独立实现，未静默改 v9：只在 obligation 明确提供 `target_value` 时做 exact target verification；现有 v6 extractor 没有 source→target mapping，因此绝不从 named values 猜目标。支持 str/bool/int literal；wrong-target remap、identity→literal rewrite、obvious call/attribute/subscript side effect、duplicate guard、unsupported/non-Python、zero obligation 均保守拒绝；legacy change 无 target 时明确标 `target_verification=unavailable`。
- [x] v8 legacy completion audit 已从宽松 `len(after)==4` 收紧：要求 4 unique/common rows、tasks=attempted_tasks=4、historical provider run ID/ledger/evidence protocol/test_outcomes marker；Windows ledger path 做 canonical slash 比较。synthetic fake 4-row artifact 不再可能仅凭行数 freeze。
- [x] 最新验证：v9/v9.1/v8-audit focused 34 passed；Ruff fix 后 clean；full non-model suite **512 passed / 4 skipped / 33 warnings**。仍无 v9/v9.1 live runner/provider call。
- [x] v9.2 `e1b-semantic-dataflow-v1` 已独立实现：typed literal identity 修复 Python `False == 0` / `True == 1` collision；支持 simple intraprocedural alias、literal match/case、fully static literal dict lookup；动态 helper/interprocedural 仍 fail-closed。effect boundary 拒绝 Call/Attribute/Subscript/AugAssign/Delete/Raise/Yield/Await 与 multi-action。
- [x] v9.2 offline preflight 已冻结 synthetic corpus：6 cases，SHA256=`12178377aa5f4648102674585851077dc9dea0b25a8b79e9cc8beaff204f8fc1`，provider_calls=0，live_runner_exists=false。focused 38 passed；Ruff clean；full **523 passed / 4 skipped / 33 warnings**。
- [x] v9.3 `e1b-semantic-helper-v1` 已独立实现 bounded interprocedural summary：只接受 same-file、单参数、可静态归约的 pure helper，并仅允许 caller 通过 one-hop direct return 使用 summary；MAX_HELPER_DEPTH=1。nested helper/recursion/call side effect/attribute/subscript/raise/yield/await/loop/try/with/dynamic return/conflicting mapping 均 fail-closed。
- [x] v9.3 开发中专项测试抓到 depth-bound 漏洞：初版会把 inner helper 的合法 summary 错当成 top-level caller witness，使 nested chain 意外 PASS；已按根因修复为“被其他函数调用的 helper 本身不能作为外层 caller witness”，没有放宽测试。focused 40 passed。
- [x] v9.3 offline preflight：7 synthetic cases，MAX_HELPER_DEPTH=1，SHA256=`682464d5c8e9fb3746a7201ef4a2246e6c49b9a678617aea7bcfb0c5f12f4b85`，provider_calls=0，live_runner_exists=false。full **534 passed / 4 skipped / 33 warnings**。
- [x] v10 `e1b-semantic-evidence-ir-v1` 已建立统一 Semantic Evidence IR / Verification Layer，不再继续堆 syntax-specific gate。IR 统一 obligation/evidence：coverage、typed source、identity/change、optional exact target、effect risk、path/function/construct/depth provenance；输出 per-obligation `satisfied / unsupported / ambiguous / contradicted`，只有全 satisfied 才 PASS。
- [x] v10 已提供 frozen-module adapters：Coverage audit、v9.2 direct dataflow、v9.3 helper witness → IR；不修改旧模块。显式 wrong target/effect risk/coverage missing 属于 contradicted；缺证据/unsupported analyzer 属于 unsupported；重复 support/provenance collision 属于 ambiguous。
- [x] v10 canonical JSON + SHA256 manifest 保留 typed literal identity。offline preflight：7 synthetic cases，SHA256=`45a166f616a40f64cf31a0ed07fe1cd006f8715c3f02da7ed361df7f17087d10`，provider_calls=0，live_runner_exists=false。focused 29 passed；Ruff clean；full **541 passed / 4 skipped / 33 warnings**。
- [x] v10.1 `e1b-verification-decision-v1` 已建立 bounded Verification Decision Policy：固定 safety-first priority `contradicted > ambiguous > unsupported > satisfied`；对应 `BLOCK_PATCH / STRUCTURAL_ESCALATION / REQUEST_MORE_EVIDENCE / ALLOW_VERIFICATION`。ALLOW_VERIFICATION 明确只允许进入 downstream verification，不代表 PASS/repair success。
- [x] evidence sufficiency accounting 已统一记录 required/satisfied/unsupported/ambiguous/contradicted 与 per-kind required/satisfied；不引入伪 confidence/probability。MAX_ESCALATIONS=2；unsupported/ambiguous 消耗 budget，耗尽后 BLOCK_PATCH；contradiction 立即 block 且不消耗 budget。
- [x] v10.1 deterministic decision audit manifest 无 timestamp/random field。offline preflight：7 synthetic cases，SHA256=`1880cee469a6f01622a844147e6382f66beee1eddabe01a34785781ec3c6cb4a`，provider_calls=0，live_runner_exists=false。focused 26 passed；Ruff clean；full **549 passed / 4 skipped / 33 warnings**。
- [x] v10.2 `e1b-verification-control-runtime-v1` 已建立 deterministic synthetic control runtime：Evidence Acquisition → v10 IR verify → v10.1 decision → bounded escalation → terminal BLOCK_PATCH/ALLOW_VERIFICATION。Runtime state 固化 step、escalations、evidence IDs/manifest、terminal action；transition 固化 action/reason、before/after evidence hash。
- [x] v10.2 有两层独立终止边界：继承 MAX_ESCALATIONS=2，同时 MAX_STEPS=5；contradiction 立即终止，persistent unsupported/ambiguity budget exhaustion fail-closed，max-step guard 作为额外防死循环边界。conflicting duplicate evidence_id 显式记 collision 并进入 ambiguity，而非静默覆盖。
- [x] v10.2 offline preflight：8 synthetic cases，SHA256=`ee2f19df05345e6e96f9717540403743980a1ce83c277f7751c3a6d05afffb93`，provider_calls=0，live_runner_exists=false。focused 23 passed；Ruff 修复 2 个格式问题后 focused 仍 23 passed；full **557 passed / 4 skipped / 33 warnings**。
- [x] v10.3 `e1b-evidence-acquisition-v1` 已建立 deterministic Evidence Acquisition Planner：有限动作空间 lexical(1)、coverage_check(1)、direct_ast(2)、helper_summary(3)、structural_escalation(4)；unsupported 选择 cheapest compatible untried action，ambiguity 只走 structural escalation，contradiction bypass acquisition，失败动作不会重复。
- [x] v10.3 新增独立 acquisition cost bound `MAX_ACQUISITION_COST=8`，与 escalation/step bounds 分离；无 compatible untried action → EXHAUSTED，下一动作会超预算 → BUDGET_EXHAUSTED，均 fail-closed。runtime trace 记录 action/cost/cumulative cost/unresolved obligation IDs/before-after evidence hash。
- [x] v10.3 offline preflight：8 synthetic cases，SHA256=`58105d85bbd99017a4afa28a1a183359e47df9af1950473dae533e02680444e7`，provider_calls=0，live_runner_exists=false。focused 24 passed；Ruff clean；full **565 passed / 4 skipped / 33 warnings**。
- [x] v10.4 `e1b-acquisition-policy-interface-v1` 已建立可替换 Policy Interface；当前只实现 deterministic-v10.3 baseline，不训练 learned policy。runtime-safe features 仅含 compatibility、prior attempt、structural、protocol cost、unresolved disposition counts、remaining budget；feature leakage audit 对 gold/grader/resolved/expected_patch/outcome/test_result 字段 fail-closed。
- [x] 新增 `e1b-acquisition-counterfactual-replay-v1`：对 synthetic action-result fixtures 隔离 replay 各 admissible first action，只比较 terminal control action / steps / protocol cost / evidence count，不执行 patch、不报告 repair success。新增 action dominance audit，仅报告 identical-capability higher-cost action，不自动删 frozen action。
- [x] v10.4 preflight：action-set SHA256=`cfd3ae16b9ada2fe78dcdbee0cc2a2d753cab881ba961d98f97900fa9f5f31ac`；8-case corpus SHA256=`d857f49162a60e7ca36daefa7111d50e941fd5719390e5c0725bdccf67f01722`；provider_calls=0，live_runner=false，learned_policy=false。focused 16 passed；Ruff 修复 2 个格式问题后 focused 仍 16 passed；full **573 passed / 4 skipped / 33 warnings**。

## P0：Evidence 协议冻结

E1-B 没有可直接复用的 V1 frozen retrieval trace；另行建立协议前不能声称与 V1 使用相同 retrieved evidence。

- [~] DEV 已采用受限 `declared-seed-read-v1`；尚未记录 irrelevant-read ratio，也未冻结 TEST evidence-policy hash。

## P0：最终配置冻结

- [ ] R10 当前 v5 未达到 4/4 门槛，不冻结。只有后续 DEV 证据达到预声明冻结门且 artifact audit 通过才可 freeze；原 6 TEST 因 fixture confidentiality 破坏不得作为 clean confirmatory cohort。
- [x] replacement held-out protocol 已写入 `E1B_REPLACEMENT_HELDOUT_PROTOCOL.md`：冻结前 tuning context 只允许看到 count/source/commit/overlap audit/manifest hash，不看 task fixture/test/gold/symbol。
- [x] 隔离 curation process 已建立 12-task replacement held-out cohort；12/12 Base-Fail/独立 Gold-Pass，overlap audit 通过，manifest=`006b96…2a12`。

## P0：replacement held-out one-shot（原“6条 sealed TEST”计划已 superseded）

- [x] 原 6 条 TEST 的 clean-confirmatory 计划已废止：它们从未执行，但 fixture confidentiality 在 v3 后已破坏，不再用于 v4+ confirmatory claim。
- [~] replacement held-out cohort、配置和分析计划已冻结；等待 exact command 授权后一次性运行，不逐题调 prompt、不重试、不追加预算。
- [ ] 报告 Autonomous Repair Rate/pass@1、F2P/P2P、attempts、wall time、calls、files read/written、安全违规。
- [ ] Oracle 与 Autonomous 分开报告，计算 Editor/Reasoning Gap，并区分 Retrieval/Editor/Regression Gap。
- [ ] 保存 trajectory、final diff、grader result、config hash；小样本结果不宣称统计泛化。

## P1：安全与回归补强（已完成）

- [x] 递归 Gold-key leakage scan；canonical root/symlink 防护；normalized-path collision；strict string-only patch content。
- [x] 保护 `.git` / `.env` / `.codex`、test path；content ceiling；完整回归 E1 smoke + E1B harness + V1 decision/policy。
- [x] 不沿用两个无法查询的旧后台 job；2026-09-18 明确重跑 Runtime + E1 smoke + V1 decision/policy，最新结果 75 passed。该数字只表示非模型回归，不表示 Autonomous Repair Rate 或 patch success。

## 封存清单

DEV：async-propagation-22、config-code-budget-25、cross-module-status-26、state-version-29。
SEALED TEST：async-cancel-27、hard-negative-router-28、multifile-policy-21、multifile-sandbox-cleanup-30、resume-approval-23、symbol-hard-negative-24。

## Claim Boundary

可说：v2→v3→v4→v5 的 DEV resolved 为 0/4→1/4→2/4→2/4；v5 协议有效、预算内、ledger 对账完整、无 parse/model failure，但仍未达到冻结门；原 6 TEST 从未执行但 fixture confidentiality 已破坏。
不可说：DEV 2/4 是总体 Autonomous Repair Rate；v4/v5 差异具有统计显著性或因果性；preservation reviewer 已证明有效；原 6 TEST 是 clean confirmatory cohort；结果具有统计泛化性。
