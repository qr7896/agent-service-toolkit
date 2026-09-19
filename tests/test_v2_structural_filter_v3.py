from evals.v2_structural_filter_v3 import is_test_path,select
def test_path_aware_test_detection():
 assert not is_test_path("src/agents/test_tools.py")
 assert is_test_path("test_research__x.py")
 p=[{"source":"structural","path":"src/agents/test_tools.py","relation_type":"caller"}];assert select(p)==p
