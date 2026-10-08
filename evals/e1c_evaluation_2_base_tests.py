"""Bounded retrieval of test blobs at a caller-pinned base; never reads checkout tests."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import PurePosixPath


def _git(workspace, *args):
    return subprocess.check_output(['git', '-C', str(workspace), *args], timeout=30)


def safe_test_path(name):
    if not isinstance(name, str):
        raise ValueError('unsafe base test path')
    path = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name
            or any(ord(c) < 32 for c in name) or path.is_absolute() or '..' in path.parts
            or path.as_posix() != name):
        raise ValueError('unsafe base test path')
    blocked = {'grader-only', '.git', '.codex', 'sealed', 'fresh30', 'gold', 'answers'}
    if any(p.casefold() in blocked for p in path.parts):
        raise ValueError('protected test path')
    return name.endswith('.py') and (
        any(p in {'tests', 'test'} for p in path.parts[:-1]) or path.name.startswith('test_')
    )


def base_blob(workspace, base, name):
    if not re.fullmatch('[0-9a-f]{40}', base):
        raise ValueError('exact base commit required')
    if not safe_test_path(name):
        raise ValueError('only base Python test paths allowed')
    # Literal Git pathspec prevents wildcard/attribute selection. No history/ref argument is accepted.
    entry = _git(workspace, 'ls-tree', '-z', base, '--', ':(literal)' + name).split(b'\0')
    if len(entry) != 2 or not entry[0]:
        raise ValueError('test absent from base')
    header, actual_name = entry[0].split(b'\t', 1)
    mode, kind, oid = header.decode().split()
    if mode not in {'100644', '100755'} or kind != 'blob' or actual_name.decode() != name:
        raise ValueError('only regular base blobs allowed')
    size = int(_git(workspace, 'cat-file', '-s', oid))
    if size > 300_000:
        raise ValueError('single base test byte budget exceeded')
    raw = _git(workspace, 'cat-file', 'blob', oid)
    if len(raw) != size or hashlib.sha1(f'blob {size}\0'.encode() + raw).hexdigest() != oid:
        raise ValueError('base blob identity differs')
    return raw, oid


def retrieve(workspace, base, seeds):
    if not re.fullmatch('[0-9a-f]{40}', base):
        raise ValueError('exact base commit required')
    seeds = sorted({s.casefold() for s in seeds if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{3,63}', s)})[:12]
    if not seeds:
        raise ValueError('bounded source/issue seeds required')
    tree = _git(workspace, 'ls-tree', '-r', '-z', base)
    if len(tree) > 2_000_000:
        raise ValueError('base tree byte budget exceeded')
    names = []
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        header, name = entry.split(b'\t', 1)
        mode, kind, _ = header.decode().split()
        name = name.decode('utf-8')
        try:
            allowed = safe_test_path(name)
        except ValueError:
            allowed = False
        if allowed and mode in {'100644', '100755'} and kind == 'blob':
            names.append(name)
    if len(names) > 512:
        raise ValueError('base test file budget exceeded')
    scanned, matches = 0, []
    for name in sorted(names):
        raw, oid = base_blob(workspace, base, name)
        scanned += len(raw)
        if scanned > 2_000_000:
            raise ValueError('total base test byte budget exceeded')
        lines = raw.decode('utf-8').splitlines()
        hits = [(n, sum(seed in line.casefold() for seed in seeds)) for n, line in enumerate(lines)]
        hits = [(n, score) for n, score in hits if score]
        if hits:
            matches.append((max(score for _, score in hits), name, raw, oid, lines, hits))
    windows, chars = [], 0
    for _, name, raw, oid, lines, hits in sorted(matches, key=lambda x: (-x[0], x[1]))[:3]:
        covered = set()
        for n, _ in sorted(hits, key=lambda x: (-x[1], x[0])):
            start, end = max(0, n - 8), min(len(lines), n + 17)
            if n in covered:
                continue
            text = '\n'.join(lines[start:end])
            if chars + len(text) > 9_000:
                continue
            windows.append({'path': name, 'start_line': start + 1, 'end_line': end,
                            'text': text, 'origin': 'base_commit_test_blob', 'base_commit': base,
                            'git_blob_oid': oid, 'source_sha256': hashlib.sha256(raw).hexdigest()})
            covered.update(range(start, end))
            chars += len(text)
            if len(windows) == 6:
                break
        if len(windows) == 6:
            break
    return {'schema': 'e1c2-base-test-context-v1', 'base_commit': base, 'seeds': seeds,
            'scanned_files': len(names), 'scanned_bytes': scanned, 'windows': windows,
            'checkout_test_content_read': False, 'future_history_read': False}
