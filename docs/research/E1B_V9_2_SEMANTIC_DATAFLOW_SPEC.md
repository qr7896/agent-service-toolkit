# E1-B v9.2 Semantic Dataflow Verifier — Offline Candidate

Date: 2026-09-20  
Schema: `e1b-semantic-dataflow-v1`  
Status: offline synthetic/public prototype; no live runner/provider calls.

## Delta from v9.1

v9.2 is separately versioned. It does not mutate frozen v9/v9.1. It addresses four explicit limitations: simple aliases, literal `match/case`, fully static literal dictionaries, and Python's `bool == int` equality collision.

Literal identity is typed, so `False` is not accepted as `0` and `True` is not accepted as `1`. Simple direct aliases are resolved intraprocedurally before guard/action comparison. Literal match cases and a local literal dictionary returned through `mapping[source]` can provide deterministic source/target witnesses.

## Effect boundary

Calls, attribute/subscript access in branch actions, augmented assignment, delete, raise, yield and await are considered risky/ambiguous and fail closed. Multi-action branches fail closed. Dynamic helpers and interprocedural transformations are not interpreted.

## Claim boundary

PASS means a supported AST shape supplies one deterministic typed source/action/optional-target witness for each supplied obligation. It is not semantic equivalence, dataflow completeness, reachability proof, side-effect freedom outside recognized nodes, or runtime correctness.

False rejects intentionally include safe helper calls, complex aliasing, enums, guarded match cases, comprehensions, dynamic dictionaries, mutations, fallthrough behavior and non-Python code. False accepts remain possible for unreachable code, semantically wrong but syntactically exact literals, and effects outside recognized action regions.

## Offline freeze artifact

`python -m evals.e1b_semantic_dataflow_v9_2_preflight` emits schema, a deterministic synthetic-corpus hash, case count, and `provider_calls=0`. It is not a live experiment and does not inspect DEV/TEST outcomes.
