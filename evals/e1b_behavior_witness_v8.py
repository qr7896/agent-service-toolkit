import re


def _normalized_variants(value):
    raw = value.strip().lower()
    variants = {raw}
    version = re.fullmatch(r"version\s*(\d+)", raw)
    if version:
        number = version.group(1)
        variants.update({f"version {number}", f"version{number}", f"version == {number}", f"version=={number}"})
    if raw in {"true", "false"}:
        variants.add(raw.title())
    return variants


def audit_behavior_witness(behavioral_contract, patch):
    corpus = "\n".join(str(content) for content in patch.values()).lower()
    target_values = behavioral_contract.get("named_target_values", [])
    preserved_values = behavioral_contract.get("named_preserved_values", [])

    def witnessed(value):
        return any(variant in corpus for variant in _normalized_variants(value))

    missing_target = [value for value in target_values if not witnessed(value)]
    missing_preserved = [value for value in preserved_values if not witnessed(value)]
    return {
        "named_target_values": target_values,
        "named_preserved_values": preserved_values,
        "missing_target_witnesses": missing_target,
        "missing_preservation_witnesses": missing_preserved,
        "behavior_witness_complete": not missing_target and not missing_preserved,
        "scope": "lexical witness only; does not prove semantic correctness",
    }


def require_behavior_witness(behavioral_contract, patch):
    report = audit_behavior_witness(behavioral_contract, patch)
    if not report["behavior_witness_complete"]:
        missing = [*report["missing_target_witnesses"], *report["missing_preservation_witnesses"]]
        raise ValueError(f"behavior witness incomplete: missing named state/value witnesses: {', '.join(missing)}")
    return report
