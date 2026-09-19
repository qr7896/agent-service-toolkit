from evals.v2_matched_retrieval_audit import n_tok
def test_tokens(): assert n_tok([{"content":"a(b)"}])>0
