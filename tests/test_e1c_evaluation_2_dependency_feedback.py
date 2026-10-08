import copy

from evals import e1c_evaluation_2_dependency_feedback as router


def feedback():
    return {'status': 'evidence_required_before_selection', 'scope_gate': {'bounded_source_requests': [], 'rejected': [], 'missing_evidence': ['existing']},
            'controller_verdict': {'status': 'unknown_or_rejected_dependency_evidence', 'trusted_reproducer': False,
                                   'program': {'rejected': [], 'unknown': ['unexposed_dependency_source_provenance_unknown'],
                                               'unexposed_dependency_bindings': [{'symbol': 'Schema'}]}}}


def test_pre_observer_program_missing_source_reaches_action_gate_without_upgrading():
    original = feedback()
    before = copy.deepcopy(original)
    result = router.route(original)
    assert original == before
    assert result['scope_gate']['bounded_source_requests'] == [{'retrieve': 'Schema'}]
    assert result['scope_gate']['action'] == 'ACQUIRE_EVIDENCE_OR_ABSTAIN'
    assert 'existing' in result['scope_gate']['missing_evidence']
    assert not result['scope_gate']['DEV_candidate_eligible'] and not result['scope_gate']['repair_eligible']


def test_existing_rejection_never_becomes_unknown_only():
    original = feedback()
    original['scope_gate']['rejected'] = ['changed source']
    result = router.route(original)
    assert result['status'] == 'action_rejected' and result['scope_gate']['action'] == 'REJECT'


def test_rejected_program_never_becomes_candidate():
    original = feedback()
    original['controller_verdict']['program']['rejected'] = ['alias shadowed']
    result = router.route(original)
    assert result['scope_gate']['action'] == 'REJECT' and not result['scope_gate']['DEV_candidate_eligible']


def test_already_qualified_or_unselected_feedback_is_unchanged():
    original = {'status': 'target_not_repeatable_failure', 'controller_verdict': {'status': 'execution_not_selected'}}
    assert router.route(original) == original
