# E1-C Strict Successor — Setup-Closure Development Change Card

Date: 2026-09-27
Status: PREDECLARED_BEFORE_IMPLEMENTATION
Provider/model calls: 0

## Problem
Historical E1-C DEV30 (`e1c-dev-v21-n30-7d8e6569`) has 30 rows / 4 resolved. Dominant unresolved class is `evidence_insufficient` (18/30), ahead of verification_failure (4), candidate_exception (3), patch_failure (1). The prior successor's only typed old-DEV witness (`django__django-11734`) passed exact-base/image/network/safety checks but real canonical preflight returned code 1 and remained `execution_ready=false`. Its public issue statement contains the scenario but does not define `Number`/`Item`; reconstructing test setup from tests/Gold is prohibited.

## Hypothesis
A generic setup-closure layer can improve trustworthy behavioral evidence by refusing non-self-contained issue scenarios early and promoting only issue-derived Python scenarios whose free names are closed by: (a) local definitions/imports in the public issue snippet, (b) Python builtins, or (c) bounded production-source symbols resolved by the existing automatic localization path. No task-ID map, test module, Gold, test.patch, official grade, or historical solution may provide closure.

## Change scope
Only reproducer preparation / execution-readiness. Locator, editor, model prompt, provider budget, grader, and sealed V20–V25 artifacts remain unchanged.

## Predeclared old-DEV30 development procedure
1. Use the already-seen 30-task DEV identity with manifest SHA `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`.
2. Read only public problem statements and exact-base production source already allowed by the strict protocol. Do not read test.patch, Gold, official grader outcomes, or test source to construct setup.
3. Deterministically extract Python-looking issue snippets, parse AST, compute free-name closure, and classify each candidate as `closed`, `production_resolvable`, or `unresolved`.
4. Do not execute unresolved candidates. Persist why each name is unresolved.
5. For execution, use only digest-pinned official images, exact-base identity, `--network none`, and bounded timeout. No automatic retry.

## Development gate
All must hold before any successor freeze/canary selection:
- provider/model calls = 0;
- full 30-task denominator preserved;
- task-ID-specific rules = 0;
- Gold/test.patch/official-grade/test-source setup accesses = 0;
- focused safety/leakage tests pass;
- old DEV30 analysis produces at least 3 closure-complete or production-resolvable behavioral candidates across at least 2 distinct repos (prevents one-task overfit);
- at least 1 such candidate completes a real exact-base digest-pinned network-disabled preflight with `execution_ready=true`;
- the known django-11734 witness remains fail-closed unless closure becomes available from allowed public issue/production evidence alone;
- no regression to frozen V25 old-DEV summary invariants (6/6 consensus, minimum family support >=2, total support >=17).

If this gate fails, preserve a development negative and do not freeze/select a canary. If it passes, freeze the mechanism before selecting a new independent non-overlapping canary.
