"""Fresh identity for the v3.1 agent loop after a TLS-connect ambiguous call."""

from evals import e1c_dev_v31 as runner
from evals.e1c_live_runner import OUT

runner.RUN_ID = "e1c-dev-v32-agentic23-20260924"
runner.RUN_DIR = OUT / runner.RUN_ID
runner.LEDGER = runner.RUN_DIR / "provider_calls.jsonl"


if __name__ == "__main__":
    runner.main()
