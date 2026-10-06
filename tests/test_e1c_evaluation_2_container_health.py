import json
from types import SimpleNamespace

import pytest

from evals.e1c_evaluation_2_container_health import (
    ContainerInfrastructureUnavailable,
    is_transport_failure,
    require_engine,
    require_valid_execution_files,
)


def test_docker_pipe_error_is_not_repeatable_software_failure(tmp_path):
    row = {"runs": [{"returncode": 1, "log_tail": "failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine"}]}
    assert is_transport_failure(row)
    (tmp_path / "control_execution.json").write_bytes(json.dumps({"runs": [row, row]}).encode())
    with pytest.raises(ContainerInfrastructureUnavailable):
        require_valid_execution_files(tmp_path)
    assert not is_transport_failure({"runs": [{"returncode": 1, "log_tail": "Traceback: ValueError bad input"}]})


def test_engine_missing_stops_before_any_provider(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="pipe unavailable"))
    with pytest.raises(ContainerInfrastructureUnavailable):
        require_engine(("sha256:image",))
