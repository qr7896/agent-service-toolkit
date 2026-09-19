# SERBench Upstream Audit

Date: 2026-09-18
Status: official checkout audited and exercised; no Test500 labels accessed; no model calls

## Verified upstream

Repository: `https://github.com/LordTARN1SHED/SERBench.git`.

Audited immutable commit: `8c27a88e48dcbcd4a5745573c95937a4740f4406`. The checkout lives outside tracked project content at `.external/SERBench`; benchmark data is not vendored.

Important correction: the current upstream README cites the work as a **2026 preprint** and explicitly says that a permanent preprint identifier will be added when available. Therefore project docs must **not treat `arXiv:2609.20050` as verified** from the upstream repository. Use the title/authors + SERBench repository until a permanent identifier is independently verified.

## Released benchmark interface

The public repository is the streamlined benchmark interface, not the paper's full experimental archive.

- Cal500: 500 states / 241 issue instances / 174 repositories / public calibration certificates.
- Test500: 500 states / 242 issue instances / 45 repositories / organizer-private certificates.
- Splits are repository-disjoint.
- State stages include before search, after search, after file inspection, and before editing.
- Core task: rank supplied candidate evidence so the returned set covers the support still missing from the captured state.
- This core track is candidate-set recovery, **not** full-repository retrieval or end-to-end repair.

## Official state fields

Use upstream IDs exactly; do not synthesize IDs from paths.

- `state_id`
- `instance_id`, `repo`
- `issue`, `information_need`
- optional captured context: `current_observation`, `current_hypothesis`, `current_subgoal`
- history: `opened_files`, `search_queries`, `observed_evidence_ids`
- `candidate_evidence`
- evidence records: `evidence_id`, `content_excerpt`, `source_path`, optional line/source metadata

This means our earlier generic compatibility contract is intentionally too generic for the real adapter. The real SERBench adapter should map these official fields rather than invent another benchmark schema.

## Certificates and leakage

Certificates describe residual requirements:
- AND across required groups;
- acceptable alternatives inside groups;
- alternative complete sets where present;
- group thresholds / `minimum_required`;
- necessity weights.

Cal500 labels are separate from inference data. Test500 labels are private.

**Controller/retriever inputs must use inference records only.** Certificates are retrospective scoring inputs. Do not merge labels into state text, candidate metadata, retrieval query, or V2 behavior-policy records.

Observed evidence can remain in the candidate pool and consumes returned rank positions. The official scorer does not mask it or backfill later IDs.

## Official prediction contract

UTF-8 JSONL, one row per state/method:

`{"state_id":"...","method":"...","ranked_evidence_ids":["..."]}`

Strict validation rejects duplicate state/method pairs, duplicate returned IDs, unknown states and out-of-pool IDs. Empty ranking is a valid abstention; omitted states are not.

## Official metrics

Use the upstream scorer as authoritative:

- `mss_complete@5`
- `mss_complete@8`
- `group_recall@5`
- `group_recall@8`
- `necessity_weighted_recall@5`

Do not replace these with our generic fallback metric for reported SERBench results.

## Upstream reference numbers

The upstream README reports frozen Test500 paper results:
- Qwen3 embedding + reranking: Complete-MSS@5 61.4%, @8 72.4%.
- MSS-Complement: Complete-MSS@5 73.0%, @8 80.6%.

These are upstream reference results, not reproduced by this project.

## License / rights

- Original interface/evaluation code: MIT.
- Original annotations/state-card material: CC BY 4.0 within the upstream-defined scope.
- Upstream repository code, issue text and source excerpts retain their original rights/licenses.

Therefore do not vendor/copy benchmark excerpts into this repository by default. Prefer a separate SERBench checkout + `SERBENCH_DATA_DIR`.

## Integration decision

**Do not extend `external_complete_set_recovery.py` into a SERBench clone.**

Next implementation should be a thin `serbench_adapter.py` that:
1. imports/uses the installed upstream `serbench` package when available;
2. loads `example` or `cal500` through upstream `load_dataset`;
3. converts our method output only into the official prediction contract;
4. delegates validation/scoring to upstream CLI/API;
5. never accesses Test500 certificates.

The upstream 3-state `example` integration and Cal500 evaluation are complete. The frozen Test500 prediction file passed official strict validation, but private certificates were not accessed and no held-out score is claimed.

## V2 research consequence

SERBench evaluates **which compact evidence set covers residual requirements**. Our V2-3 controller evaluates **whether to stop or switch acquisition modality as evidence evolves**. A fair comparison must therefore separate:
- supplied-candidate selection compatibility;
- full-repository acquisition control;
- downstream edit/repair evaluation.

Do not compare our current internal 10-task Oracle numbers directly against SERBench Test500 percentages.
