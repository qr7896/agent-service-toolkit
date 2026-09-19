from evals.v2_logo_summary import summarize
def test_summary():
 x=summarize({"folds":[{"delta_pp":1},{"delta_pp":3}],"weighted_frequency":.5,"weighted_contextual":.6});assert x["delta_pp"]["median"]==2 and x["positive"]==2
