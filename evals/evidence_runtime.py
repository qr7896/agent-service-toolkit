from dataclasses import asdict, dataclass

ACTION_COST = {"files": 1.0, "lexical": 1.1, "semantic": 1.2, "structural": 0.9}
ACTION_RISK = {"files": 0.2, "lexical": 0.3, "semantic": 0.2, "structural": 0.1}


@dataclass(frozen=True)
class EvidenceItem:
    path: str
    content: str
    source: str
    score: float = 0.0
    symbol: str | None = None
    relation_type: str | None = None
    depth: int | None = None
    origin: str | None = None

    @property
    def key(self):
        return (self.path, self.symbol, self.content)


class EvidenceLedger:
    def __init__(self):
        self.items = []
        self.actions = []

    def add(self, action, items):
        if action not in ACTION_COST:
            raise ValueError(f"unknown evidence action: {action}")
        items = list(items)
        previous = {item.key for item in self.items}
        new = [item for item in items if item.key not in previous]
        redundant = len(items) - len(new)
        self.items.extend(new)
        row = {
            "action": action,
            "returned": len(items),
            "new": len(new),
            "redundant": redundant,
            "redundancy": redundant / len(items) if items else 0.0,
            "cost": ACTION_COST[action],
            "risk": ACTION_RISK[action],
        }
        self.actions.append(row)
        return row

    def summary(self):
        return {
            "actions": list(self.actions),
            "action_count": len(self.actions),
            "unique_evidence": len(self.items),
            "total_cost": sum(x["cost"] for x in self.actions),
            "total_risk": sum(x["risk"] for x in self.actions),
            "mean_redundancy": sum(x["redundancy"] for x in self.actions) / len(self.actions)
            if self.actions
            else 0.0,
        }

    def payload(self):
        return [asdict(item) for item in self.items]


class WorkspaceRetrievalAdapter:
    def __init__(self, workspace, ledger=None, structural_adapter=None, semantic_adapter=None):
        self.workspace = workspace
        self.ledger = ledger or EvidenceLedger()
        self.structural_adapter = structural_adapter
        self.semantic_adapter = semantic_adapter

    def files(self):
        items = [
            EvidenceItem(path=p, content="", source="files") for p in self.workspace.list_files()
        ]
        self.ledger.add("files", items)
        return items

    def lexical(self, query, max_results=20):
        hits = self.workspace.search_text(query, max_results=max_results)
        items = [
            EvidenceItem(path=h["path"], content=h["text"], source="lexical", score=1.0)
            for h in hits
        ]
        self.ledger.add("lexical", items)
        return items

    def semantic(self, query, max_results=10):
        if self.semantic_adapter is None:
            raise NotImplementedError("semantic adapter not configured")
        items = self.semantic_adapter.search(query, max_results=max_results)
        self.ledger.add("semantic", items)
        return items

    def structural(self, query="", relation="symbols"):
        if self.structural_adapter is None:
            raise NotImplementedError("structural adapter not configured")
        method = getattr(self.structural_adapter, relation, None)
        if method is None:
            raise ValueError(f"unknown structural relation: {relation}")
        items = method(query)
        self.ledger.add("structural", items)
        return items

    def structural_traverse(self, seed, max_depth=2, max_nodes=20):
        if self.structural_adapter is None:
            raise NotImplementedError("structural adapter not configured")
        items = self.structural_adapter.traverse(seed, max_depth=max_depth, max_nodes=max_nodes)
        self.ledger.add("structural", items)
        return items

    def read(self, path):
        text = self.workspace.read_text(path)
        item = EvidenceItem(path=path, content=text, source="files")
        self.ledger.add("files", [item])
        return item
