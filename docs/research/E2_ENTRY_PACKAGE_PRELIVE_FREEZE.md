# E2 Entry Package — Pre-Live Freeze

Status: **E1C_OPERATIONAL_GATE_PASSED; E2_MAIN_NOT_STARTED**
Date: 2026-09-23

This freezes the E2 entry decision before E1-C outcomes are observed. It does not authorize E2 live execution.

2026-09-24 gate update: the independent E1-C n=30 audit found 30/30 complete, 0 critical safety violations and 0 infrastructure failures, so the predeclared operational gate passed. E2 still needs its own disjoint cohort, admission, contamination audit, zero-call multi-arm dry-run, resource decision and separate live authorization. Same-task E1-C DEV iterations do not satisfy those conditions.

## Entry gate

E2 may enter live preparation only if the completed E1-C n=30 audit has all of:

- artifact completeness = 100%
- critical safety violations = 0
- provider/infrastructure failures <= 3/30
- exact denominator = 30; no silent retry or dropped task
- runtime identity equals the E1-C frozen runtime, except separately disclosed infrastructure-only fixes

If any condition fails, E2 remains blocked. The failed E1-C rows stay in the denominator.

## E2 frozen minimum design

- 100 new tasks, disjoint from E1 and E1-C task lineage/source commits
- grouped repository/commit split and contamination audit
- primary paired comparisons: V0 Utility Gate vs Fixed-K lexical; frozen V2 vs V0 Utility Gate
- full main matrix: Fixed-K, V0 Evidence, V0 Utility, V1, V2 = 500 task-arm runs
- V3 Experience ON/OFF only on a predeclared strict-past eligible subset
- diagnostics on one fixed 30-task subset: No-RAG, lexical-only, semantic-only, No-CodeGraph
- no outcome-driven early stopping or arm deletion
- provider/infrastructure failures remain in denominator

## Analysis freeze

Primary reports: paired resolved-rate difference, bootstrap 95% CI, pass@1, F2P/P2P, calls, provider tokens, files read, irrelevant-read proxy, and safety events.

E3 efficacy path: paired resolved-rate delta versus V0 Utility has 95% CI lower bound > 0.

E3 efficiency path: resolved-rate noninferiority no worse than -5 percentage points, plus median tokens or files read at least 20% lower, with no new critical safety violation.

## Authorization boundary

This package is a zero-call pre-live freeze. E2 remains blocked until the E1-C n=30 gate is actually measured and passes.
