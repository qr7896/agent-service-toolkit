import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evals.v1_train_ranker import PRE_ACTION_FEATURES, TEXT_DIM, TEXT_VECTORIZER

STATE_FEATURES=tuple(f for f in PRE_ACTION_FEATURES if not f.startswith("candidate_"))
FEATURE_SCHEMA=STATE_FEATURES+tuple(f"task_hash_{i}" for i in range(TEXT_DIM))

def vector(ep):
    if not ep["candidates"]:
        base=[0.0 for _ in STATE_FEATURES]
    else:
        f=ep["candidates"][0]["features"]
        base=[float(f[k]) for k in STATE_FEATURES]
    return base+TEXT_VECTORIZER.transform([ep.get("task_text",ep.get("instance_id",""))]).toarray()[0].tolist()

def load_rows(path):
    eps=[json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    return [{"episode_id":e["episode_id"],"split":e["split"],"x":vector(e),"y":int(e["stop_label"])} for e in eps]

def ece(y,p,bins=5):
    edges=np.linspace(0.0,1.0,bins+1); value=0.0
    for lo,hi in zip(edges[:-1],edges[1:]):
        mask=(p>=lo)&((p<hi) if hi<1.0 else (p<=hi))
        if mask.any(): value+=mask.mean()*abs(float(y[mask].mean())-float(p[mask].mean()))
    return float(value)

def choose_threshold(model,rows):
    x=np.asarray([r["x"] for r in rows]); y=np.asarray([r["y"] for r in rows]); p=model.predict_proba(x)[:,1]
    candidates=sorted(set([0.5,*p.tolist()])); scored=[]
    for threshold in candidates:
        pred=p>=threshold; false_stop=int(((pred==1)&(y==0)).sum()); missed_stop=int(((pred==0)&(y==1)).sum())
        scored.append((2*false_stop+missed_stop,-float(threshold),float(threshold)))
    return min(scored)[2]

def evaluate(model,rows,threshold=0.5):
    x=np.asarray([r["x"] for r in rows]); y=np.asarray([r["y"] for r in rows]); p=model.predict_proba(x)[:,1]
    out={"episodes":len(rows),"stop_rate":round(float(y.mean()),6),"accuracy":round(float(accuracy_score(y,p>=threshold)),6),"auprc":round(float(average_precision_score(y,p)),6),"brier":round(float(brier_score_loss(y,p)),6),"ece_5bin":round(ece(y,p),6)}
    out["auroc"]=round(float(roc_auc_score(y,p)),6) if len(set(y))>1 else None
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--episodes",type=Path,default=Path("evals/results/v1_decision_episodes.jsonl")); ap.add_argument("--output-dir",type=Path,default=Path("evals/results")); args=ap.parse_args()
    rows=load_rows(args.episodes); train=[r for r in rows if r["split"]=="train"]; dev=[r for r in rows if r["split"]=="dev"]; test=[r for r in rows if r["split"]=="test"]
    model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000,class_weight="balanced",random_state=0)); model.fit(np.asarray([r["x"] for r in train]),np.asarray([r["y"] for r in train]))
    threshold=choose_threshold(model,dev)
    report={"feature_schema":list(FEATURE_SCHEMA),"runtime_boundary":"state before next retrieval action","train":evaluate(model,train,threshold),"dev":evaluate(model,dev,threshold),"threshold":round(threshold,6),"threshold_objective":"minimize 2*false_stop + missed_stop on dev; false STOP is safety-weighted","calibration_status":"probability calibration reported via Brier/ECE; no posthoc calibrator due small dev","test_status":"frozen_not_evaluated","test_episodes":len(test)}
    args.output_dir.mkdir(parents=True,exist_ok=True); joblib.dump(model,args.output_dir/"v1_logreg_stopper.joblib"); (args.output_dir/"v1_stopper_metrics.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))

if __name__=="__main__": main()
