"""Train the V1 learned action ranker without exposing Gold fields at runtime."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import HashingVectorizer
from evals.v1_decision_dataset import ACTIONS, RUNTIME_FEATURES

ACTION_FEATURES=tuple(f"action_{a}" for a in ACTIONS)
PRE_ACTION_FEATURES=tuple(f for f in RUNTIME_FEATURES if not f.startswith("candidate_output_") and not f.startswith("candidate_new_") and f!="candidate_redundancy")
TEXT_DIM=32
TEXT_VECTORIZER=HashingVectorizer(n_features=TEXT_DIM,alternate_sign=False,norm=None)
FEATURE_SCHEMA=PRE_ACTION_FEATURES+ACTION_FEATURES+tuple(f"task_hash_{i}" for i in range(TEXT_DIM))

def _vector(candidate, task_text="", runtime_features=PRE_ACTION_FEATURES, include_text=True):
    f=candidate["features"]
    values=[float(f[k]) for k in runtime_features]+[1.0 if candidate["action"]==a else 0.0 for a in ACTIONS]
    if include_text: values.extend(TEXT_VECTORIZER.transform([task_text]).toarray()[0].tolist())
    return values

def load_rows(path, runtime_features=PRE_ACTION_FEATURES, include_text=True):
    episodes=[json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    rows=[]
    for ep in episodes:
        for c in ep["candidates"]:
            rows.append({"episode_id":ep["episode_id"],"split":ep["split"],"action":c["action"],"x":_vector(c,ep.get("task_text",ep.get("instance_id","")),runtime_features,include_text),"y":int(not ep["stop_label"] and c["action"]==ep["oracle_best_action"]),"stop":bool(ep["stop_label"])})
    return rows

def _fit_logreg(rows):
    train=[r for r in rows if r["split"]=="train"]; dev=[r for r in rows if r["split"]=="dev"]
    model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced",random_state=0)); model.fit(np.asarray([r["x"] for r in train]),np.asarray([r["y"] for r in train])); return evaluate(model,dev)

def ablations(path):
    groups={
        "full":PRE_ACTION_FEATURES,
        "no_cost":tuple(f for f in PRE_ACTION_FEATURES if f!="candidate_cost"),
        "no_risk":tuple(f for f in PRE_ACTION_FEATURES if f!="candidate_risk"),
        "state_only":tuple(f for f in PRE_ACTION_FEATURES if not f.startswith("candidate_")),
    }
    out={name:{"runtime_features":list(features),"include_text":True,"dev":_fit_logreg(load_rows(path,features,True))} for name,features in groups.items()}
    out["no_task_text"]={"runtime_features":list(PRE_ACTION_FEATURES),"include_text":False,"dev":_fit_logreg(load_rows(path,PRE_ACTION_FEATURES,False))}
    return out

def evaluate(model,rows):
    if not rows:return {"rows":0}
    x=np.asarray([r["x"] for r in rows]); y=np.asarray([r["y"] for r in rows]); p=model.predict_proba(x)[:,1]
    grouped={}
    for row,score in zip(rows,p): grouped.setdefault(row["episode_id"],[]).append((float(score),row["action"],row["y"]))
    actionable={eid:v for eid,v in grouped.items() if any(item[2] for item in v)}
    top1=(sum(max(v)[2] for v in actionable.values())/len(actionable)) if actionable else 0.0
    out={"rows":len(rows),"episodes":len(grouped),"actionable_episodes":len(actionable),"top1_oracle_action_accuracy":round(top1,6),"row_accuracy":round(float(accuracy_score(y,p>=0.5)),6)}
    if len(set(y))>1: out["auroc"]=round(float(roc_auc_score(y,p)),6)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--episodes",type=Path,default=Path("evals/results/v1_decision_episodes.jsonl")); ap.add_argument("--output-dir",type=Path,default=Path("evals/results")); args=ap.parse_args()
    rows=load_rows(args.episodes); train=[r for r in rows if r["split"]=="train"]; dev=[r for r in rows if r["split"]=="dev"]; test=[r for r in rows if r["split"]=="test"]
    x=np.asarray([r["x"] for r in train]); y=np.asarray([r["y"] for r in train])
    models={
        "logreg":make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced",random_state=0)),
        "small_mlp":make_pipeline(StandardScaler(),MLPClassifier(hidden_layer_sizes=(16,),max_iter=2000,early_stopping=False,random_state=0)),
    }
    args.output_dir.mkdir(parents=True,exist_ok=True); results={}
    for name,model in models.items():
        model.fit(x,y); results[name]={"train":evaluate(model,train),"dev":evaluate(model,dev)}; joblib.dump(model,args.output_dir/f"v1_{name}_ranker.joblib")
    winner=max(results,key=lambda n:(results[n]["dev"]["top1_oracle_action_accuracy"],results[n]["dev"].get("auroc",0.0)))
    report={"feature_schema":list(FEATURE_SCHEMA),"runtime_boundary":"pre_action_only; counterfactual candidate outputs excluded","gold_features":[],"models":results,"selected_on_dev":winner,"ablations":ablations(args.episodes),"lightgbm_status":"not_installed","test_status":"frozen_not_evaluated","test_rows":len(test)}
    (args.output_dir/"v1_ranker_metrics.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__":main()
