import ast

from evals.evidence_runtime import EvidenceItem


class CodeGraphAdapter:
    def __init__(self, workspace):
        self.workspace = workspace

    def _python_files(self):
        return [p for p in self.workspace.list_files() if p.endswith(".py")]

    def symbols(self, query="", *, origin=None, depth=0):
        out = []
        q = query.lower()
        for path in self._python_files():
            try:
                text = self.workspace.read_text(path)
                tree = ast.parse(text)
            except (SyntaxError, UnicodeDecodeError, PermissionError):
                continue
            lines = text.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if q and q not in node.name.lower():
                        continue
                    snippet = lines[node.lineno - 1] if node.lineno <= len(lines) else node.name
                    out.append(
                        EvidenceItem(
                            path,
                            snippet,
                            "structural",
                            1.0,
                            node.name,
                            "definition",
                            depth,
                            origin or query or node.name,
                        )
                    )
        return out

    def imports(self, query="", *, origin=None, depth=0):
        out = []
        q = query.lower()
        for path in self._python_files():
            try:
                tree = ast.parse(self.workspace.read_text(path))
            except (SyntaxError, UnicodeDecodeError, PermissionError):
                continue
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    base = node.module or ""
                    names = [base + "." + a.name if base else a.name for a in node.names]
                for name in names:
                    if not q or q in name.lower():
                        out.append(
                            EvidenceItem(
                                path,
                                name,
                                "structural",
                                1.0,
                                name,
                                "import",
                                depth,
                                origin or query or name,
                            )
                        )
        return out

    def callers(self, symbol, *, origin=None, depth=0):
        out = []
        for path in self._python_files():
            try:
                text = self.workspace.read_text(path)
                tree = ast.parse(text)
            except (SyntaxError, UnicodeDecodeError, PermissionError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name == symbol:
                    out.append(
                        EvidenceItem(
                            path,
                            f"call:{symbol}@{node.lineno}",
                            "structural",
                            1.0,
                            symbol,
                            "caller",
                            depth,
                            origin or symbol,
                        )
                    )
        return out

    def neighbors(self, symbol, *, origin=None, depth=0):
        items = []
        items.extend(self.symbols(symbol, origin=origin, depth=depth))
        items.extend(self.callers(symbol, origin=origin, depth=depth))
        items.extend(self.imports(symbol, origin=origin, depth=depth))
        seen = set()
        out = []
        for item in items:
            if item.key not in seen:
                seen.add(item.key)
                out.append(item)
        return out

    def traverse(self, seed, max_depth=2, max_nodes=20):
        if max_depth < 0 or max_nodes < 1:
            raise ValueError("invalid traversal budget")
        frontier = [(seed, 0)]
        expanded = set()
        out = []
        seen_items = set()
        while frontier and len(out) < max_nodes:
            symbol, depth = frontier.pop(0)
            if symbol in expanded or depth > max_depth:
                continue
            expanded.add(symbol)
            for item in self.neighbors(symbol, origin=seed, depth=depth):
                if item.key not in seen_items:
                    seen_items.add(item.key)
                    out.append(item)
                    if len(out) >= max_nodes:
                        break
                if depth < max_depth and item.symbol and item.symbol not in expanded:
                    frontier.append((item.symbol, depth + 1))
        return out
