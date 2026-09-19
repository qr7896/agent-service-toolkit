import asyncio

import pytest

from evals.atomic_budget import AtomicBudgetGuard, invoke_with_timeout


def test_guard_refuses_call_when_reserve_exceeds_remaining_budget():
    guard = AtomicBudgetGuard(ceiling=5000, per_call_reserve=5000)
    guard.settle(1)
    assert guard.reservation().remaining == 4999
    assert guard.admit() is False


def test_guard_allows_call_when_full_reserve_is_available():
    guard = AtomicBudgetGuard(ceiling=5000, per_call_reserve=5000)
    assert guard.admit() is True


def test_settlement_reports_provider_overrun_without_hiding_it():
    guard = AtomicBudgetGuard(ceiling=5000, per_call_reserve=5000)
    guard.settle(22860)
    assert guard.overrun_tokens == 17860
    assert guard.admit() is False


def test_invalid_budget_configuration_is_rejected():
    with pytest.raises(ValueError):
        AtomicBudgetGuard(ceiling=100, per_call_reserve=0)


def test_wall_timeout_is_independent_of_token_guard():
    async def slow():
        await asyncio.sleep(0.05)
        return "late"

    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(invoke_with_timeout(slow, timeout_seconds=0.001))
