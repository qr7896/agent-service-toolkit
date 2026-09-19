from __future__ import annotations
import argparse,ast,json,tempfile
from pathlib import Path
from evals.codegraph_adapter import CodeGraphAdapter
from evals.evidence_runtime import EvidenceLedger,WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.v2_structural_escalation_probe import visible_symbols

def source_paths(payload):
 return {x["path"] for x in payload if not Path(x["path"]).name.startswith("test_")}

def run(case):
 with tempfile.TemporaryDirectory(prefix="v2-adaptive-") as tmp:
  root=Path(tmp)
  for rel,c in case["files"].items():
   t=root/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(c,encoding="utf-8")
  ledger=EvidenceLedger();adapter=WorkspaceRetrievalAdapter(SafeWorkspace(root),ledger=ledger)
  first=case["plans"][0];q=first["requests"]["lexical"]["query"];adapter.lexical(q)
  decision="stop"
  # Runtime-observable sufficiency: lexical evidence containing non-test source file.
  if not source_paths(ledger.payload()):
   decision="structural"
   cg=CodeGraphAdapter(adapter.workspace);adapter.structural_adapter=cg
   seeds=visible_symbols(case["files"])
   seen=set();items=[]
   for seed in seeds:
    for item in cg.neighbors(seed,origin="runtime-visible-call",depth=0):
     if item.key not in seen:seen.add(item.key);items.append(item)
   ledger.add("structural",items)
  s=ledger.summary();s["evidence_payload"]=ledger.payload();s["adaptive_decision"]=decision;return s

def replay(cases):
 rows=[{"task_id":c["task_id"],"adaptive":run(c)} for c in cases]
 return {"protocol":"v2-adaptive-stop-escalate-replay-v1","tasks":len(rows),"rows":rows,
 "aggregate":{"actions":sum(r["adaptive"]["action_count"] for r in rows),"unique_evidence":sum(r["adaptive"]["unique_evidence"] for r in rows),
 "cost":round(sum(r["adaptive"]["total_cost"] for r in rows),4),"risk":round(sum(r["adaptive"]["total_risk"] for r in rows),4),
 "stops":sum(r["adaptive"]["adaptive_decision"]=="stop" for r in rows),"structural_escalations":sum(r["adaptive"]["adaptive_decision"]=="structural" for r in rows)},
 "claim_boundary":"Runtime-observable deterministic retrieval policy only; no Gold used in branch decisions."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--cases",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=replay(json.loads(a.cases.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r["aggregate"]))
if __name__=="__main__":main()
