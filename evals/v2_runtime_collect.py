from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
from evals.evidence_controller import EvidenceController
from evals.evidence_policy import EvidenceBudget, EvidencePolicy
from evals.evidence_runtime import WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.v2_decision_log import DecisionJSONLWriter
from evals.v2_shadow_logger import V2ShadowDecisionLogger


def run_case(case: dict, root: Path, writer):
    task_id=case["task_id"]; workspace=root/task_id; workspace.mkdir(parents=True,exist_ok=True)
    for rel,content in case.get("files",{}).items():
        target=workspace/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(content,encoding="utf-8")
    logger=V2ShadowDecisionLogger(task_id,writer,{k:case[k] for k in ("split","cluster","source_commit") if k in case})
    controller=EvidenceController(WorkspaceRetrievalAdapter(SafeWorkspace(workspace)),EvidencePolicy(EvidenceBudget(max_actions=case.get("max_actions",3),max_cost=10,max_risk=10)),decision_logger=logger)
    plans=list(case["plans"])
    def planner(_state):
        return plans.pop(0) if plans else {"candidates":[],"requests":{},"utility":{}}
    result=controller.run(planner)
    return {"task_id":task_id,"trace":result["trace"],"records":logger.step}


def collect_cases(cases: list[dict], output: Path):
    if output.exists(): output.unlink()
    writer=DecisionJSONLWriter(output)
    with tempfile.TemporaryDirectory(prefix="v2-shadow-") as tmp:
        rows=[run_case(case,Path(tmp),writer) for case in cases]
    return {"tasks":len(rows),"records":sum(r["records"] for r in rows),"output":output.as_posix()}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--cases",type=Path,required=True); ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(); cases=json.loads(args.cases.read_text(encoding="utf-8")); print(json.dumps(collect_cases(cases,args.output),ensure_ascii=False))


if __name__=="__main__": main()
