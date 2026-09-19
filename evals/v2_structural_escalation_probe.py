from __future__ import annotations
import argparse,ast,json,re,tempfile
from pathlib import Path
from evals.codegraph_adapter import CodeGraphAdapter
from evals.safe_workspace import SafeWorkspace
from evals.swe_tasks import load_tasks
from evals.v2_grouped_robustness import source_problem_id

def visible_symbols(files):
 out=[]
 for path,text in files.items():
  if not path.endswith(".py"):continue
  try:tree=ast.parse(text)
  except SyntaxError:continue
  for n in ast.walk(tree):
   if isinstance(n,ast.Call):
    if isinstance(n.func,ast.Attribute):out.append(n.func.attr)
    elif isinstance(n.func,ast.Name):out.append(n.func.id)
 return list(dict.fromkeys(out))

def probe(cases,tasks_path):
 specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 with tempfile.TemporaryDirectory(prefix="v2-escalate-") as tmp:
  base=Path(tmp)
  for case in cases:
   spec=specs.get(source_problem_id(case["task_id"]))
   if not spec:continue
   root=base/source_problem_id(case["task_id"]);root.mkdir()
   for rel,c in case["files"].items():
    t=root/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(c,encoding="utf-8")
   cg=CodeGraphAdapter(SafeWorkspace(root));seeds=visible_symbols(case["files"]);ev=[]
   for s in seeds:ev.extend(cg.neighbors(s,origin="runtime-visible-test-symbol",depth=0))
   paths={x.path for x in ev};gold=set(spec.gold_files)
   rows.append({"task_id":case["task_id"],"runtime_seeds":seeds,"structural_paths":sorted(paths),"gold_hit":bool(paths&gold),"gold_paths_hit":sorted(paths&gold)})
 return {"protocol":"v2-runtime-observable-structural-escalation-probe-v1","tasks":len(rows),"gold_hit_tasks":sum(r["gold_hit"] for r in rows),"rows":rows,
  "claim_boundary":"Uses runtime-visible AST call symbols only; Gold is used solely after retrieval to score coverage."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--cases",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=probe(json.loads(a.cases.read_text(encoding="utf-8")),a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"tasks":r["tasks"],"gold_hit_tasks":r["gold_hit_tasks"]}))
if __name__=="__main__":main()
