# E1-C Strict-v5 Handoff — 2026-09-25

## Read first

1. `E1C_STRICT_BLIND_DEV30_TO_FRESH30_PLAYBOOK.md`
2. `E1C_STRICT_V5_IMPLEMENTATION_STATUS_2026-09-25.md`
3. `data/e1c_strict_v5_failure_pareto.json`
4. `data/e1c_strict_v5_canary_manifest.template.json`

## Current state

Strict-v5 is now the only valid forward experiment lineage. The v4 live canary/result path is historical and non-authoritative for the strict assertion-blind protocol.

Zero-provider implementation now includes issue projection, repair-visible leakage/path guards, metadata-only reserve freeze, production-only localization, bounded inspect, zero-provider runner skeleton, audit-side DEV30 taxonomy, and fail-closed Canary/C5/Fresh30 gates.

Latest validation evidence:

- strict-v5 current full focused selection: **136 passed / 766 deselected / 5 deprecation warnings / 0 failures**
- latest full non-model regression: **899 passed / 4 skipped / 33 warnings / 0 failures** in 145.42s, using `uv run --frozen python -X utf8 -m pytest -q`
- strict-v5 + blind boundary/evidence subset: 42 passed
- v4 historical baseline: 14 passed / 4 warnings
- strict-v5 Ruff: clean
- provider/model calls added by strict-v5 work: 0
- new independent canary/Fresh30 task content opened: 0
- `new_task_tree_touched=false`
- conservative locally-touched/prior-lineage exclusion set: 232 identities
- runner DNS: GitHub Raw + Docker registry resolve; Hugging Face still fails DNS
- executable probe contract: safe literal-call grammar only; local execution is untrusted, Docker `--network none` path is required for trusted reproducer status
- source registry: official SWE-bench GitHub tree revision `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`, 500 resource identities, safe but incomplete (`instance_id+repo` only)
- Hugging Face DNS still unavailable; Docker registry reachable but insufficient to recover `base_commit`
- freeze certificate/materialization-plan tooling exists and currently blocks cleanly because the real strict-v5 canary manifest/audit do not exist
- superseding status: the official `SWE-bench/swe-bench-tasks` task repo provided safe metadata-only `task.yaml` at revision `3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d`; real strict-v5 canary identity is now frozen and certified
- frozen identities: `pydata__xarray-3993`, `sympy__sympy-15308`, `django__django-16092`
- post-freeze public statements have been materialized for exactly these three; strict projection succeeded 3/3; tests/Gold/test.patch remain outside repair-visible materialization
- grader-only is complete 3/3 tasks / 15/15 files; isolated verification/resume-admission tooling is implemented
- image transport snapshot: Docker Hub official manifests 0/3 reachable; GHCR Epoch manifests 3/3 reachable but explicitly non-authoritative; `mirror.gcr.io` 3/3 timed out without a digest
- `e1c_strict_v5_resume_admission` currently fails closed with all three exact frozen official images missing; provider/model calls remain 0
- `e1c_strict_v5_official_image_acquire` now gates every pull behind complete authoritative linux/amd64 manifest digests and verifies post-pull local RepoDigest equality; current real preflight is `official_manifest_preflight_incomplete / pull_attempted=false`
- `e1c_strict_v5_advance_admission` is the single preferred zero-provider entry point; current real state is `stage=official_image_acquisition / ready=false`, so verification/live remain unreachable
- image identity is now independent from transport: Docker Hub registry/tag-API digest is authoritative evidence; GHCR becomes transport-admissible only after an exact linux/amd64 digest match. Current no-proxy WebCodex snapshot is authoritative 0/3 and mirror-equivalent 0/3, so GHCR remains blocked.
- `e1c_strict_v5_equivalent_mirror_acquire` performs bounded mirror pull/tag only after that exact digest proof and verifies both mirror and official-tag RepoDigests before admission can continue.
- current WebCodex child environment has no HTTP/HTTPS proxy variables, although local `127.0.0.1:7892` is connectable. `advance_admission --proxy <explicit-proxy>` now scopes an intentional proxy to the command without serializing its value. The prior proxy-enabled evidence remains: official manifests 3/3 reachable, but xarray layer transfer timed out at 900s.
- a new curl-backed `e1c_strict_v5_blob_preflight` now runs before any missing-image pull. It bounds the sample to 1 MiB, resolves the exact linux/amd64 official manifest, measures a real layer, sums platform layer bytes, and estimates full-image transfer time against the frozen pull budget. Python `urllib` is not used for the transport verdict because it produced a TLS-handshake false negative while curl on the same proxy reached auth/manifest successfully.
- transport evidence is mixed rather than simply up/down: one bounded proxy run completed 1 MiB for all three frozen images at about 263/305/293 kB/s; the budget-aware xarray sample later measured 244,025 B/s over a **2,050,010,331-byte** platform image, estimating **8,400.8s**, far beyond the frozen 900s budget; a subsequent xarray repeat received only **274,071 bytes in 30.186s** before timeout. The current conclusion is transport variance + budget mismatch, not manifest unreachability.
- `advance_admission --pull-timeout 900 --proxy ...` now stops at `stage=blob_transport_preflight` and performs **0 Docker pulls** when the estimate exceeds budget or the bounded sample fails. Evidence summaries append to `data/e1c_strict_v5_blob_preflight_ledger.jsonl`, so later good/bad probes cannot erase prior transport evidence.
- proxy-aware authoritative identity is now implemented end-to-end, including propagation of the explicit proxy from `advance_admission` into its identity fallback. A real snapshot reached authoritative consensus for Sympy and Django from both Registry V2 and Docker Hub tag API, but each official digest differs from the corresponding GHCR digest. Therefore `mirror_mismatch_count=2` and the all-three GHCR admission path is **conclusively closed**, not merely pending proof. Xarray authoritative identity was temporarily unavailable in that snapshot, but it cannot rescue the all-three mirror gate because two rows already mismatch.
- `e1c_strict_v5_infra_gate` is now the read-only machine decision layer. Current real output: `official_transport_not_budget_admissible`, `next_action=bounded_transport_preflight_only`, `full_pull_allowed=false`, `mirror_route_conclusively_closed=true`, `mirror_pull_allowed=false`, `c5_allowed=false`, `fresh30_allowed=false`.
- local Docker sibling images show substantial Sympy/Django shared storage, but this is diagnostic-only. No frozen xarray sibling is local and incomplete registry cache cannot be authoritatively mapped through Docker CLI, so cache heuristics do not weaken or bypass the 900s gate.
- 2026-09-25 local follow-up: direct IPv4/IPv6 Docker Hub traffic still resets, but the existing Windows proxy `127.0.0.1:7892` makes all three frozen official manifests reachable. The acquisition code now handles both multi-arch OCI indexes and single-platform manifests, checks the official digest and linux/amd64 platform, and its focused tests pass 8/8. One bounded run of the exact zero-provider advance command then timed out on the first official xarray pull after 900 seconds; no local RepoDigest was produced, no verification ran, and provider calls remain 0. A 1 MiB HTTP range probe of an official xarray blob through the same proxy received only 129,767 bytes in 30 seconds before timeout. Image-layer throughput, not manifest availability, is now the observed external blocker.

## Stage A reproducibility seal

Playbook Stage A is machine-READY without opening live admission. Current strict-v5 workspace identity contains **90 relevant files**, SHA `03ede235f688353cdc024f60393d055b97cf0e3ec16e149329e20cbbcc9bd495`; all are dirty/untracked relative to HEAD, so `ad6426f` is only repository HEAD, not the experiment-code identity. The 31/31 legacy artifact seal remains unchanged. Stages B-E now also have machine gates; the A-E aggregate is `engineering_ready_a_through_e=true`, but independent-canary admission, live, C5, and Fresh30 remain closed.

## Current blocker

Docker Desktop itself is no longer the blocker. A WSL2 stale attachment (`WSL_E_USER_VHD_ALREADY_ATTACHED`) was cleared with `wsl --shutdown`, Docker Engine recovered, and the explicit proxy path remains healthy. The exact frozen Sympy official image has been pulled successfully, so only xarray and Django remain missing. The latest formal xarray sample is **316,599 B/s**, estimating **6475.1s** for the full image; targeted diagnostic Django is **300,969 B/s**, estimating **4490.1s**. Both remain above the frozen 900-second budget. Current cache-aware thresholds are xarray **2.245 MB/s**, Sympy **0 MB/s required / image local**, and Django **1.502 MB/s**. The unified infra gate therefore remains `full_pull_allowed=false`.

The v5 canary manifest exists and is certified. Exact-base source is ready 3/3, and grader-only materialization is complete 3/3 tasks / 15/15 files with `repair_visible=false`. The remaining blocker is official image-layer transport for the exact frozen Docker Hub images. The explicit proxy can resolve auth/manifests and sometimes transfer 1 MiB ranges, but measured xarray throughput is not compatible with the frozen 900-second pull budget and is unstable across bounded repeats. The budget-aware gate therefore stops before pull. `mirror.gcr.io` failed, and the GHCR route is now **conclusively closed** because Sympy and Django official linux/amd64 digests are known and differ from their GHCR mirror digests. Base-Fail/Gold-Pass therefore cannot yet run authoritatively. Current admission is incomplete, not failed.

Current admission seal: `reason=admission_prerequisites_incomplete`, `decisive_pre_live_failure=false`, `live_allowed=false`. Current v5 probe plan is `no_reproducer` for all three tasks, but this must not be promoted to a decisive mechanism result until image/Base-Fail/Gold-Pass/infrastructure prerequisites are complete.

## Exact next sequence

1. Preserve the frozen identity exactly as-is: `pydata__xarray-3993`, `sympy__sympy-15308`, `django__django-16092`. No redraw or outcome-conditioned replacement.
2. The three statements are already materialized post-freeze and strict projection is 3/3 supported.
3. Exact-base source trees are already materialized and source identity is 3/3 ready.
4. Do not blindly retry a 900-second pull or the same 1 MiB bounded probe under unchanged network conditions. The advisory trend currently says another immediate recheck has low information gain. The formal command remains `uv run --frozen python -X utf8 -m evals.e1c_strict_v5_advance_admission --pull-timeout 900 --proxy <validated-proxy>` and the formal gate is unchanged: a future bounded preflight must fit the same frozen budget before any pull. Do not raise the budget or retry GHCR as an admission bypass.
5. If image acquisition succeeds, the same command proceeds through isolated Base-Fail/Gold-Pass -> admission report -> seal. The repair-visible side receives only distilled verification evidence, not tests/Gold contents.
6. Only with complete prerequisites should current v5 `no_reproducer` observations be adjudicated. Require Docker `--network none` repeated stability for trusted reproducer status and at least 2/3 trusted reproducers.
9. Freeze strict-v5 code/config/model/prompt/call/token ceilings and produce one exact live command.
10. Stop and obtain explicit user authorization for that exact command.
11. Run paired canary once. Open C5 only for treatment-only official resolved >=1, baseline-only=0, and no identity/leak/safety/budget/infrastructure anomaly.
12. If open, freeze and run same-version DEV30 once; Fresh30 stays closed unless it is exactly 30 attempted / 30 official resolved / completed.
13. Only then select a brand-new Fresh30 metadata identity, admit 30/30, freeze configuration, obtain separate exact live authorization, and run one-shot.

## V6 quarantine

Files named `e1c_strict_v6_*` that appeared during this work are future mechanism-development artifacts only. They are contaminated by being developed after the current v5 canary was exposed. Do not run them on `pydata__xarray-3993`, `sympy__sympy-15308`, or `django__django-16092` as independent evidence, and do not open a v6 canary until the v5 admission/infra conclusion is sealed under the playbook.

## Forbidden shortcuts

Do not reuse v4 live results to open strict-v5 gates; do not inspect new task content before identity freeze; do not use public/official test assertions in repair-visible context; do not hand-select paths per task; do not rerun an independent canary identity until it works; do not outcome-condition replacements; do not combine cross-version best-of into a single-system score.
