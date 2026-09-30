from evals.e1c_evaluation_2_unified_dev_v1 import prompt, quote, route


def test_public_only_route_and_prompt():
    constructor = {
        "issue": (
            "Expose option\n`pkg.module.Example` is relevant.\n"
            "expose `flag` in `Example.__init__()`, default `False`\n"
        ),
        "windows": [],
    }
    method, source = route(constructor)
    assert method == "deterministic_boolean_constructor"
    assert "Example(flag=True)" in source
    assert quote(constructor, method) in constructor["issue"]

    ordinary = {"issue": "Public API fails on a valid input.", "windows": []}
    assert route(ordinary) == ("model_public_issue", None)
    assert "manufacture the expected warning/error" in prompt(ordinary)
