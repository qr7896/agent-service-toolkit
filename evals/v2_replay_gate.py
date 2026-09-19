from __future__ import annotations
from dataclasses import dataclass, asdict

ORIGINS={"empirical_logged","derived_offline","deterministic_runtime","synthetic"}
PROPENSITY={"logged_behavior","derived_uniform","plumbing_uniform","not_available"}

@dataclass(frozen=True)
class SourceProvenance:
    data_origin: str
    propensity_semantics: str
    behavior_policy_id: str | None = None
    def validate(self):
        if self.data_origin not in ORIGINS or self.propensity_semantics not in PROPENSITY:
            raise ValueError("unknown provenance semantics")
        return self

def replay_eligibility(validation: dict, sources: list[SourceProvenance]) -> dict:
    sources=[s.validate() for s in sources]
    schema_ready=not validation.get("errors")
    sample_ready=validation.get("records",0) >= validation.get("minimum_records",200)
    generic_ready=bool(validation.get("ready_for_replay")) and schema_ready and sample_ready
    supervised_ready=generic_ready
    ips_sources_ok=bool(sources) and all(
        s.data_origin=="empirical_logged" and
        s.propensity_semantics=="logged_behavior" and
        bool(s.behavior_policy_id)
        for s in sources
    )
    return {
        "schema_ready":schema_ready,
        "sample_ready":sample_ready,
        "generic_replay_ready":generic_ready,
        "supervised_replay_ready":supervised_ready,
        "ips_ready":generic_ready and ips_sources_ok,
        "source_provenance":[asdict(s) for s in sources],
    }
