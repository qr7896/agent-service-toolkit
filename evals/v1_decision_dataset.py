"""Build V1 decision episodes and oracle labels from the frozen V0 task set."""
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
from typing import Any
from evals.adaptive_retrieval_benchmark import BACKEND_COST, TASKS, _merge, backend_outputs, gold
from evals.retrieval_metrics import task_metrics
from evals.swe_tasks import load_tasks, prepare

ACTIONS=("files","lexical","semantic","structural")
V1_CLUSTER_SPLIT={"validation":"train","observability":"train","policy-gate":"train","input-normalization":"train","evidence-decision":"train","memory-quality":"dev","workflow-composition":"dev","sandbox-output":"test","durable-approval":"test"}
ACTION_RISK={"files":0.2,"lexical":0.3,"semantic":0.2,"structural":0.1}
LAMBDA_REDUNDANCY=0.15
LAMBDA_RISK=0.1
RUNTIME_FEATURES=("round","actions_tried","tokens_spent","cost_spent","artifact_files","artifact_symbols","artifact_tests","artifact_callers","candidate_cost","candidate_risk","candidate_output_files","candidate_output_symbols","candidate_output_tests","candidate_output_callers","candidate_output_tokens","candidate_new_files","candidate_new_symbols","candidate_new_tests","candidate_new_callers","candidate_redundancy")
GOLD_ONLY_FIELDS=("oracle_gain","oracle_value","oracle_best_action","stop_label","context_recall_before","context_recall_after")

def _counts(run: Any)->dict[str,int]:
    merged={k:set() for k in ("files","symbols","tests","callers")}
    for step in run.retrieval_trace:
        artifacts=step.get("artifacts") or {}
        for key in merged: merged[key].update(artifacts.get(key) or [])
    return {k:len(v) for k,v in merged.items()}

def _recall(run: Any,spec: Any)->float:
    return float(task_metrics(run.__dict__,gold(spec)).get("context_recall") or 0.0)

def _artifact_sets(run: Any)->dict[str,set[str]]:
    merged={k:set() for k in ("files","symbols","tests","callers")}
    for step in run.retrieval_trace:
        artifacts=step.get("artifacts") or {}
        for key in merged: merged[key].update(artifacts.get(key) or [])
    return merged

def _v1_split(spec: Any)->str:
    if spec.cluster not in V1_CLUSTER_SPLIT: raise ValueError(f"Unassigned V1 cluster: {spec.cluster}")
    return V1_CLUSTER_SPLIT[spec.cluster]

def build_episodes(tasks_path:Path=TASKS,budget:int=8000)->list[dict[str,Any]]:
    from agents.tools import get_embeddings
    tasks=load_tasks(tasks_path); embedding=get_embeddings(); episodes=[]
    with tempfile.TemporaryDirectory(prefix="retrieval-v1-") as temp:
        base=Path(temp)
        for spec in tasks:
            root=prepare(spec,base/spec.instance_id); outputs=backend_outputs(spec,root,embedding)
            tried=[]; current=_merge(outputs,tried,budget); before=_recall(current,spec); decision=0
            while True:
                counts=_counts(current); current_sets=_artifact_sets(current); candidates=[]
                for action in (a for a in ACTIONS if a not in tried):
                    after_run=_merge(outputs,[*tried,action],budget); after=_recall(after_run,spec); after_sets=_artifact_sets(after_run)
                    gain=max(0.0,after-before)
                    new_counts={k:len(after_sets[k]-current_sets[k]) for k in current_sets}; output_counts={k:len(after_sets[k]) for k in current_sets}
                    total_after=sum(output_counts.values()); total_new=sum(new_counts.values()); redundancy=0.0 if total_after==0 else 1.0-(total_new/total_after)
                    risk=ACTION_RISK[action]; value=gain/(BACKEND_COST[action]+0.1)-LAMBDA_REDUNDANCY*redundancy-LAMBDA_RISK*risk
                    features={"round":decision,"actions_tried":len(tried),"tokens_spent":current.estimated_tokens,"cost_spent":current.cost,"artifact_files":counts["files"],"artifact_symbols":counts["symbols"],"artifact_tests":counts["tests"],"artifact_callers":counts["callers"],"candidate_cost":BACKEND_COST[action],"candidate_risk":risk,"candidate_output_files":output_counts["files"],"candidate_output_symbols":output_counts["symbols"],"candidate_output_tests":output_counts["tests"],"candidate_output_callers":output_counts["callers"],"candidate_output_tokens":max(0,after_run.estimated_tokens-current.estimated_tokens),"candidate_new_files":new_counts["files"],"candidate_new_symbols":new_counts["symbols"],"candidate_new_tests":new_counts["tests"],"candidate_new_callers":new_counts["callers"],"candidate_redundancy":round(redundancy,6)}
                    candidates.append({"action":action,"features":features,"oracle_gain":round(gain,6),"oracle_value":round(value,6),"context_recall_after":round(after,6)})
                best=max(candidates,key=lambda r:(r["oracle_value"],r["oracle_gain"])) if candidates else None
                stop=best is None or best["oracle_value"]<=0.0
                episodes.append({"episode_id":f"{spec.instance_id}:{decision}","instance_id":spec.instance_id,"task_text":spec.problem_statement,"split":_v1_split(spec),"v0_split":spec.split,"cluster":spec.cluster,"source_commit":spec.source_commit,"decision":decision,"tried_actions":list(tried),"runtime_feature_names":list(RUNTIME_FEATURES),"candidates":candidates,"oracle_best_action":"" if stop else best["action"],"stop_label":stop,"context_recall_before":round(before,6)})
                if stop: break
                tried.append(best["action"]); current=_merge(outputs,tried,budget); before=_recall(current,spec); decision+=1
    return episodes

def validate_episodes(episodes:list[dict[str,Any]])->dict[str,Any]:
    leaked=sorted({key for ep in episodes for c in ep["candidates"] for key in c["features"] if key.startswith("gold_") or key in GOLD_ONLY_FIELDS})
    clusters={}; commits={}
    for ep in episodes:
        clusters.setdefault(ep["cluster"],set()).add(ep["split"])
        commit=ep.get("source_commit")
        if commit: commits.setdefault(commit,set()).add(ep["split"])
    cross=sorted(k for k,v in clusters.items() if len(v)>1); cross_commits=sorted(k for k,v in commits.items() if len(v)>1)
    return {"episodes":len(episodes),"tasks":len({e["instance_id"] for e in episodes}),"splits":{sp:len({e["instance_id"] for e in episodes if e["split"]==sp}) for sp in ("train","dev","test")},"runtime_gold_leakage":leaked,"cross_split_clusters":cross,"cross_split_commits":cross_commits,"stop_positive":sum(bool(e["stop_label"]) for e in episodes)}

def main()->None:
    parser=argparse.ArgumentParser(); parser.add_argument("--tasks",type=Path,default=TASKS); parser.add_argument("--output",type=Path,default=Path("evals/results/v1_decision_episodes.jsonl")); parser.add_argument("--summary",type=Path,default=Path("evals/results/v1_decision_dataset_summary.json")); parser.add_argument("--budget",type=int,default=8000); args=parser.parse_args()
    episodes=build_episodes(args.tasks,args.budget); summary=validate_episodes(episodes)
    if summary["runtime_gold_leakage"]: raise RuntimeError(f"Gold leakage: {summary['runtime_gold_leakage']}")
    if summary["cross_split_clusters"]: raise RuntimeError(f"Cluster leakage: {summary['cross_split_clusters']}")
    if summary["cross_split_commits"]: raise RuntimeError(f"Commit leakage: {summary['cross_split_commits']}")
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in episodes)+"\n",encoding="utf-8"); args.summary.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
