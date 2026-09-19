from evals.v2_structural_filter_v2 import select
def test_keeps_non_test_caller_and_drops_test_caller():
 p=[{"source":"structural","path":"src/a.py","relation_type":"caller"},{"source":"structural","path":"test_a.py","relation_type":"caller"}]
 assert select(p)==[p[0]]
