import json
from pathlib import Path

from evals.v2_decision_schema import DecisionRecord


class DecisionJSONLWriter:
    """Append-only V2 decision logger. No model calls and no policy learning."""

    def __init__(self, path):
        self.path = Path(path)

    def append(self, record: DecisionRecord):
        payload = record.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return payload

    def read_all(self):
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
