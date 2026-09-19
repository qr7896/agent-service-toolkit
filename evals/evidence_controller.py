class EvidenceController:
    def __init__(self, adapter, policy, decision_logger=None):
        self.adapter = adapter
        self.policy = policy
        self.decision_logger = decision_logger
        self.trace = []

    def execute(self, action, request):
        if action == "files":
            return self.adapter.files()
        if action == "lexical":
            return self.adapter.lexical(request.get("query", ""), request.get("max_results", 20))
        if action == "read":
            return [self.adapter.read(request["path"])]
        if action == "structural" and "seed" in request:
            return self.adapter.structural_traverse(
                request["seed"],
                request.get("max_depth", 2),
                request.get("max_nodes", 20),
            )
        method = getattr(self.adapter, action, None)
        if method is None:
            raise NotImplementedError(f"evidence action not implemented: {action}")
        return method(**request)

    def step(self, candidates, requests=None, utility=None):
        requests = requests or {}
        action = self.policy.choose(self.adapter.ledger, candidates, utility)
        before = self.policy.state(self.adapter.ledger)
        if self.decision_logger is not None:
            self.decision_logger.record(
                before=before,
                candidates=candidates,
                chosen_action=action,
                utility=utility or {},
            )
        if action == "stop":
            row = {
                "action": "stop",
                "reason": "policy_stop",
                "before": before,
                "after": before,
                "items": 0,
            }
            self.trace.append(row)
            return row
        try:
            items = self.execute(action, requests.get(action, {}))
            after = self.policy.state(self.adapter.ledger)
            row = {
                "action": action,
                "reason": "executed",
                "before": before,
                "after": after,
                "items": len(items),
            }
        except Exception as exc:
            row = {
                "action": action,
                "reason": "execution_error",
                "error": type(exc).__name__,
                "message": str(exc),
                "before": before,
                "after": self.policy.state(self.adapter.ledger),
                "items": 0,
            }
        self.trace.append(row)
        return row

    def run(self, planner, max_steps=None):
        max_steps = max_steps or self.policy.budget.max_actions + 1
        for _ in range(max_steps):
            decision = planner(self.snapshot())
            row = self.step(
                decision.get("candidates", []),
                decision.get("requests", {}),
                decision.get("utility", {}),
            )
            if row["action"] == "stop" or row["reason"] == "execution_error":
                break
        return self.snapshot()

    def snapshot(self):
        return {
            "policy": self.policy.state(self.adapter.ledger),
            "evidence": self.adapter.ledger.payload(),
            "trace": list(self.trace),
        }
