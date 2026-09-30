"""Select a new strict-v9 metadata-only canary after mechanism freeze."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from evals.e1c_admission import ROOT
OUT=ROOT/"data/e1c_strict_v9_canary_manifest.json"; PREREG=ROOT/"data/e1c_strict_v9_prereg.json"; BOUNDARY=ROOT/"data/e1c_strict_v9_selection_boundary.json"; SALT="e1c-strict-v9-independent-canary"; REQUIRED=("instance_id","repo","base_commit","image")
def freeze(rows,*,source_revision,output=OUT):
 p=json.loads(PREREG.read_text(encoding="utf-8")); b=json.loads(BOUNDARY.read_text(encoding="utf-8")); touched=set(b["explicit_prior_canary_exclusions"]); ranked=[]
 for row in rows:
  if isinstance(row,dict) and set(row)==set(REQUIRED) and all(isinstance(row.get(k),str) and row[k] for k in REQUIRED) and len(row["base_commit"])==40 and row["instance_id"] not in touched:
   ranked.append((hashlib.sha256(f"{SALT}|{row['instance_id']}".encode()).hexdigest(),{k:row[k] for k in REQUIRED}))
 ranked.sort(); selected=[]; seen=set()
 for _,r in ranked:
  if r["instance_id"] in seen: continue
  seen.add(r["instance_id"]); selected.append(r)
  if len(selected)==3: break
 if len(selected)!=3: raise ValueError("need 3 untouched strict-v9 identities")
 v={"schema":"e1c-strict-v9-external-canary-reserve-v1","source":"official_swebench_task_repo_task_yaml","source_revision":source_revision,"identity_frozen_before_statement_materialization":True,"selection_salt":SALT,"mechanism_prereg_sha256":p["prereg_sha256"],"tasks":selected,"provider_calls":0,"task_content_inspected":False}; encoded=json.dumps(v,ensure_ascii=False,indent=2)+"\n"; output.write_text(encoded,encoding="utf-8"); return {"instance_ids":[x["instance_id"] for x in selected],"manifest_sha256":hashlib.sha256(encoded.encode()).hexdigest(),"provider_calls":0}
