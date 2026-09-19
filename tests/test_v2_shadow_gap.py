import json
from evals.v2_shadow_gap import analyze
def test_gap_counts(tmp_path):
 p=tmp_path/"x";p.write_text("\n".join([json.dumps({"executed_action":"files","shadow_action":"files","agreement":True,"step":0}),json.dumps({"executed_action":"stop","shadow_action":"files","agreement":False,"step":1})]))
 x=analyze(p);assert x["disagreements"]==1 and x["pair_counts"]["stop->files"]==1
