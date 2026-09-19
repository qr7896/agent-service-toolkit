# External Sufficiency Benchmark Integration Plan

Date: 2026-09-19
Status: V2 external integration complete and frozen

## Purpose

Move the V2 evidence-acquisition work off the current small internal deterministic sample without copying or reimplementing an external benchmark. The immediate target is compatibility with a public sufficient-evidence benchmark such as SERBench, subject to an upstream repository/license/schema audit.

## Reuse-first rule

1. **Upstream evaluator is authoritative.** If the benchmark ships a loader/evaluator, call or adapt to it instead of recreating its metric.
2. **No vendored dataset by default.** Keep external data outside this repository unless its license explicitly permits redistribution.
3. **Thin compatibility seam only.** `evals/external_sufficiency_compat.py` validates a minimal exported schema; it does not claim to implement SERBench.
4. **Generic fallback metric only.** `external_complete_set_recovery.py` exists for fixture/compatibility testing. When upstream evaluation exists, report upstream numbers.
5. **No Gold online.** Required-evidence groups may score outputs retrospectively; they must not enter controller state or retrieval queries.
6. **No sealed E1-B TEST interaction.** External benchmark work is separate from the six sealed internal TEST cases.

## Minimal external export contract

Each external state should expose, after upstream preprocessing:

- `external_state_id`
- `repository`
- `state_text`
- `candidate_evidence`
- `required_evidence_groups` for retrospective complete-set scoring
- optional `source_commit` and metadata

This contract intentionally avoids assuming SERBench's exact field names before the upstream code is audited.

## Mapping into this project

External state → compatibility adapter → existing EvidenceStateFeatures / retrieval adapters → selected evidence IDs → upstream evaluator.

Do **not** translate external labels into V2 `chosen_action` behavior-policy records. External sufficiency labels and this project's action trajectories are different supervision objects.

## Required upstream audit before real data

Record:
- repository URL and immutable commit/tag;
- dataset/evaluator license;
- exact state schema;
- candidate unit identity and granularity;
- definition of required evidence groups;
- whether candidate construction uses Gold;
- official complete-set metric implementation;
- prompt/token budget accounting;
- repository checkout requirements;
- whether benchmark artifacts can be cached locally;
- whether MSS-Complement implementation/checkpoints are available.

## First real experiment

Use the smallest official non-test/dev slice allowed by the benchmark:
1. reproduce the official evaluator on an official baseline/output;
2. export states through the thin compatibility seam;
3. run an existing project retrieval arm without changing its algorithm;
4. score using the official evaluator;
5. compare only matched budget/state settings;
6. report compatibility failures separately from retrieval failures.

## Claim boundary

The upstream benchmark is audited at commit `8c27a88e48dcbcd4a5745573c95937a4740f4406`; the official example and Cal500 scorer were executed. The project is **SERBench Cal500-evaluated**, but is not numerically comparable to upstream Test500 MSS-Complement results. Test500 remains prediction-ready without private-label evaluation.

## Final V2 integration outcome

- Official example: loader → inference audit → abstention/lexical predictions → local preflight → official validator/scorer passed. This remains an integration check only.
- Cal500: 500 states, 174 repositories, 43,451 supplied candidates; official validator/scorer passed for all arms.
- Frozen method: `v2_candidate_compat_v2_4_1`, k=8, no Gold/certificate inputs, `mss_complete@5/@8=0.062/0.078`.
- Core-track separation: CodeGraph, repository acquisition, EvidenceController modality switching, and structural Filter V3 remain a separate acquisition-control track because SERBench core supplies candidate chunks and no CodeGraph relations.
- Test500: 500 predictions passed official strict validation. Private evaluation requires the official submission queue; no score was fabricated.


**V2-4 SERBench upstream audit + official-contract adapter（零模型调用）**：已核对公开 SERBench 仓库，而不是继续猜 schema。重要纠正：上游 README 当前把论文列为 **2026 preprint**，并明确写“permanent preprint identifier when available”；因此此前文档中把 `arXiv:2609.20050` 当已验证永久编号的写法不再可信，后续以论文标题/作者 + SERBench upstream 为准，直到独立验证永久编号。上游公开接口确认：Cal500=500 states/241 issues/174 repos/public certificates；Test500=500/242/45/private certificates，repository-disjoint。官方 inference fields 包括 state_id/instance_id/repo/issue/information_need/current observation-hypothesis-subgoal/opened_files/search_queries/observed_evidence_ids/candidate_evidence；prediction contract 为 state_id+method+ranked_evidence_ids。官方 primary metrics 是 mss_complete@5/@8、group_recall@5/@8、necessity_weighted_recall@5；因此本项目明确禁止扩写 generic fallback scorer 来复刻 SERBench，真实结果必须委托 upstream evaluator。新增 `SERBENCH_UPSTREAM_AUDIT.md` 与薄 `evals/serbench_adapter.py`，只做官方字段映射/预测契约，不复制 evaluator/data。上游代码 MIT，原始 annotations/state-card material 在其定义范围内 CC BY 4.0，而嵌入的 upstream code/issue/source excerpts 保留原权利，所以默认不 vendor 数据。第一真实接入顺序冻结为 upstream 3-state example → Cal500 → 方法冻结后才 Test500；Test500 certificates 不访问。定向回归 **25 passed**；模型 API=0；内部 sealed E1-B TEST=0。

**V2-4a official-runner seam（reuse upstream，零模型调用）**：已新增 `evals/serbench_official_runner.py`，目标不是复制 SERBench loader/scorer，而是从单独的 upstream checkout 直接 import `serbench.load_dataset`，生成官方 prediction JSONL。首个 integration method 故意使用官方允许的 empty-ranking abstention，避免为了“跑通”而临时发明 ranking 算法；真实 scorer 仍必须由 upstream CLI/API 执行。由于当前 WebCodex workspace 尚无已审计的 SERBench checkout，本轮没有伪造 example/Cal500 结果，也没有 vendor 数据。新增 runner contract test；与 adapter/external/V2 回归合计 **24 passed**。下一步唯一阻塞是把 upstream SERBench checkout 作为外部依赖提供给 runner，然后先跑官方 3-state example；在此之前 V2-4a 保持未完成。

**V2-4a candidate-pool integration arm + prediction preflight（reuse-first，零模型调用）**：在等待独立 SERBench upstream checkout 时，继续补齐不依赖 benchmark 数据的接口层，而没有伪造官方结果。新增 `serbench_candidate_ranker.py`：只使用 inference-visible issue/information_need/current state + 官方 supplied candidate excerpts 做确定性 lexical ranking，输出既有 `serbench_adapter.prediction` 契约；它是 integration/calibration baseline，不是新 retrieval 算法，也不读取 certificate/Gold。新增 `serbench_prediction_preflight.py`：在调用 upstream scorer 前本地 fail-fast 检查 duplicate state/method、duplicate evidence IDs、unknown state、out-of-pool IDs；明确 upstream validator/scorer 仍是 authoritative。定向回归 **24 passed**。当前 V2-4a 的代码路径已具备 upstream loader seam → candidate ranking/abstention → official prediction JSONL → local preflight；剩余阻塞仍是实际 upstream checkout + official 3-state example/scorer execution。模型 API=0，sealed E1-B TEST=0。

**V2-4 external-eval hardening（零模型调用）**：在 upstream checkout 尚未进入当前 workspace 的情况下，只完成不会重复造轮子的外围护栏。新增 `serbench_inference_audit.py`：只审计 inference JSONL 的 state/candidate IDs、candidate count、observed-evidence count 与 stage distribution，明确不接收/检查 certificate/Gold。新增 `serbench_method_freeze.py`：对 Cal500 prediction + official report 做 SHA-256 artifact freeze，并要求显式 verified upstream ref；若 upstream_ref=UNVERIFIED 或 split≠cal500，则 `test500_allowed=false`，防止在 Cal500 方法未冻结时误进 Test500。定向回归 **26 passed**。本轮没有假装已经拿到 SERBench 数据，也没有复制 upstream scorer。模型 API=0，sealed E1-B TEST=0。

**V2-4a upstream dependency resolution / blocker verification（零模型调用）**：本轮实际尝试把 SERBench upstream 拉进当前 WebCodex workspace，而不是继续写假 integration。WebCodex structured runner 拒绝直接启动 `git`/git.exe；随后用 Python HTTPS 访问 upstream raw GitHub，连接在读取阶段 timeout。因此当前环境确实没有可用 upstream checkout，且网络路径不能可靠完成下载。新增最小 `serbench_upstream_resolver.py`，只解析 `--root`、`SERBENCH_ROOT`、`.external/SERBench`、`../SERBench`，要求真实 `serbench/` package + README；当前实测输出 **found=false / ready=false**，并 fail-closed status 2。它不下载、不 vendor、不复制 benchmark。定向回归 **24 passed**。因此 V2-4a 当前阻塞被从“推测缺 upstream”升级为“已执行验证的 external-dependency blocker”；官方 example 仍不能诚实打勾。模型 API=0，E1-B sealed TEST=0。
