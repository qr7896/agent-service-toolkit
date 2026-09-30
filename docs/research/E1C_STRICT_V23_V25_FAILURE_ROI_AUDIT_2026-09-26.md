# E1-C Strict V23/V25 Failure and ROI Audit — 2026-09-26

## Scope
Zero-provider audit required by the PLAYBOOK after two independent mechanism/canary rounds fail to produce a net-new admissible live signal. This document is an audit, not a new mechanism freeze. It must not be used to tune V25 or reuse V23/V25 canary identities.

## Evidence
- V23: frozen independent canary failed the preregistered candidate gate (3/3 source ready, 3/3 projection supported, 1/3 executable, 0/3 consensus). No official-image/live phase was authorized.
- V25: zero-provider DEV gate passed before canary inspection (6/6 consensus, min family support 2, total family support 17), then a new independent canary passed the candidate gate with 2/3 executable candidates.
- V25 SymPy-16637 official image committed at `sha256:e9f3c11aec668ecba061657a380848ce3dd7f90c3b4cccebddcdb856c7347e4b`.
- SymPy Base ran exactly once. Source identity was valid and exact-base tree matched, but the official image Python runtime failed before parseable test output (`ValueError: source code string cannot contain null bytes`). Official parser result: valid_log=false, parsed_test_count=0, f2p_explicit_fail=0, phase_pass=false. Base is nonadmissible; Gold is prohibited and Base is not retried.
- V25 Django-12125 was already frozen non-executable. Therefore after SymPy became nonadmissible, only Django-12830 could possibly become trusted: maximum possible trusted=1 < preregistered required=2. The V25 live gate is mathematically unreachable; further image acquisition cannot change the gate and was stopped with cache preserved.

## ROI / stop decision
- Provider/model calls across this continuation: 0.
- No baseline/treatment live canary calls were authorized or consumed; there is no model-outcome denominator to reinterpret.
- Additional paid expansion has zero justified value until a new zero-provider mechanism can clear a predeclared development gate and a completely new independent canary is frozen.
- Per PLAYBOOK section 8, V23 + V25 constitute two different independent rounds without a net-new live gain. Paid expansion is paused. C5, DEV30 and Fresh30 remain closed.

## Research boundary
V23/V25 canary content, task-specific paths, grader outputs and Gold must not be used to modify their frozen mechanisms or train the next mechanism. Successor research may use old DEV/non-canary evidence and generic infrastructure lessons only. A later canary, if justified after the audit, requires a new mechanism identity and new non-overlapping metadata-first identities.

## Next allowed gate
Zero-provider successor mechanism research on old DEV/non-canary evidence only. Before any new canary: predeclare a measurable development improvement, pass focused/full non-model regressions and leakage audit, freeze mechanism/code/budget identity, then select a new independent metadata-only canary. No paid/live command is currently authorized.
