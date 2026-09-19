from evals.v2_marginal_evidence_utility import meu
def test_meu():
 assert meu(2,0,1,1,0,1,1)==1
 assert meu(0,0,1,1,0,1,1)==0
