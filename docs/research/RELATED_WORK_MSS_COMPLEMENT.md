# Related Work Note — MSS-Complement vs. Evidence-Sufficiency-Aware Adaptive Retrieval

> Date: 2026-09-18
> Status: related-work correction + comparison protocol
> External model calls added by this note: 0
> Sealed TEST opened/called: 0

## 1. Newly relevant work

**Feng, Zhang, Yang, Xie (2026), _The Missing Complement: State-Conditioned Minimal Sufficient Evidence for Coding Agents_, arXiv:2609.20050, submitted 2026-09-17.**

Public abstract reports SERBench with 500 held-out agent states from 45 repositories. MSS-Complement formulates retrieval as state-conditioned minimal sufficient evidence recovery: recover a compact set covering every fact still required by the agent's next decision, rather than independently ranking passages by relevance. The abstract reports 4–8 intact source units within a 6,144-token budget; complete-set recovery of 73.0% at five items and 80.6% at eight in one fixed configuration; and an AMA-Bench result using a 76.2% smaller answer prompt.

Primary navigation:
- arXiv id: `2609.20050`
- benchmark/resource link reported by the abstract: `https://github.com/LordTARN1SHED/SERBench`

**Evidence rule:** until the full paper/code is locally reviewed, claims in this note that go beyond the public abstract must remain TODO rather than inferred.

## 2. What this changes for this project

The project must **stop claiming generic “Evidence Sufficiency for Coding Agents” as its novelty**. MSS-Complement already explicitly formulates state-conditioned minimal sufficient evidence recovery and set-level sufficiency.

The defensible research object is narrower and more operational:

> **Evidence-Sufficiency-Aware Adaptive Retrieval Control:** given the evolving evidence state and retrieval history, decide whether to STOP or acquire more evidence, and if acquisition should continue, which retrieval modality should be used under explicit cost/risk/redundancy constraints.

Working distinction:

| Axis | MSS-Complement (public abstract) | This project V2 |
|---|---|---|
| Main object | jointly sufficient evidence set | next retrieval/control action |
| State-conditioned | yes | yes |
| Sufficiency | set-level | controller state / stop condition |
| Explicit STOP action | not established from abstract | yes |
| Retrieval modality switching | not established from abstract | lexical → structural currently; action space also files/semantic |
| Structural graph | not established from abstract | CodeGraphAdapter |
| Cost/risk/redundancy state | token budget reported; other dimensions TBD | explicit cost, risk, redundancy |
| Compression | compact evidence set | runtime-only structural filter V3 |
| Current evaluation scale | 500 states / 45 repos | much smaller; 20 original/source problems overall, current adaptive audit 10 tasks |
| Current downstream evidence | repair-localization ablation reported | constrained Oracle editability only; autonomous effect unproven |

Do not turn “not established from abstract” into “paper does not do this.” Full-paper/code audit is required.

## 3. Existing evidence from this project that is relevant

Current deterministic V2 observations:

- repeated lexical branch: 20 actions / cost 22.0 / risk 6.0 / constrained-Oracle resolved 4/10;
- pure early stop: 10 / 11.0 / 3.0 / Oracle 4/10;
- adaptive stop-or-structural: 17 / 17.3 / 3.7 / Oracle 10/10;
- structural escalation initially produced 77 evidence items;
- runtime-only path-aware structural filter V3 reduces 77 → 12 items;
- structural evidence volume: 1310 → 226 chars; deterministic regex proxy tokens 402 → 74 (-81.59%);
- 7/7 escalated tasks retain retrospective target coverage after V3 filtering;
- constrained Oracle remains 10/10 after filtering.

These are **small deterministic-sample / constrained-Oracle results**. They are not Autonomous Repair Rate, not provider-token savings, and not evidence that this project outperforms MSS-Complement.

## 4. Strong comparison question

Avoid: “Which method is better?”

Use:

> **Does explicit acquisition control (STOP + modality switching) provide value beyond state-conditioned sufficient-set recovery, especially when repeated retrieval has zero marginal evidence gain?**

Subquestions:

1. **Stop:** when the current set is sufficient, can explicit STOP remove redundant acquisition without reducing downstream editability?
2. **Escalate:** when lexical evidence is insufficient, can structural escalation recover target-bearing evidence that repeated lexical retrieval misses?
3. **Compress:** after escalation, can runtime-only filtering reduce evidence volume while preserving target coverage?
4. **Budget:** what is the marginal evidence utility of each additional retrieval action under token/cost/risk budgets?
5. **Generalization:** do these effects survive on independent repositories/problems rather than aliases of the current benchmark family?

## 5. Fair comparison protocol

### Track A — SERBench compatibility
If SERBench artifacts/license permit:
1. reproduce the published MSS-Complement evaluation or an explicitly labelled compatible subset;
2. map captured state into this project's EvidenceStateFeatures without Gold leakage;
3. compare lexical/rerank, MSS-Complement, and adaptive controller under matched evidence budgets;
4. report complete-set recovery, evidence items/tokens, tool calls, latency/cost where available;
5. do not use project-specific Gold paths for online decisions.

### Track B — Runtime acquisition control
Create sequential states where an agent has already acquired evidence. Compare:
- repeat lexical;
- fixed-budget structural;
- MSS-style sufficient-set recovery if reproducible;
- adaptive STOP/structural controller;
- adaptive controller + V3 filter.

Primary metrics:
- complete required-evidence coverage;
- redundant retrieval actions;
- unique evidence gain per action;
- evidence volume;
- tool calls / retrieval cost / risk;
- downstream repair/localization only when independently graded.

### Track C — Complementarity
Test whether MSS-style recovered evidence can become an input/state feature for the controller:
`MSS recovery → sufficiency state → STOP / modality escalation`.
This tests complementarity instead of forcing a winner-take-all comparison.

## 6. Marginal Evidence Utility metric candidate

For action `a_t`:

`MEU(a_t) = ΔUsefulEvidence / (α·ΔEvidenceTokens + β·ΔCost + γ·ΔRisk)`

Protocol warning: “UsefulEvidence” must be defined without leaking Gold into the online controller. Gold/required groups may be used only for retrospective evaluation. A runtime proxy can use unique evidence gain, source diversity, structural relation quality, redundancy and budget state; causal validity is not yet established.

## 7. Novelty claims: red / yellow / green

### RED — retire now
- “first Evidence Sufficiency method for Coding Agents”
- “first minimal sufficient evidence retrieval for coding agents”
- any claim that sufficiency itself is the project's new concept

### YELLOW — requires full-paper/code audit
- “first explicit STOP controller”
- “first modality-switching sufficient-evidence controller”
- “first CodeGraph-guided sufficiency controller”
- any priority/first claim

### GREEN — current defensible project framing
- this implementation explicitly models retrieval as a safe action space including `stop/files/lexical/semantic/structural`;
- current deterministic experiments separate **stop**, **coverage escalation**, and **structural evidence compression**;
- current V3 filter is runtime-only and path-aware;
- current evidence includes explicit cost/risk/redundancy accounting;
- current results remain constrained/small-sample and do not establish autonomous repair superiority.

## 8. Immediate backlog

- [ ] Full-paper audit: algorithm, prompts, candidate construction, stopping behavior, retrieval tools, state representation, Gold use, executors, datasets, licenses.
- [ ] Inspect SERBench repository and record reproducibility requirements.
- [ ] Add MSS-Complement to the formal related-work bibliography.
- [ ] Add `source_problem_id`-strict external benchmark adapter before claiming cross-repository generalization.
- [ ] Implement MEU as an **offline diagnostic first**, not runtime control.
- [ ] Produce matched-budget comparison table.
- [ ] Expand independent problems/repositories before any superiority claim.
- [ ] Preserve commit/research chronology showing this project's pre-2026-09-17 EvidenceLedger/stop-vs-continue/structural-escalation work.

## 9. Claim boundary

The paper's publication makes this project's novelty bar stricter, but does not invalidate the current runtime-control direction. The safe thesis is **complementary control over evidence acquisition trajectories**, not ownership of minimal sufficient evidence as a concept.

## 10. Frozen external-evaluation conclusion (2026-09-19)

Official SERBench Cal500 evaluation confirms that the two tasks must remain separate. The direct V2 acquisition STOP rule abstained on 62.2% of states and reached `mss_complete@8=0.070`; the one corrected supplied-candidate mapping reached 0.078, while the deterministic lexical calibration arm reached 0.118. This is a negative external result for transferring the current acquisition controller into candidate ranking, not evidence that the runtime-control idea is invalid.

The upstream MSS-Complement `0.730/0.806` Complete-MSS@5/@8 figures are frozen **Test500** reference results. They are not compared as matched Cal500 measurements and were not reproduced here. No superiority claim is supported.


**V2-3 Matched-state / matched-budget retrieval comparison（零模型调用）**：停止继续发明指标，直接复用现有 `WorkspaceRetrievalAdapter`、`CodeGraphAdapter`、`visible_symbols` 与 Filter V3，新增 `v2_matched_retrieval.py` 做同一 initial runtime-visible state、每 arm **2 retrieval actions** 的 offline comparison：repeat lexical×2 vs structural traversal×2。随后 `v2_matched_retrieval_audit.py` 只在检索结束后用 Gold 做 retrospective scoring。10 tasks 结果：lexical target-path hit **4/10**，V3-retained structural **10/10**；retained evidence proxy tokens **521 vs 130**；lexical unique evidence **22**，structural retained unique **20**。再用同一 constrained Oracle grader 做 matched downstream：lexical **4/10 resolved**，structural **10/10 resolved**。这比此前 controller-selected 7-case efficiency comparison更少一个 selection confound，因为两种 modality 都从相同 initial state、相同 action count执行；但仍不是 randomized causal trial，structural query semantics 与 lexical query semantics 不同，也不能外推为 structural 普遍优越或优于 MSS-Complement。该结果支持下一步将重点放在 external/independent benchmark（优先 SERBench compatibility）而不是继续造本地指标。定向回归 **22 passed**；模型 API=0，sealed TEST=0。

**V2-4 External sufficient-evidence benchmark compatibility seam（reuse-first，零模型调用）**：本轮不继续扩内部10-task指标，也不复制外部 benchmark。新增 `evals/external_sufficiency_compat.py`，只定义最薄 external-state export contract（external_state_id/repository/state_text/candidate_evidence + retrospective required_evidence_groups），并 fail-closed 校验；新增 1 条 synthetic fixture 验证 adapter。新增 `external_complete_set_recovery.py` 仅作为 fixture/compatibility fallback metric，并明确：若 SERBench/upstream 提供官方 evaluator，**官方 evaluator 必须作为 authoritative implementation，禁止重复造轮子**。新增 `EXTERNAL_SUFFICIENCY_BENCHMARK_INTEGRATION.md` 固化 reuse-first 原则、license/commit/schema/candidate construction/Gold/token-budget/evaluator audit checklist，以及 first-real-experiment protocol。当前状态只能写 **integration-ready**，不能写 SERBench-evaluated，更不能与 MSS-Complement 数值比较。特别禁止把 external required-evidence labels 转成 V2 chosen_action behavior-policy data，两者 supervision object 不同。fixture compatibility report ready=true；定向回归 **23 passed**；模型 API=0，sealed TEST=0。下一步应审计 upstream SERBench repo/official evaluator，然后适配官方接口，而不是在本仓库重新实现 SERBench。

**V2-4 SERBench upstream audit + official-contract adapter（零模型调用）**：已核对公开 SERBench 仓库，而不是继续猜 schema。重要纠正：上游 README 当前把论文列为 **2026 preprint**，并明确写“permanent preprint identifier when available”；因此此前文档中把 `arXiv:2609.20050` 当已验证永久编号的写法不再可信，后续以论文标题/作者 + SERBench upstream 为准，直到独立验证永久编号。上游公开接口确认：Cal500=500 states/241 issues/174 repos/public certificates；Test500=500/242/45/private certificates，repository-disjoint。官方 inference fields 包括 state_id/instance_id/repo/issue/information_need/current observation-hypothesis-subgoal/opened_files/search_queries/observed_evidence_ids/candidate_evidence；prediction contract 为 state_id+method+ranked_evidence_ids。官方 primary metrics 是 mss_complete@5/@8、group_recall@5/@8、necessity_weighted_recall@5；因此本项目明确禁止扩写 generic fallback scorer 来复刻 SERBench，真实结果必须委托 upstream evaluator。新增 `SERBENCH_UPSTREAM_AUDIT.md` 与薄 `evals/serbench_adapter.py`，只做官方字段映射/预测契约，不复制 evaluator/data。上游代码 MIT，原始 annotations/state-card material 在其定义范围内 CC BY 4.0，而嵌入的 upstream code/issue/source excerpts 保留原权利，所以默认不 vendor 数据。第一真实接入顺序冻结为 upstream 3-state example → Cal500 → 方法冻结后才 Test500；Test500 certificates 不访问。定向回归 **25 passed**；模型 API=0；内部 sealed E1-B TEST=0。
