from __future__ import annotations
from typing import Any

def state_text(row:dict[str,Any])->str:
 parts=[]
 for key in ("issue","information_need","current_observation","current_hypothesis","current_subgoal"):
  value=row.get(key)
  if value: parts.append(f"{key}: {value}")
 return "\n".join(parts)

def to_external_state(row:dict[str,Any])->dict[str,Any]:
 if not row.get("state_id") or not row.get("repo") or not isinstance(row.get("candidate_evidence"),list):
  raise ValueError("SERBench inference row requires state_id, repo, candidate_evidence")
 return {"external_state_id":row["state_id"],"repository":row["repo"],"state_text":state_text(row),
  "candidate_evidence":row["candidate_evidence"],
  "metadata":{"instance_id":row.get("instance_id"),"opened_files":row.get("opened_files",[]),
   "search_queries":row.get("search_queries",[]),"observed_evidence_ids":row.get("observed_evidence_ids",[])}}

def prediction(state_id:str,method:str,ranked_evidence_ids:list[str])->dict[str,Any]:
 if not state_id or not method: raise ValueError("state_id and method required")
 if len(ranked_evidence_ids)!=len(set(ranked_evidence_ids)): raise ValueError("duplicate evidence ids")
 return {"state_id":state_id,"method":method,"ranked_evidence_ids":ranked_evidence_ids}
