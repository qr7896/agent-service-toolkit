# E1-B v9.1 Target/Effect Semantic Verifier — Offline Candidate

Date: 2026-09-20  
Schema: `e1b-semantic-effect-v1`  
Status: offline only; no live runner and no provider/model call.

## Why a separate version

Frozen v9 checks coarse branch action class: identity versus change. Its documented false-accept boundary is that any change can pass even when it changes to the wrong target. v9.1 is a new schema rather than a silent mutation.

The current v6 public contract extractor exposes named values in change clauses and preservation clauses, but it does **not** establish a deterministic source→target mapping. Therefore v9.1 never invents a target from that extractor. Exact target verification is enabled only when a richer public/synthetic obligation explicitly supplies `target_value`; otherwise the report says `target_verification=unavailable`.

## Conservative semantics

For simple Python `name == literal` / `name is literal` guards, the verifier supports string, boolean and integer literals. A single `return` or direct assignment to the guarded variable is classified as identity/change. When an explicit target exists, a change must produce that exact literal. Identity requires preserving the guarded variable rather than merely returning an equal-looking literal.

Obvious call statements and attribute/subscript writes inside the guarded branch are treated as side-effect/ambiguity and fail closed. Multiple statements, duplicate guards, unsupported syntax/files, missing guards and zero obligations do not produce PASS. Output ordering is deterministic.

## Boundaries

PASS is a static source/target/action/effect witness, not semantic equivalence. It does not prove reachability, alias correctness, interprocedural effects, exception behavior, hidden mutation inside a returned call, or correctness outside recognized branches.

Expected false rejects include helper-based transforms, tables, match/case, enums, compound guards, safe logging, deliberate object mutation, fallthrough identity and non-Python implementations. Expected false accepts remain possible when code is unreachable, a syntactically correct literal has the wrong domain meaning, or effects occur outside the recognized branch.

## Evaluation boundary

This module is developed and tested only with synthetic/public generic examples. It must not be tuned against the four repeatedly observed DEV outcomes. No v9.1 live evaluation is authorized by this document. A future evaluation requires a separately frozen runner/protocol and the existing held-out integrity rules.
