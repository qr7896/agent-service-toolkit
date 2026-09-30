import evals.e1b_run_dev_live_v4 as base
from evals.e1b_editor_adapter_v6 import build_proposal_messages, build_review_messages
from evals.e1b_run_dev_live_v4 import *  # noqa: F403

RUN_ID = "e1b-r10-dev-v6"
MAX_OUTPUT_TOKENS = 550
EVIDENCE_PROTOCOL = "declared-seed-read-v5-deterministic-contract"
LEDGER_PATH = Path(".codex/e1b/r10-v6/provider_calls.jsonl")  # noqa: F405
RESULT_PATH = Path("evals/results/e1b_autonomous_dev_run_v6.json")  # noqa: F405
V4_EVIDENCE_FOR = base.evidence_for


def provider_config(task_id):
    return {
        "configurable": {
            "provider_ledger_path": str(LEDGER_PATH),
            "provider_run_id": RUN_ID,
            "provider_task_id": task_id,
            "provider_total_token_ceiling": TOKEN_BUDGET,  # noqa: F405
            "provider_task_token_ceiling": TASK_TOKEN_CEILING,  # noqa: F405
            "provider_max_calls_per_task": 2,
            "provider_max_output_tokens": MAX_OUTPUT_TOKENS,
            "provider_prompt_reserve_multiplier": PROMPT_RESERVE_MULTIPLIER,  # noqa: F405
            "provider_disable_thinking": True,
        }
    }


def evidence_for(task, root):
    payload = V4_EVIDENCE_FOR(task, root)
    payload["protocol"] = EVIDENCE_PROTOCOL
    return payload


def preflight():
    original = (
        base.RUN_ID,
        base.MAX_OUTPUT_TOKENS,
        base.EVIDENCE_PROTOCOL,
        base.LEDGER_PATH,
        base.RESULT_PATH,
        base.provider_config,
        base.evidence_for,
        base.build_proposal_messages,
        base.build_review_messages,
    )
    try:
        base.RUN_ID = RUN_ID
        base.MAX_OUTPUT_TOKENS = MAX_OUTPUT_TOKENS
        base.EVIDENCE_PROTOCOL = EVIDENCE_PROTOCOL
        base.LEDGER_PATH = LEDGER_PATH
        base.RESULT_PATH = RESULT_PATH
        base.provider_config = provider_config
        base.evidence_for = evidence_for
        base.build_proposal_messages = build_proposal_messages
        base.build_review_messages = build_review_messages
        report = base.preflight()
        report["protocol"] = "e1b-r10-deterministic-contract-dev-preflight-v1"
        report["result_exists"] = RESULT_PATH.exists()
        report["ledger_exists"] = LEDGER_PATH.exists()
        report["ready"] = report["ready"] and not report["result_exists"] and not report["ledger_exists"]
        return report
    finally:
        (
            base.RUN_ID,
            base.MAX_OUTPUT_TOKENS,
            base.EVIDENCE_PROTOCOL,
            base.LEDGER_PATH,
            base.RESULT_PATH,
            base.provider_config,
            base.evidence_for,
            base.build_proposal_messages,
            base.build_review_messages,
        ) = original


async def main():
    parser = argparse.ArgumentParser()  # noqa: F405
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), ensure_ascii=False, indent=2))  # noqa: F405
        return
    base.RUN_ID = RUN_ID
    base.MAX_OUTPUT_TOKENS = MAX_OUTPUT_TOKENS
    base.EVIDENCE_PROTOCOL = EVIDENCE_PROTOCOL
    base.LEDGER_PATH = LEDGER_PATH
    base.RESULT_PATH = RESULT_PATH
    base.provider_config = provider_config
    base.evidence_for = evidence_for
    base.build_proposal_messages = build_proposal_messages
    base.build_review_messages = build_review_messages
    await base.main()


if __name__ == "__main__":
    asyncio.run(main())  # noqa: F405
