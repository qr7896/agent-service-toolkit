from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from evals.codegraph_adapter import CodeGraphAdapter
from evals.evidence_runtime import EvidenceLedger,WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.v2_structural_escalation_probe import visible_symbols
from evals.v2_structural_filter_v3 import select

def _write(root,files):
 for rel,c in files.items():
  t=root/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(c,encoding="utf-8")

def _lexical(case,root):
 ledger=EvidenceLedger();a=WorkspaceRetrievalAdapter(SafeWorkspace(root),ledger=ledger)
 q=case["plans"][0]["requests"]["lexical"]["query"];a.lexical(q);a.lexical(q)
 return ledger.summary(),ledger.payload()

def _structural(case,root):
 ledger=EvidenceLedger();a=WorkspaceRetrievalAdapter(SafeWorkspace(root),ledger=ledger)
 cg=CodeGraphAdapter(a.workspace);seen=set();items=[]
 for seed in visible_symbols(case["files"]):
  for item in cg.neighbors(seed,origin="matched-state-runtime-visible-call",depth=0):
   if item.key not in seen:seen.add(item.key);items.append(item)
 ledger.add("structural",items)
 raw=ledger.payload();kept=select(raw)
 return ledger.summary(),raw,kept

def run(case):
 with tempfile.TemporaryDirectory(prefix="v2-matched-") as tmp:
  root=Path(tmp);_write(root,case["files"])
  # Same initial observable state: no prior evidence. Each arm gets one two-action
  # budget. Structural arm executes the same runtime-visible symbol traversal twice.
  ls,lp=_lexical(case,root);ss,sp,kept=_structural(case,root)
  # Repeat structural once to make action budget matched at 2.
  ledger=EvidenceLedger();a=WorkspaceRetrievalAdapter(SafeWorkspace(root),ledger=ledger);cg=CodeGraphAdapter(a.workspace)
  seeds=visible_symbols(case["files"])
  for _ in range(2):
   seen=set();items=[]
   for seed in seeds:
    for item in cg.neighbors(seed,origin="matched-state-runtime-visible-call",depth=0):
     if item.key not in seen:seen.add(item.key);items.append(item)
   ledger.add("structural",items)
  ss=ledger.summary();sp=ledger.payload();kept=select(sp)
  return {"task_id":case["task_id"],
   "lexical":{"summary":ls,"evidence_payload":lp},
   "structural":{"summary":ss,"evidence_payload":sp,"retained_payload":kept}}

def replay(cases):
 rows=[run(c) for c in cases]
 return {"protocol":"v2-matched-state-budget-retrieval-v1","tasks":len(rows),"action_budget_per_arm":2,"rows":rows,
 "claim_boundary":"Offline matched initial-state/two-action retrieval diagnostic. No Gold, editor, or runtime policy decision; not causal modality superiority."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--cases",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=replay(json.loads(a.cases.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"tasks":r["tasks"]}))
if __name__=="__main__":main()
