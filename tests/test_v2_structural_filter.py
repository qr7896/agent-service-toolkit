from evals.v2_structural_filter import select
def test_drops_test_callers():
 p=[{"source":"structural","path":"test_x.py","relation_type":"caller"},{"source":"structural","path":"src/x.py","relation_type":"definition"}];assert len(select(p))==1
