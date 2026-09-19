from evals.v2_structural_noise_audit import metrics
def test_precision():
 p=[{"source":"structural","path":"src/a.py"},{"source":"structural","path":"test_a.py"}];m=metrics(p,{"src/a.py"});assert m["target_precision"]==.5 and m["source_precision"]==.5
