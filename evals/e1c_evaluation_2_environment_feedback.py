"""Project matching own-executor environment records, never scorer material."""

from __future__ import annotations

import copy
import re

from evals.e1c_strict_v5_boundary import audit_repair_visible_payload


def project_environment(feedback, controls, target):
    value = copy.deepcopy(feedback)
    records = [*controls, target]
    if len(controls) != 2 or any(not isinstance(row, dict) for row in records):
        raise ValueError('two control records and target required')
    identity = ('schema', 'input_sha256', 'image', 'base_commit', 'missing_optional_import')
    if (target.get('schema') != 'e1c-evaluation-2-probe-execution-v1'
            or any(any(row.get(key) != target.get(key) for key in identity) for row in records)
            or any(row.get('network_none') is not True or row.get('pull_never') is not True for row in records)
            or any(not row.get('runs') or any(run.get('timed_out') is not False
                                            or run.get('returncode') not in (0, 1) for run in row['runs']) for row in records)):
        raise ValueError('matching valid offline executions required')
    module = target.get('missing_optional_import')
    if not isinstance(module, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', module):
        raise ValueError('explicit optional import condition required; none is not absence evidence')
    value['own_executor_environment'] = {
        'schema': 'e1c2-enforced-import-feedback-v1', 'module': module,
        'condition': 'executor_forced_import_failure_in_both_phases',
        'evidence_origin': 'matching_control_and_target_execution_records',
        'naturally_uninstalled_claimed': False, 'runtime_guard_value_observed': False,
        'semantic_alignment_proven': False, 'trusted_reproducer': False,
    }
    audit_repair_visible_payload(value)
    return value
