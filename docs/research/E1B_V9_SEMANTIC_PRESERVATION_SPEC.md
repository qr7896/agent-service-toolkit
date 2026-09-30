# E1-B v9 Semantic Preservation Verifier — Offline Candidate

Date: 2026-09-20  
Schema: `e1b-semantic-preservation-v1`  
Status: offline prototype only; no provider/model evaluation authorized or performed.

## Motivation

v8 exposed a concrete boundary on repeated DEV: a patch can contain the expected guarded state literals and still violate runtime preservation. v9 therefore does not add more lexical witnesses. It asks a narrower structural question: when an explicit Python equality branch guards a named state/value, is the branch action consistent with the obligation type?

## Frozen prototype scope

Input is a pre-existing public behavioral obligation list plus a candidate patch. The prototype parses Python with `ast`, recognizes only simple `name == constant` / `name is constant` guards, and classifies a single-statement branch as either identity (`return name` or `name = name`) or change (a different return/assignment). An identity obligation requires exactly one unambiguous identity branch; a change obligation requires exactly one unambiguous non-identity branch.

It fails closed for unsupported files, syntax errors, compound/multi-statement branch bodies, duplicate candidate guards, absent guards, and unsupported expressions. Zero obligations do not produce a semantic-success claim.

## What PASS means

PASS means only that every supplied obligation has one simple Python AST guard/action witness whose coarse action class matches `identity` or `change`, with no unsupported patch file in this prototype.

PASS does not prove semantic equivalence, correct variable/dataflow, correct returned value, side-effect freedom, path completeness, exception behavior, alias correctness, interprocedural behavior, or runtime correctness. In particular, a `change` action can still change to the wrong value.

## Expected false rejects

Legitimate implementations using dictionaries/tables, helper calls, match/case, enums, aliases, compound boolean guards, multiple statements, mutation followed by return, fallthrough identity, non-Python participants, or interprocedural preservation are intentionally rejected by this first prototype.

## Expected false accepts

The prototype can accept a branch that changes to the wrong target, uses the wrong semantic variable with the same literal, performs harmful side effects outside the recognized statement, or is unreachable at runtime. These require stronger dataflow/effect semantics or deterministic tests, not more lexical matching.

## Evaluation boundary

No v9 live runner is created here. Do not evaluate v9 by repeatedly tuning against the four observed DEV outcomes. Further design should use synthetic/public generic cases; only after a mechanism/spec freeze should a future evaluation be considered. Clean confirmatory claims remain subject to the replacement held-out protocol.
