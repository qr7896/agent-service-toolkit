# V1 Learned Retrieval Policy — Frozen Evaluation

## Scope

V1 evaluates a learned retrieval-action ranker and an independent learned stopping policy on the V0 retrieval benchmark. This remains retrieval-layer evidence acquisition research; it is not an end-to-end code-repair success claim.

## Protocol

- 20 tasks, converted to 49 sequential decision episodes.
- Group-aware split: 12 train / 4 dev / 4 test tasks.
- Clusters and source_commit groups are disjoint across splits.
- The split is not described as temporal because reliable chronology is not available.
- Runtime features exclude Gold labels and counterfactual post-action observations.
- Ranker and stopper are selected using train/dev only.
- The frozen manifest records SHA-256 hashes for code, data, metrics, and model artifacts.
- Test evaluation is one-shot and only runs after manifest verification.

## Frozen policy

- Ranker: Logistic Regression.
- Stopper: Logistic Regression.
- STOP threshold: 0.942382.
- Threshold objective on dev: minimize 2 * false_stop + missed_stop.
- No post-hoc probability calibrator is fit because the dev set is very small.

## Ranker

| Split | Actionable episodes | Top-1 oracle action accuracy | Row accuracy | AUROC |
| --- | ---: | ---: | ---: | ---: |
| Train | 14 | 0.8571 | 0.9773 | 0.9730 |
| Dev | 7 | 0.5714 | 0.7941 | 0.8889 |
| Frozen test | 8 | 0.5000 | 0.8056 | 0.8661 |

The frozen test result is lower than dev Top-1 and should not be tuned against. It indicates only moderate action-selection transfer on the current small benchmark.

## Stopper

| Split | Episodes | Accuracy | AUROC | AUPRC | Brier | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 26 | 1.0000 | 1.0000 | 1.0000 | 0.0007 | 0.0243 |
| Dev | 11 | 1.0000 | 1.0000 | 1.0000 | 0.0092 | 0.0617 |
| Frozen test | 12 | 1.0000 | 1.0000 | 1.0000 | 0.0074 | 0.0541 |

Frozen test produced 0 false STOP and 0 missed STOP episodes. The sample is too small to infer broad generalization; the result is evidence that the current stop labels are highly separable in this benchmark.

## Ablation interpretation

On dev, removing candidate cost, candidate risk, or task text did not change actionable Top-1 from 0.5714. This means V1 does not establish an independent benefit for those feature groups. The small task count and coarse action space limit attribution.

## V1 conclusion and boundary

V1 demonstrates a leakage-controlled train/dev/test protocol, a deployable pre-action feature boundary, an independently learned stopper, calibration reporting, and a hash-verified frozen test. It does not yet demonstrate that the learned policy beats V0 Utility Gate on Gold Recall or reduces end-to-end retrieval cost, because the current frozen evaluation scores teacher imitation rather than replaying the learned policy through the retrieval environment.

Therefore the V1 roadmap Go/No-Go criterion is not yet satisfied. The next required experiment is frozen-policy replay: execute Ranker + Stopper sequentially on the test tasks and compare Gold Recall, retrieval actions, and context tokens against V0 Utility Gate without changing the frozen models.

## Frozen sequential replay and matched baseline

The frozen Ranker + Stopper was replayed sequentially on the four V1 frozen-test tasks at an 8K context budget. A matched V0 baseline was rerun on exactly the same task IDs and budget.

| Metric | V1 frozen policy | Matched V0 baseline | Change |
| --- | ---: | ---: | ---: |
| Context Recall | 0.7812 | 0.7812 | 0.0000 |
| Context Tokens | 87.0 | 122.5 | -28.98% |
| Retrieval / Tool Calls | 1.25 | 2.00 | -37.50% |
| Evidence Efficiency | 9.0702 | 6.9047 | +31.36% |
| Avg retrieval cost | 1.05 | 2.50 | -58.00% |

The learned policy preserved the matched baseline's measured context recall on all four frozen-test tasks while using less context and fewer retrieval actions. This is a retrieval-efficiency result only; it is not evidence of improved patch success.

Paired task bootstrap was repeated with seeds 0, 1, and 2, using 5,000 resamples per seed. All three seeds produced the same direction: recall delta was exactly 0 on all four tasks; context tokens had 3 wins / 1 tie / 0 losses with mean saving 35.5 tokens and 95% interval [13.0, 53.0]; tool calls had 3 wins / 1 tie / 0 losses with mean saving 0.75 calls and interval [0.25, 1.0]. These intervals are descriptive for this four-task benchmark and should not be treated as population-level confidence from a large independent sample.

## Frozen action-space ablation

To avoid pretending that V0 capabilities are ordinary ranker columns, V1 separates feature ablation from capability/action-space ablation. The frozen ranker, stopper, threshold, tasks, and 8K budget were kept unchanged while one retrieval action was removed at a time.

| Arm | Context Recall | Tokens | Tool Calls | Test Recall | Caller Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full | 0.7812 | 87.0 | 1.25 | 1.00 | 0.25 |
| No Structural | 0.5000 | 80.75 | 2.00 | 0.00 | 0.00 |
| No Semantic | 0.7812 | 87.0 | 1.25 | 1.00 | 0.25 |
| No Lexical | 0.7812 | 87.0 | 1.25 | 1.00 | 0.25 |
| No Files | 0.7812 | 99.5 | 1.25 | 1.00 | 0.25 |

Removing Structural is the only capability ablation that materially degrades evidence coverage on this four-task frozen subset: context recall falls by 0.2812, Gold Test Recall falls from 1.00 to 0, and Gold Caller Recall falls from 0.25 to 0, while tool calls increase from 1.25 to 2.00. This supports the narrower claim that structural retrieval is carrying unique test/caller evidence for these held-out tasks. Removing Semantic or Lexical does not change the aggregate replay result because the frozen policy does not need those actions on this subset. Removing Files preserves recall but increases tokens from 87.0 to 99.5 and average retrieval cost from 1.05 to 1.50.

This experiment is an action-space capability ablation, not an independent feature-effect estimate. V1 does not implement an explicit Experience-conditioned ranker feature, so no learned-policy No-Experience result is claimed; that question remains for V2/V3.

## Go / No-Go status

All three V1 Go/No-Go criteria are satisfied under the roadmap's current small-benchmark protocol: recall is not below V0; both token use and retrieval actions improve by more than 10%; and paired-bootstrap direction is consistent across seeds 0, 1, and 2. V1 is therefore marked **GO on the frozen retrieval benchmark**. This decision is deliberately scoped to retrieval-layer efficiency on four held-out tasks and is not an end-to-end repair-success claim.

The main observed weakness remains caller evidence: both policies obtain caller recall 0.25 on this subset. V1 improves efficiency rather than evidence coverage. Increasing caller/structural evidence coverage is therefore a candidate target for V2 rather than a reason to retune the frozen V1 policy.
