from evals import e1c_evaluation_2_module_retrieval_dev as trial


def test_module_function_query_finds_real_production_function_not_class_owner(tmp_path):
    (tmp_path / 'utils.py').write_text('def parse(value):\n    return value\n')
    (tmp_path / 'other.py').write_text('def parse(value):\n    return value\n')
    rows, feedback = trial.retrieve('utils.parse', tmp_path)
    assert len(rows) == 1 and rows[0]['path'] == 'utils.py' and rows[0]['symbol'] == 'parse'
    assert not rows[0]['alias_binding_proven'] and not feedback['alias_binding_proven']
    assert feedback['matches'] == 1 and feedback['scan_bytes'] < 64 * 1024 * 1024


def test_class_method_retrieval_is_not_changed_and_test_files_are_excluded(tmp_path):
    (tmp_path / 'core.py').write_text('class Api:\n    def parse(self):\n        return 1\n')
    (tmp_path / 'test_utils.py').write_text('def parse(value):\n    return value\n')
    rows, feedback = trial.retrieve('Api.parse', tmp_path)
    assert len(rows) == 1 and rows[0]['path'] == 'core.py'
    assert 'fallback_plain_symbol' not in feedback
    assert trial.retrieve('utils.parse', tmp_path)[0] == []


def test_inner_retrieval_hook_budget_and_other_hooks_restored():
    compiled = trial.previous.previous.stage.pilot.previous.previous.method.base.base._compiled
    original = compiled.base.loop.retrieve
    with trial.configured(), compiled.configured():
        assert compiled.base.loop.retrieve is trial.retrieve
        assert compiled.base.loop.parse_action is trial.previous.previous.stage.pilot.parse_action
        assert compiled.CAP == 40000 and compiled.TASK_CAP == 24000
    assert compiled.base.loop.retrieve is original
