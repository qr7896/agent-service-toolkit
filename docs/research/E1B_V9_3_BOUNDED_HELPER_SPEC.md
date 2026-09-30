# E1-B v9.3 Bounded Helper Summary — Offline Candidate

Date: 2026-09-20  
Schema: `e1b-semantic-helper-v1`  
Maximum helper depth: 1  
Status: offline synthetic/public prototype only.

## Purpose

v9.2 deliberately rejects dynamic helper calls such as `return normalize(status)`. v9.3 admits only a narrow subset: a same-file helper with one parameter whose body can be reduced deterministically to typed source→identity/change/target rows. The caller may consume that summary through one direct return call.

## Safety boundary

A helper is rejected if it has an unsupported signature, globals/nonlocals, attribute/subscript access, augmented assignment, delete, raise, yield, await, try/with, loops/comprehensions, any nested/direct call, unsupported control flow, dynamic return, or conflicting source mapping. Nested helper calls and recursion are therefore rejected by construction. Depth is frozen at one.

Supported helper mappings are simple literal `if` or literal `match/case` branches with a single return. String/bool/int literals remain typed, so booleans cannot satisfy integer obligations.

## Claim boundary

PASS means a same-file one-hop helper has a deterministic supported AST summary matching the supplied typed obligation. It does not prove runtime correctness, reachability, exception equivalence, total function behavior, purity outside recognized AST restrictions, or inter-file/interprocedural semantics beyond one hop.

The conservative policy intentionally false-rejects many valid helpers. This is preferable to recursively trusting dynamic code in a reliability gate.

## Offline freeze

`python -m evals.e1b_semantic_helper_v9_3_preflight` records schema, depth=1, synthetic corpus count/hash, provider_calls=0 and live_runner_exists=false. No DEV/TEST outcome is used by the preflight.
