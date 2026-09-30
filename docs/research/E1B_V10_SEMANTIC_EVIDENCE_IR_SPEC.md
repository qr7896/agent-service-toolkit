# E1-B v10 Semantic Evidence IR — Reliable Verification Layer

Date: 2026-09-20  
Schema: `e1b-semantic-evidence-ir-v1`  
Status: offline architecture/prototype only.

## Purpose

v7-v9.3 introduced useful but separate concepts: participant coverage, state obligations, identity/change actions, exact targets, effect risk, typed dataflow and bounded helper summaries. v10 stops adding syntax-specific gates and normalizes these concepts into one auditable Semantic Evidence IR.

An obligation states what must hold. Evidence states what a deterministic verifier observed and where it came from. The verification layer decides whether each obligation is `satisfied`, `unsupported`, `ambiguous`, or `contradicted`, then fails closed unless every obligation is satisfied.

## Core records

Obligations carry an ID, kind, typed source, optional typed target and optional participant. Evidence carries an ID, kind/status, typed source/target, effect-risk flag and provenance: path, function, construct and bounded depth.

Typed literals preserve the bool/int distinction. Canonical JSON and SHA256 manifests make obligation/evidence sets auditable.

## Semantics

A single compatible support satisfies an obligation. Explicit wrong action/target, missing required coverage or effect risk is contradictory. Multiple compatible supports or provenance collisions are ambiguous. Missing or unsupported evidence remains unsupported rather than being mislabeled as contradiction.

All non-satisfied dispositions fail closed.

## Adapters

The new layer is designed to consume frozen-module audit artifacts rather than modify those modules. Coverage, direct typed dataflow and bounded-helper witnesses can be normalized into IR evidence. Any adapter uncertainty remains unsupported.

## Claim boundary

This IR does not make the underlying static analysis semantically complete. It provides deterministic normalization, provenance and conservative evidence composition. PASS means all supplied obligations have one non-conflicting supported evidence record under the frozen adapters; it does not prove runtime correctness, complete program semantics or repair success.

No live model runner is created. Development uses synthetic/public generic cases only.
