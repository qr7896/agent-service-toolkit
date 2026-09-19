from evals.serbench_candidate_ranker import rank_state

def test_candidate_only_and_deterministic():
 row={"state_id":"s","issue":"parser timeout","information_need":"caller","candidate_evidence":[
 {"evidence_id":"a","source_path":"x.py","content_excerpt":"unrelated"},
 {"evidence_id":"b","source_path":"parser.py","content_excerpt":"caller timeout"}]}
 out=rank_state(row,k=2)
 assert out["ranked_evidence_ids"]==["b","a"]
 assert set(out["ranked_evidence_ids"])=={"a","b"}
