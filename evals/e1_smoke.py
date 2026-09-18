import argparse
import json
import tempfile
import time
from pathlib import Path

from evals.protocol_paths import TASKS, V0_MATCHED, V1_CLUSTER_SPLIT, V1_REPLAY
from evals.swe_tasks import grade, load_tasks, prepare

OUTCOMES = ("invalid_base", "retrieval_blocked", "patch_failure", "regression_failure", "resolved")


def split(s):
    return V1_CLUSTER_SPLIT[s.cluster]


def retrieved_files(r):
    return {
        x for step in r["retrieval_trace"] for x in (step.get("artifacts") or {}).get("files", [])
    }


def file_diagnostics(s, e):
    g = set(s.gold_sources)
    f = g & set(e)
    i = set(e) - g
    return {
        "required_gold_files": sorted(g),
        "retrieved_gold_files": sorted(f),
        "missing_gold_files": sorted(g - f),
        "irrelevant_files": sorted(i),
        "retrieved_files_count": len(e),
        "irrelevant_read_ratio": len(i) / len(e) if e else 0.0,
    }


def all_passed(n):
    return bool(n) and all(n.values())


def classify_failure(b, f, m, w):
    if b["resolved"]:
        return "invalid_base"
    if f["resolved"]:
        return "resolved"
    if m or not w:
        return "retrieval_blocked"
    if not all_passed(f["fail_to_pass"]):
        return "patch_failure"
    return "regression_failure"


def apply_gold_patch(s, r, a):
    w = []
    for rel, c in s.gold_sources.items():
        if rel in a:
            t = r / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(c, encoding="utf-8")
            w.append(rel)
    return w


def summarize(rows, p):
    rs = [r for r in rows if r["policy"] == p]
    n = len(rs)
    return {
        "tasks": n,
        "oracle_pass_at_1": sum(r["resolved"] for r in rs) / n,
        "sufficient_evidence_rate": sum(r["resolved"] for r in rs) / n,
        "avg_tool_calls": sum(r["tool_calls"] for r in rs) / n,
        "avg_context_tokens": sum(r["context_tokens"] for r in rs) / n,
        "avg_retrieved_files": sum(r["retrieved_files_count"] for r in rs) / n,
        "avg_irrelevant_read_ratio": sum(r["irrelevant_read_ratio"] for r in rs) / n,
        "retrieval_blocked_rate": sum(r["failure_type"] == "retrieval_blocked" for r in rs) / n,
        "outcomes": {k: sum(r["failure_type"] == k for r in rs) for k in OUTCOMES},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--budget", type=int, default=8000)
    ap.add_argument("--cached-retrieval", type=Path, default=V1_REPLAY)
    ap.add_argument("--cached-baseline", type=Path, default=V0_MATCHED)
    ap.add_argument(
        "--output", type=Path, default=Path("evals/results/e1_smoke_oracle_editor.json")
    )
    a = ap.parse_args()
    selected = [t for t in load_tasks(TASKS) if split(t) == "test"][: a.limit]
    v1 = json.loads(a.cached_retrieval.read_text())
    v0 = json.loads(a.cached_baseline.read_text())["utility_gate_groupaware"]
    cache = {
        "v1_frozen": {r["instance_id"]: r for r in v1["rows"]},
        "v0_groupaware": {r["instance_id"]: r for r in v0["rows"]},
    }
    rows = []
    with tempfile.TemporaryDirectory(prefix="e1-smoke-") as d:
        base = Path(d)
        for spec in selected:
            for policy in cache:
                root = base / f"{policy}-{spec.instance_id}"
                prepare(spec, root)
                bg = grade(spec, root)
                st = time.perf_counter()
                ret = cache[policy][spec.instance_id]
                acts = [x["action"] for x in ret["retrieval_trace"]]
                ev = retrieved_files(ret)
                diag = file_diagnostics(spec, ev)
                w = apply_gold_patch(spec, root, ev)
                fg = grade(spec, root)
                ft = classify_failure(bg, fg, diag["missing_gold_files"], w)
                rows.append(
                    {
                        "instance_id": spec.instance_id,
                        "policy": policy,
                        "resolved": fg["resolved"],
                        "failure_type": ft,
                        "actions": acts,
                        "tool_calls": len(acts),
                        "context_tokens": ret["estimated_tokens"],
                        "patch_files_written": w,
                        "wall_time_ms": round((time.perf_counter() - st) * 1000, 3),
                        "base_grade": bg,
                        "final_grade": fg,
                        "f2p_passed": sum(fg["fail_to_pass"].values()),
                        "f2p_count": len(fg["fail_to_pass"]),
                        "p2p_passed": sum(fg["pass_to_pass"].values()),
                        "p2p_count": len(fg["pass_to_pass"]),
                        **diag,
                    }
                )
    report = {
        "protocol": "E1 retrieval-to-patch smoke with constrained Oracle Editor",
        "scope": "retrieval-policy-to-editability upper bound; not autonomous Coding Agent success",
        "tasks": len(selected),
        "budget": a.budget,
        "summaries": {p: summarize(rows, p) for p in cache},
        "rows": rows,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summaries"], indent=2))


if __name__ == "__main__":
    main()
