from evals import e1c_evaluation_2_patch_probe_zero as probe


def test_patch_command_writes_only_disposable_container_and_keeps_public_probe(monkeypatch, tmp_path):
    def original(*args, **kwargs):
        return ['docker', 'run', '--rm', '--network', 'none', '--pull=never', '--read-only',
                '--cap-drop', 'ALL', '--name', 'owned-probe', 'image', 'sh', '-c',
                'identity || exit 90; cd /testbed; python /e1c2_probe.py', 'e1c2', 'base']

    monkeypatch.setattr(probe, 'docker_command', original)
    command = probe.patch_command({}, 'image', 'base', tmp_path / 'probe.py', tmp_path / 'patch.diff', None)
    assert '--read-only' not in command
    assert '--pull=never' in command and command[command.index('--network') + 1] == 'none'
    assert any('target=/candidate.patch,readonly' in value for value in command)
    script = command[command.index('-c') + 1]
    assert script.startswith('identity || exit 90;')
    assert 'git apply --check' in script and 'python /e1c2_probe.py' in script
    assert '/admission' not in script and 'gold' not in script
