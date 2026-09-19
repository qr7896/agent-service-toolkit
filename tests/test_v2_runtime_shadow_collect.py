import json
from evals.v2_runtime_shadow_collect import collect_shadow
def test_shadow_collection(tmp_path):
 cases=[{"task_id":"x","files":{"a.py":"def alpha(): pass"},"max_actions":1,"plans":[{"candidates":["files"],"requests":{},"utility":{"files":1}}]}]
 model=tmp_path/"m.json";model.write_text(json.dumps({"centroids":{"files":[0,0,0,0,0,0],"stop":[2,2,2,2,2,2]},"scales":[1]*6}))
 out=tmp_path/"o.jsonl";r=collect_shadow(cases,model,out);assert r["records"]>=1 and out.exists()
