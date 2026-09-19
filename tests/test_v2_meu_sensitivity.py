from evals.v2_meu_sensitivity import audit
def test_grid_reuses_meu():
 b={"rows":[{"action":"lexical","retained_proxy_tokens":10,"cost":2,"risk":1,"unique_gain":1},{"action":"structural","retained_proxy_tokens":2,"cost":1,"risk":1,"unique_gain":2}]}
 r=audit(b);assert r["grid_points"]==45 and 0<=r["structural_higher_fraction"]<=1
