"""Pack retrieved evidence into a fixed approximate token budget."""

from __future__ import annotations

from dataclasses import dataclass, field


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


@dataclass(frozen=True)
class ContextItem:
    source: str
    text: str
    relevance: float = 1.0

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.text)


@dataclass
class PackedContext:
    items: list[ContextItem] = field(default_factory=list)
    tokens: int = 0
    dropped: int = 0

    def text(self, source: str) -> str:
        return "\n\n".join(item.text for item in self.items if item.source == source)


def blocks(source: str, text: str, relevance: float = 1.0) -> list[ContextItem]:
    return [ContextItem(source, part, relevance) for part in text.split("\n\n") if part.strip()]


def pack_context(items: list[ContextItem], budget: int) -> PackedContext:
    """Greedy relevance-per-token packing; truncate one item only if none fits."""
    budget = max(0, int(budget))
    ranked = sorted(items, key=lambda item: item.relevance / max(item.tokens, 1), reverse=True)
    selected: list[ContextItem] = []
    used = 0
    for item in ranked:
        if item.tokens <= budget - used:
            selected.append(item)
            used += item.tokens
    if not selected and ranked and budget:
        item = ranked[0]
        text = item.text[: budget * 4]
        selected = [ContextItem(item.source, text, item.relevance)]
        used = estimate_tokens(text)
    return PackedContext(selected, used, len(items) - len(selected))


__all__ = ["ContextItem", "PackedContext", "blocks", "estimate_tokens", "pack_context"]
