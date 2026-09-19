from evals.v2_downstream_oracle import oracle_edit
class S: gold_sources={"a.py":"fixed","b.py":"x"}
def test_oracle_only_writes_allowed(tmp_path):
 assert oracle_edit(S(),tmp_path,{"a.py"})==["a.py"] and not (tmp_path/"b.py").exists()
