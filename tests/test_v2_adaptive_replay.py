from evals.v2_adaptive_replay import source_paths
def test_source_paths_excludes_test_files():
 assert source_paths([{"path":"test_x.py"},{"path":"src/x.py"}])=={"src/x.py"}
