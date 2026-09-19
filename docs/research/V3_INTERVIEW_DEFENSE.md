# V3 Interview Defense

1. **Is this just reinventing agent memory?** No. The claim is not that memory is new; the research variable is a reliability-aware, temporally valid adoption policy and whether it helps under paired chronological evaluation. Existing memory systems are related work, not evidence that this policy works.

2. **Why is this not ordinary RAG?** RAG retrieves external knowledge. V3 retrieves prior execution experience with outcome, provenance, lifecycle, compatibility and temporal constraints; retrieval is separated from adoption.

3. **Why prospective data?** Retrospective rows can contain information unavailable at execution time. Prospective capture fixes the evidence boundary before outcomes are observed.

4. **Why can’t the old eight trajectories be used?** They have no execution-time commit provenance. Backfilling today’s HEAD would fabricate historical state and invalidate compatibility/alias checks.

5. **Retrieved versus adopted?** Retrieved means a candidate entered context; adopted means an observed policy decision used that experience. Retrieval frequency alone cannot establish memory influence.

6. **Why isn’t counterfactual replay causal?** It only establishes that compatible positive and negative prior evidence existed. It does not observe the same task executed under both interventions.

7. **Why is the Git commit important?** Experience validity depends on repository state. The commit anchors what code existed at execution time and supports alias blocking and commit-distance compatibility.

8. **Why can’t synthetic smoke results be reported as results?** Synthetic data validates plumbing and invariants, not behavior on real coding tasks. The artifact audit rejects synthetic evidence by default.

9. **What is the V2/V3 boundary?** V2 is within-task evidence acquisition and sufficiency. V3 asks whether cross-task experience memory improves later executions. V3 does not reopen V2 tuning.

10. **How would you demonstrate memory value?** Compare frozen memory arms on the same chronological eligible pool using independently graded task success plus attempts, reads and tool calls; also report abstention and stale-memory harm.

11. **What if memory makes results worse?** That is a valid result. Analyze whether harm comes from compatibility errors, stale experiences, adoption errors or cost overhead without changing the frozen policy on the evaluation cohort.

12. **Why have an abstain path?** Unknown commit distance or weak reliability should not be converted into false confidence. Abstention is part of the safety/reliability hypothesis and must be measured as a cost.

13. **Why separate positive, negative and excluded experience?** Treating unknown/read-only outcomes as failures manufactures negative evidence. Only semantically supported outcomes enter positive/negative comparison.

14. **Does 37 passing tests prove the research idea?** No. They establish implementation invariants and reproducibility gates. Efficacy requires real prospective paired evaluation.
