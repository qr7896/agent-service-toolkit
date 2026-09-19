from evals.v2_structural_filter_coverage import score
def test_empty_replay(tmp_path):
 p=tmp_path/"t";p.write_text(""); # smoke only
