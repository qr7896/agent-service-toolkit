# E2 Entry Gate Status — 2026-09-23

Status: **PASS_OPERATIONAL_ENTRY; E2_MAIN_NOT_STARTED**

The pre-live E2 entry criteria were frozen before any E1-C outcome. The measured E1-C audit below now closes that operational gate; E2 main remains separate.

## Measured E1-C live and Entry Gate (2026-09-24)

- Frozen cohort SHA-256: `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`; runner SHA-256: `24858b2b80e727cbe2e9e20d4ed7dea265aa18680404fdd073151304805e75e4`.
- The exact user-authorized live command completed once with 30/30 rows, 49 completed provider calls, 65,801 tokens, no failed/ambiguous provider event. First-pass resolved 0/30; final resolved 1/30 (one selective salvage). No outcome-based retry or cohort replacement.
- Independent audit at `.codex/e1c/e1c-n30-7d8e6569/audit.json`: artifact completeness=true (30/30), infrastructure failure tasks=0/30, critical safety violations=0. Two attempted writes to paths outside the displayed evidence were blocked before patch application; they are not successful forbidden writes. Final non-resolved rows comprise 25 official-grade failures plus 4 patch-validation failures.
- **E2 operational Entry Gate: PASS** on its predeclared completeness/safety/infrastructure criteria. This is not an E2 efficacy result: E1-C resolved only 1/30, and E2's independent n=100 paired multi-arm experiment has not begun. Formal E1 n=30 remains sealed at 0/30 and is never pooled into E1-C.

## Admission history (pre-live snapshots)

- **2026-09-24 final admission checkpoint (supersedes the older snapshot below):** original candidates **30/30 phase-recorded, 23 admitted**; all 10 deterministic replacements have both phase records, 8 admitted. Total 40 recorded / 31 admitted. Final n=30 cohort is the first 30 admitted in frozen discovery order; the 31st passing task is excluded from the denominator. Manifest SHA-256=`7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`. Its zero-call prompt/source preflight is 30/30 ready, max first reserve 3,916/4,000. Replacement 3's first Docker pull `unexpected EOF` log was preserved; the user explicitly authorized one successful retry. No E1-C live run, DeepSeek call, or E2 gate outcome.

- **Earlier v2 snapshot (historical):** original candidate 30; local images 23; recorded admission 23; Base-Fail PASS 18; Gold-Pass PASS 17; both phases admitted **17/30**. Five official images have non-allowlisted source drift (including newly observed `.ci/durations.json` and `.editorconfig`); one Gold phase passed targeted tests but failed harness cleanup, so it remains not admitted. The frozen original candidate manifest is unchanged. Deterministic selection has reached 40 metadata candidates, including 10 replacements; their public task files and exact source commits are **10/10 verified**, but image and official test admission are pending. Original candidate 24 (`matplotlib__matplotlib-24026`) hit its 3600-second Docker pull hard timeout; no phase results were produced and the batch stopped without retry. A guarded `--replacement-pool` continuation is available only after original 30 phase records exist. No final n=30 manifest, no DeepSeek E1-C calls, no E2 gate outcome. See [v2 source identity rule](./E1C_ADMISSION_V2_SOURCE_IDENTITY.md).

- Candidate manifest: 30 `selected_not_admitted`; SHA256 `16f86e20a296cc6e555038c0cbe336b6008d3b9252e8dc930a2d1c0a6cd9bca6`.
- Public task inventory: 30/30 complete; SHA256 `2fab1d97764557140926a78a285b8499c2537bc701dc06aaae5e854f250c7e03`.
- Source inventory: 30/30 exact `base_commit` matches; SHA256 `1f77339101734c2189e0143ba5dbc54f2f343b591df32a5bc8e55f755d0fdbef`.
- Static checks: 60/60 test/gold patches apply cleanly to their respective base; all 30 have nonempty FAIL_TO_PASS and PASS_TO_PASS metadata. These checks are **not** Base-Fail/Gold-Pass execution.
- Docker Desktop WSL2 engine: running; `docker info` and unauthenticated `docker run --rm hello-world` succeeded. Docker data disk is on `D:`.
- Original pre-admission candidate manifest (SHA256 `fc402eb31a9c031ed8a4e08727e2af7e3cbf20565df22178b06257539252d418`) is preserved in `.codex/e1c/pre_metadata_correction/`. `sphinx-doc__sphinx-9711` had an empty PASS_TO_PASS list and was replaced before any live outcome by the next deterministic eligible candidate, `pylint-dev__pylint-7080`. No task was replaced based on agent performance.
- Official-harness admission in progress: `sympy__sympy-13798` has Base-Fail PASS (explicit FAIL_TO_PASS failure 1/1) and independent Gold-Pass PASS (FAIL_TO_PASS 1/1, PASS_TO_PASS maintained 102/102). Both fresh containers matched the declared base source tree; the image adds an empty commit, so container HEAD itself differs. Logs and phase JSONs are in `.codex/e1c/admission/sympy__sympy-13798/`. Pinned SWE-bench parser commit: `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`.
- Second candidate `pytest-dev__pytest-5631` also passed: Base-Fail explicit 1/1; Gold-Pass F2P 1/1 and P2P 15/15. The first base container run produced a complete log but Windows GBK decoding interrupted post-processing before a phase JSON; its original log is preserved as `base.pre_utf8_fix.log` (SHA256 `a78b06c799b25de919626f998b9048b49e4ed3bfe61b4bc6af4a84ed96b73825`). A disclosed UTF-8-mode rerun in a fresh container produced the canonical base result; this is an admission infrastructure correction, not an agent/model retry.
- Candidates 3–5 also passed both stages. **5 validated candidates** in total. Local read-only runner preflight reports images 6/30, Base-Fail 5/30, Gold-Pass 5/30. The sixth candidate `sphinx-doc__sphinx-9230` failed before test execution: official image tree differs from requested base in `setup.py` and `tox.ini`; both failed phase artifacts are preserved. The next candidate `django__django-11880` image pull failed at Docker Hub anonymous-token `EOF` and the batch stopped. These are infrastructure/protocol failures, not Agent outcomes. See [WebCodex runner handoff](./EXPERIMENT_NETWORK_PREFLIGHT.md).

## Gate decision

Measured E1-C artifact completeness is 100%, critical safety violations 0, and infrastructure failure tasks 0/30 (threshold ≤3/30). The predeclared operational Entry Gate is **PASS**. Low repair efficacy (1/30) remains a substantive limitation and must not be presented as a positive efficacy signal.

## Unblock condition

Before E2 main, freeze its separate amendment/preregistration, curate an independent 100-task cohort, verify each task with Base-Fail/Gold-Pass and contamination checks, and pass zero-call multi-arm dry-runs. E2 real-model execution requires a new exact-command authorization; the E1-C authorization does not extend to E2.
