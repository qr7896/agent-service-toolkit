from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path
from evals.swe_tasks import load_tasks
from evals.v2_grouped_robustness import source_problem_id

def tokens(text):
 return {x.lower() for x in re.findall(r"[A-Za-z_][A-Za-z0-9_]*",text)}

def analyze(downstream,tasks_path):
 specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 for r in downstream["rows"]:
  if r["v1"]["resolved"]:continue
  spec=specs[r["instance_id"]];seen=set(r["v1"]["allowed_files"]);gold=set(spec.gold_files);missing=gold-seen
  test_text="\n".join(spec.test_files.values());setup_text="\n".join(spec.setup_files.values())
  gold_symbols=set(spec.gold_symbols);symbol_visible=bool(gold_symbols & tokens(test_text+"\n"+setup_text))
  if not seen:kind="empty_retrieval"
  elif missing and symbol_visible:kind="target_file_missed_despite_visible_symbol"
  elif missing:kind="target_file_missed_query_mismatch"
  else:kind="retrieved_target_but_not_editable"
  recommendation={"empty_retrieval":"files_then_structural","target_file_missed_despite_visible_symbol":"structural_symbol_traversal",
   "target_file_missed_query_mismatch":"files_then_symbol_extraction","retrieved_target_but_not_editable":"targeted_read"}[kind]
  rows.append({"task_id":r["task_id"],"failure_type":kind,"seen_files":sorted(seen),"missing_gold_files":sorted(missing),
    "gold_symbols":sorted(gold_symbols),"gold_symbol_runtime_visible":symbol_visible,"recommended_escalation":recommendation})
 return {"protocol":"v2-coverage-failure-taxonomy-v1","unresolved":len(rows),"counts":dict(Counter(x["failure_type"] for x in rows)),
  "recommendations":dict(Counter(x["recommended_escalation"] for x in rows)),"rows":rows,
  "claim_boundary":"Gold metadata is used only for retrospective failure diagnosis; recommendations are not runtime labels and must not leak into deployed policy state."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--downstream",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=analyze(json.loads(a.downstream.read_text(encoding="utf-8")),a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
