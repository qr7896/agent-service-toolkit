# E1-B Interview Defense

## “Isn't this just a pile of rules around an Agent?”

The current safety/control layer is deliberately deterministic. That is a baseline and experimental scaffold, not a claim that hand-written rules are the final policy. The research object is the state/action interface: what evidence is available, when acquisition stops or escalates, what must be verified, and which safety constraints a future learned policy cannot bypass. A learned policy has not yet been implemented, so I would not present one as completed work.

## “Why not just reuse CodeGraph or another Coding-Agent repository?”

CodeGraph-like structure is reused conceptually where it solves structural navigation. The project question is broader than graph retrieval: it asks when evidence is sufficient, when to switch modality, how to bound cost/risk, and how to verify/control the result. Reusing an entire agent would not by itself answer that experiment question. The project should still reuse mature components rather than reimplement commodity parsing, graph storage or model serving.

## “Where is the learned policy?”

There isn't one yet. v10.4 intentionally freezes a swappable policy interface around a deterministic v10.3 baseline. That separation prevents a future learned rank/stop policy from changing the verifier or safety boundary at the same time as the experimental treatment.

## “Why are there so many versions?”

The versions record failed hypotheses and frozen protocol changes: lexical witness limitations led to structured transition obligations; syntax-specific checks led to a unified Evidence IR; deterministic verification led to acquisition control; then the protocol was frozen and audited. For presentation, I collapse them into three or four contributions rather than narrating every version.

## “Does 611 passing tests mean the Agent repairs code successfully?”

No. 611/4/33 is a software regression baseline for the repository. It is not repair rate, benchmark accuracy, memory efficacy or model quality.

## “Did memory help?”

In the selected V3 paired pilot, n=3 showed no observed success benefit; OFF/ON patches were identical and ON used 369 more tokens in aggregate. That is enough to stop claiming an observed benefit in that small protocol, not enough to conclude memory is generally ineffective.

## “What did you actually invent?”

The strongest defensible answer is the research integration: evidence-sufficiency-aware acquisition decisions plus modality escalation, a typed semantic evidence/verification boundary, and a reproducible fail-closed experiment-control chain. Individual ingredients such as AST analysis, graph retrieval, LangGraph orchestration and memory are not claimed as inventions.

## “What evidence is still missing?”

A clean replacement held-out cohort, independently curated Base-Fail/Gold-Pass attestations, frozen exact model/config, and a preregistered one-shot experiment. v9-v10.8 currently provide offline/synthetic/control-plane evidence, not autonomous repair efficacy.

## “Why should I trust the evaluation?”

The original six TEST fixtures were never executed, but their fixture confidentiality was compromised after v3, so they are excluded from clean later confirmatory claims. The replacement protocol exposes only content-neutral metadata before freeze and chains freeze/admission/package hashes. That reduces researcher degrees of freedom; it does not magically prove external validity.
