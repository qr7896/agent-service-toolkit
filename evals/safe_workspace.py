from pathlib import Path

PROTECTED = {".git", ".env", ".codex", "__pycache__"}
DEFAULT_MAX_READ_BYTES = 100_000


class SafeWorkspace:
    def __init__(
        self,
        root,
        max_read_bytes=DEFAULT_MAX_READ_BYTES,
        max_total_bytes=500_000,
        max_read_calls=50,
    ):
        self.root = Path(root).resolve()
        self.max_read_bytes = max_read_bytes
        self.max_total_bytes = max_total_bytes
        self.max_read_calls = max_read_calls
        self.events = []

    def _fail(self, code, rel, message, exc_type=PermissionError, **details):
        event = {
            "action": "workspace_error",
            "error_type": code,
            "path": str(rel).replace(chr(92), "/"),
            **details,
        }
        self.events.append(event)
        error = exc_type(message)
        error.event = event
        raise error

    def _target(self, rel):
        raw = str(rel).replace(chr(92), "/")
        if not raw or raw.startswith("/") or raw.startswith("../") or ":" in raw:
            self._fail("path_denied", rel, f"workspace escape blocked: {rel}")
        target = (self.root / raw).resolve()
        if target != self.root and self.root not in target.parents:
            self._fail("path_denied", rel, f"resolved workspace escape blocked: {rel}")
        parts = Path(raw).parts
        if any(part in PROTECTED for part in parts):
            self._fail("protected_path", rel, f"protected path blocked: {rel}")
        return target

    def list_files(self):
        rows = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root).as_posix()
            if any(part in PROTECTED for part in Path(rel).parts):
                continue
            rows.append(rel)
        rows.sort()
        self.events.append({"action": "list_files", "count": len(rows)})
        return rows

    def read_text(self, rel):
        target = self._target(rel)
        if not target.is_file():
            self._fail("not_found", rel, str(rel), FileNotFoundError)
        size = target.stat().st_size
        reads = [e for e in self.events if e["action"] == "read_text"]
        if len(reads) >= self.max_read_calls:
            self._fail(
                "read_call_budget_exceeded",
                rel,
                "read call budget exceeded",
                limit=self.max_read_calls,
                used=len(reads),
            )
        if sum(e["bytes"] for e in reads) + size > self.max_total_bytes:
            self._fail(
                "total_byte_budget_exceeded",
                rel,
                "total read byte budget exceeded",
                limit=self.max_total_bytes,
                used=sum(e["bytes"] for e in reads),
                requested=size,
            )
        if size > self.max_read_bytes:
            self._fail(
                "single_file_budget_exceeded",
                rel,
                f"read byte limit exceeded: {rel}",
                limit=self.max_read_bytes,
                requested=size,
            )
        text = target.read_text(encoding="utf-8")
        self.events.append(
            {"action": "read_text", "path": str(rel).replace(chr(92), "/"), "bytes": size}
        )
        return text

    def search_text(self, query, max_results=20):
        if not isinstance(query, str) or not query:
            raise ValueError("query must be non-empty")
        hits = []
        for rel in self.list_files():
            try:
                text = self.read_text(rel)
            except (UnicodeDecodeError, PermissionError):
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                if query.lower() in line.lower():
                    hits.append({"path": rel, "line": line_no, "text": line[:500]})
                    if len(hits) >= max_results:
                        self.events.append(
                            {"action": "search_text", "query": query, "results": len(hits)}
                        )
                        return hits
        self.events.append({"action": "search_text", "query": query, "results": len(hits)})
        return hits

    def evidence_summary(self):
        reads = [e for e in self.events if e["action"] == "read_text"]
        return {
            "events": list(self.events),
            "read_calls": len(reads),
            "bytes_read": sum(e["bytes"] for e in reads),
            "unique_files_read": len({e["path"] for e in reads}),
        }
