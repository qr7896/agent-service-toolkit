from evals.v2_adaptive_compare import compare
def test_delta(): assert compare({"v1_resolved":4},{"tasks":10,"resolved":10})["resolved_delta"]==6
