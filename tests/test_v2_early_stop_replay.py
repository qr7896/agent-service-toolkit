from evals.v2_early_stop_replay import replay
def test_early_stop_never_adds_actions(tmp_path):
 cases=[{"task_id":"x","files":{"a.py":"alpha\n"},"max_actions":2,"plans":[{"candidates":["lexical","stop"],"requests":{"lexical":{"query":"alpha"}},"utility":{"lexical":1,"stop":0}},{"candidates":["lexical","stop"],"requests":{"lexical":{"query":"alpha"}},"utility":{"lexical":.6,"stop":0}}]}]
 model={"centroids":{"lexical":[0,0,0,0,0,0],"stop":[1,1,1,1,1,1]},"scales":[1]*6};x=replay(cases,model);assert x["aggregate"]["action_delta"]<=0
