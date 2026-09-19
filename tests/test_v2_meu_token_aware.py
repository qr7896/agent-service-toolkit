from evals.v2_per_action_evidence_budget import toks
from evals.v2_meu_token_aware import calc
def test_proxy_and_meu():
 assert toks("a(b)")>0
 assert calc({"retained_proxy_tokens":10,"cost":1,"risk":0,"unique_gain":2},.1,1,1)==1
