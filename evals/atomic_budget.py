import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass(frozen=True)
class BudgetReservation:
    ceiling: int
    spent: int
    reserve: int

    @property
    def remaining(self) -> int:
        return max(0, self.ceiling - self.spent)

    @property
    def callable(self) -> bool:
        return self.reserve > 0 and self.reserve <= self.remaining


class AtomicBudgetGuard:
    """Fail-closed admission control for providers that report usage only after a call."""

    def __init__(self, ceiling: int, per_call_reserve: int):
        if ceiling < 0 or per_call_reserve <= 0:
            raise ValueError("ceiling must be >= 0 and per_call_reserve must be > 0")
        self.ceiling = ceiling
        self.per_call_reserve = per_call_reserve
        self.spent = 0

    def reservation(self) -> BudgetReservation:
        return BudgetReservation(self.ceiling, self.spent, self.per_call_reserve)

    def admit(self) -> bool:
        return self.reservation().callable

    def settle(self, actual_tokens: int) -> None:
        if actual_tokens < 0:
            raise ValueError("actual_tokens must be >= 0")
        self.spent += actual_tokens

    @property
    def overrun_tokens(self) -> int:
        return max(0, self.spent - self.ceiling)


async def invoke_with_timeout(
    invoke: Callable[[], Awaitable[Any]],
    timeout_seconds: float,
) -> Any:
    """Bound wall time independently from token accounting."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be > 0")
    return await asyncio.wait_for(invoke(), timeout=timeout_seconds)
