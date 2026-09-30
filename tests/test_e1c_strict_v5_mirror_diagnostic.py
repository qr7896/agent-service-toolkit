import pytest

from evals.e1c_strict_v5_mirror_diagnostic import mirror_image


def test_mirror_image_is_deterministic_and_keeps_double_underscore() -> None:
    assert mirror_image("pydata__xarray-3993") == (
        "ghcr.io/epoch-research/swe-bench.eval.x86_64.pydata__xarray-3993:latest"
    )


@pytest.mark.parametrize("value", ["bad", "../x__y", "x/y__z", "x__y:latest"])
def test_mirror_image_rejects_unsafe_ids(value: str) -> None:
    with pytest.raises(ValueError):
        mirror_image(value)
