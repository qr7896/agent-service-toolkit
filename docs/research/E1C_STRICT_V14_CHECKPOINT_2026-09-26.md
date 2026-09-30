# E1-C Strict-v14 checkpoint — 2026-09-26

Strict-v14 was developed only on synthetic and previously exposed development material. It adds a margin-gated multi-evidence structural witness combining issue-visible tokens, localization symbols/origins and production paths. Exposed development remains 6/6 executable while the focused suite grows to 27/27 PASS. Replay SHA-256: `28191d921bf62ed13c21c883cab0e292a84d5694a7726ff37dce40d6cd8e414d`.

The mechanism was frozen before identity selection. The boundary excludes 24 prior canary identities. At selection time the older v5-v7 official metadata pools were exhausted: all 24 identities were already excluded. This was recorded rather than bypassed by reuse. A zero-provider, metadata-only extension was then derived from the already-existing 30-task E1-C candidate manifest; no problem statements or tests were inspected, and deterministic SWE-bench image names were added. This yielded a new frozen canary: `django__django-11880`, `astropy__astropy-13453`, and `sympy__sympy-17318`.

All three statements and exact base sources materialized. Django required one bounded retry of the same frozen identity. Per-task frozen assessment measured Django as 1 executable candidate, Astropy as 0, and SymPy as 0. Thus strict-v14 can reach at most 1/3 executable and cannot satisfy the unchanged >=2/3 candidate gate. Official images and all downstream gates remain closed.

The aggregation blocker was closed without recomputation: the three already completed frozen per-task measurements were persisted into a resumable aggregate artifact, SHA-256 `eaa578381154d9193ceb6398faa58ea92d1d765078a53cbe0c9593af8310c3ee`. Strict-v14 is sealed negative with partial transfer at 1/3. No strict-v14 canary outcome may be used to tune strict-v14 or its successor.
