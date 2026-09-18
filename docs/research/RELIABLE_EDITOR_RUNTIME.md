# Reliable Editor Runtime

## Scope and claim boundary

This document freezes the deterministic runtime contract around evidence acquisition and safe repository access. It does not claim Autonomous Repair Rate, patch-success generalization, or learned-policy superiority. E1-B real-model DEV remains paused and the six prospective TEST outcomes remain sealed.

## Runtime architecture

```text
Planner / future LangGraph node
          |
          v
EvidenceController -- choose --> EvidencePolicy
          |                         |
          | execute                 +-- action / cost / risk budget
          v
WorkspaceRetrievalAdapter
   |          |          |
 lexical   semantic    structural
   |          |          +--> CodeGraphAdapter --> bounded traversal
   +----------+---------------------> EvidenceItem
                                      |
                                      v
                                EvidenceLedger
                                      |
                                      v
                                  trace / STOP

All repository reads --> SafeWorkspace --> path and read budgets --> Repository
```

Semantic retrieval reuses `agents.code_semantic` through a deterministic adapter and reads through `SafeWorkspace`; tests inject a fake embedding instead of loading BGE-M3. CodeGraph also reads through `SafeWorkspace`, and every lexical, semantic, and structural item enters the same `EvidenceLedger`.

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `evidence_runtime.py` | Uniform `EvidenceItem`, deduplication, per-action ledger rows and serializable evidence payload |
| `evidence_policy.py` | Explainable action selection and STOP under action/cost/risk budgets |
| `semantic_adapter.py` | Structured wrapper around local semantic code retrieval; emits uniform `EvidenceItem` records |
| `frozen_v1_policy_adapter.py` | Read-only adapter for the frozen V1 ranker/stopper with manifest verification |
| `evidence_controller.py` | Policy → execution → ledger → trace loop; errors are explicit and stop the run |
| `codegraph_adapter.py` | Read-only Python AST definitions, imports, callers and bounded traversal |
| `safe_workspace.py` | Canonical path containment, protected-path policy, read ceilings and structured rejection events |
| `e1b_autonomous_harness.py` | Gold-hidden editor payload, strict patch schema, write-path protection and independent grading |

## Evidence schema

Every evidence item has `path`, `content`, `source`, `score` and optional `symbol`. Structural evidence additionally records:

| Field | Meaning |
| --- | --- |
| `relation_type` | `definition`, `caller`, or `import` |
| `depth` | Bounded traversal BFS depth from the seed |
| `origin` | Original traversal seed; unchanged while the frontier expands |

The ledger deduplicates by evidence identity, then records `returned`, `new`, `redundant`, `redundancy`, `cost`, and `risk` for every action.

## Budget hierarchy

Budgets are independent and cumulative; a higher layer does not bypass a lower one.

1. CodeGraph traversal: `max_depth` and `max_nodes` bound graph expansion.
2. Evidence policy: `max_actions`, `max_cost`, and `max_risk` control acquisition and STOP.
3. Read boundary: `max_read_bytes`, `max_total_bytes`, and `max_read_calls` constrain repository access.
4. Editor boundary: `max_iterations`, `max_files_written`, test/protected-path policy, and the per-file patch-content ceiling constrain writes.
5. Experiment boundary: DEV-only until final freeze; six TEST outcomes remain sealed.

## Trace schema

Each controller trace row contains:

- `action`, `reason`, and returned `items` count;
- policy state `before` and `after`;
- on failure, exception type in `error` and its message;
- policy state with remaining/spent action, cost and risk budgets, unique evidence, and mean redundancy.

The snapshot contains `policy`, the serialized evidence payload, and the ordered `trace`. `execution_error` is terminal for the current controller run; it is never converted silently into another retrieval action.

## Failure taxonomy

SafeWorkspace emits a `workspace_error` event before raising the compatible Python exception.

| `error_type` | Meaning | Exception compatibility |
| --- | --- | --- |
| `path_denied` | Absolute, parent, drive-qualified, root-escape or symlink-escape path | `PermissionError` |
| `protected_path` | Access under `.git`, `.env`, `.codex`, or `__pycache__` | `PermissionError` |
| `not_found` | Requested path is not a regular file | `FileNotFoundError` |
| `single_file_budget_exceeded` | One file exceeds `max_read_bytes` | `PermissionError` |
| `total_byte_budget_exceeded` | The next read exceeds the cumulative byte ceiling | `PermissionError` |
| `read_call_budget_exceeded` | The next read exceeds the call ceiling | `PermissionError` |

Budget failures include `limit` and current/requested usage where applicable. Controller-level unavailable actions or adapter failures remain `execution_error`. Autonomous evaluation keeps retrieval, editor/reasoning, regression, model/parse, and budget failures separate from these runtime access events.

## Future LangGraph wiring

The future graph should store the controller snapshot in State and use deterministic conditional edges:

```text
plan evidence request
  -> controller step
  -> executed: update evidence state and re-plan
  -> policy_stop: continue to editor only if evidence sufficiency passes
  -> execution_error: record failure taxonomy and stop or request HITL
```

LangGraph must orchestrate this contract rather than reimplement budgets in prompts. Gold fields stay outside graph State during Autonomous evaluation. Any learned policy is injected behind the policy interface and versioned separately; frozen V1 artifacts are never overwritten.

The heuristic policies are explicitly versioned: `runtime-v0` preserves the original utility/cost/risk behavior, while `runtime-v1` adds last-action redundancy and structural-depth penalties. The separate `frozen-v1-adapter` verifies the frozen manifest before loading the existing ranker and stopper; it does not train or write model artifacts.

## Regression gate

The non-model gate covers Runtime, E1 smoke, V1 decision-dataset, and V1 learning-policy tests. The latest run passed 74 tests and is recorded in `PROGRESS_RESEARCH_ROADMAP.md`; passing this gate proves plumbing compatibility only.
