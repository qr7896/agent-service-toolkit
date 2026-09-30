# E1-C Strict-v7 Reproducer-focused Development Plan — 2026-09-26

## Why a successor is needed

Strict-v6 was correctly stopped before image acquisition: the independently frozen canary
produced 0/3 candidate executable reproducers against a preregistered minimum of 2/3.
The failure is mechanism coverage, not Docker availability.

The exposed v6 rows are now development-only evidence. They show three generic witness
families that the successor should be able to represent without reading public tests or
Gold patches:

1. state-transition / side-effect contracts;
2. multi-step Python scenario contracts;
3. build/render artifact contracts.

The successor must remain assertion-blind. It may use only projected public issue text,
production source localization, bounded production-source inspection, and deterministic
zero-provider transformations.

## Development target

Develop strict-v7 as a typed witness IR rather than another collection of issue-specific
regular expressions. Candidate witness types should have explicit provenance and execution
requirements:

- call-result witness: retain strict-v6 literal-call behavior;
- state-transition witness: precondition -> action -> observable postcondition;
- scenario witness: bounded self-contained Python snippet extracted from issue prose only;
- artifact witness: bounded local build command plus deterministic artifact predicate.

Each witness type must fail closed when imports, fixtures, setup, external network, or
expected observations cannot be justified from repair-visible evidence.

## Safety invariants

- no benchmark test assertion or Gold/test.patch content in repair-visible context;
- no per-task hand-written witness;
- no task ID, image tag, or grader path in the agent bundle;
- candidate execution occurs only in Docker with network disabled;
- witness must be frozen before Base-Fail/Gold-Pass;
- Base-Fail/Gold-Pass is independent grader evidence, never agent-visible evidence;
- no outcome-conditioned replacement or same-canary tuning;
- no model/provider call before zero-provider candidate admission;
- exact live command requires separate explicit authorization.

## Order of work

1. Implement typed witness IR and renderers against synthetic fixtures and already-exposed
   v6 development material.
2. Add negative tests for unsafe imports, shell metacharacters, external network recipes,
   test-path references, benchmark IDs, and non-production paths.
3. Require a focused engineering suite to pass before any new canary is selected.
4. Freeze mechanism file hashes and configuration.
5. Freeze the strict-v7 selection boundary. The boundary must include all earlier touched
   identities plus all three strict-v6 canary identities.
6. Only then select a new metadata-only three-task canary; do not open statements before
   identity freeze.
7. Materialize statements and exact base source for only that frozen canary.
8. Require at least 2/3 candidate executable witnesses before any large image pull.
9. If the candidate gate passes, acquire exact official images and run isolated Base-Fail /
   Gold-Pass plus repeated witness stability.
10. Only after at least 2/3 trusted reproducers and clean leakage/safety/budget gates may an
    exact live canary command be frozen.

The DEV30 -> C5 -> Fresh30 sequence remains closed until a successor mechanism passes this
independent canary path.
