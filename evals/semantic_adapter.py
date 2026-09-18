from agents.code_semantic import semantic_hits
from evals.evidence_runtime import EvidenceItem


class SemanticAdapter:
    def __init__(self, workspace, embedding_function=None):
        self.workspace = workspace
        self.embedding_function = embedding_function

    def search(self, query, max_results=10):
        ranked = semantic_hits(
            query,
            self.workspace.root,
            max_results,
            self.embedding_function,
            self.workspace,
        )
        return [
            EvidenceItem(
                path=chunk.path,
                content=chunk.text,
                source="semantic",
                score=score,
                symbol=chunk.symbol,
            )
            for score, chunk in ranked
        ]
