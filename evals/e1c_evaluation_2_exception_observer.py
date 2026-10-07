"""Zero-model exception observations, not semantic or adversarial attestation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from unittest.mock import patch

from evals import e1c_evaluation_2_guard_type_observer as transport

_validate_driver, _docker_command = transport.build_driver, transport.docker_command
DRIVER = '''import hashlib, json, runpy, sys
if hashlib.sha256(open('/e1c2_model_probe.py', 'rb').read()).hexdigest() != DATA['probe_sha256']:
    raise RuntimeError('model probe source changed')
for site in DATA['sites']:
    if hashlib.sha256(open('/testbed/' + site['path'], 'rb').read()).hexdigest() != site['source_sha256']:
        raise RuntimeError('observed production source changed')
known = [(TypeError, 'builtins.TypeError'), (AttributeError, 'builtins.AttributeError'),
    (ValueError, 'builtins.ValueError'), (AssertionError, 'builtins.AssertionError')]
records = []
seen = set()
def trace(frame, event, arg):
    if event == 'exception' and len(records) < 8:
        tag = next((name for cls, name in known if arg[0] is cls), None)
        if tag is not None:
            args = arg[1].args
            if type(args) is tuple and len(args) == 1 and type(args[0]) is str:
                message = args[0]
                digest = hashlib.sha256(message.encode()).hexdigest()
                path = frame.f_code.co_filename
                selected = any(path == '/testbed/' + s['path'] for s in DATA['sites'])
                public_match = selected and digest in DATA['public_hashes']
                keyword = next((k for k in DATA['keywords'] if tag == 'builtins.TypeError'
                    and path == '/e1c2_model_probe.py' and "unexpected keyword argument '" + k + "'" in message), None)
                identity = (path, frame.f_lineno, digest)
                if (public_match or keyword is not None) and identity not in seen:
                    seen.add(identity)
                    records.append({'scope': 'selected_production' if selected else 'owned_probe',
                        'path': path.removeprefix('/testbed/'), 'line': frame.f_lineno,
                        'exception_type': tag, 'message_sha256': digest,
                        'matches_public_message': public_match, 'declared_missing_keyword': keyword})
    return trace
sys.settrace(trace)
try:
    runpy.run_path('/e1c2_model_probe.py', run_name='__main__')
finally:
    sys.settrace(None)
    print(DATA['marker'] + json.dumps({'schema': 'e1c2-source-bound-exception-observation-v1',
        'records': records, 'argument_values_emitted': False, 'raw_messages_emitted': False,
        'exception_observer_module_sha256': DATA['module_sha256'], 'semantic_alignment_proven': False}))
'''


def public_message_hashes(issue):
    messages = re.findall(r"^[\w.]+(?:Error|Exception):\s*(.+)$", issue, re.M)
    messages += re.findall(r"\bfailing\s+with\s+(?:a\s+)?`([^`]+)`", issue, re.I)
    return sorted({hashlib.sha256(m.strip().encode()).hexdigest() for m in messages if 8 <= len(m.strip()) <= 512})[:8]


def build_driver(probe_sha, sites, nonce, hashes, keywords):
    _, marker = _validate_driver(probe_sha, sites, nonce)
    if len(hashes) > 8 or any(not re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes):
        raise ValueError("bounded public message hashes required")
    if len(keywords) > 4 or any(not re.fullmatch(r"[A-Za-z_]\w{0,99}", k) or k.startswith("__") for k in keywords):
        raise ValueError("bounded public keyword claims required")
    data = {"probe_sha256": probe_sha, "sites": sites, "marker": marker, "public_hashes": hashes,
            "keywords": keywords, "module_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    return "import json\nDATA = json.loads(" + repr(json.dumps(data)) + ")\n" + DRIVER, marker


def observe(candidate, probe, sites, image, base_commit, root, *, public_hashes, keywords, blocked_import_dir=None):
    def builder(probe_sha, selected, nonce):
        return build_driver(probe_sha, selected, nonce, public_hashes, keywords)

    def command(descriptor, selected_image, commit, mounted):
        return _docker_command(descriptor, selected_image, commit, mounted, blocked_import_dir=blocked_import_dir)

    # Original validated-probe/image/nonce/source/timeout transport is preserved;
    # the controller driver never receives a forged model safe_static_check.
    with patch.object(transport, "build_driver", builder), patch.object(transport, "docker_command", command):
        return transport.observe(candidate, probe, sites, image, base_commit, root)
