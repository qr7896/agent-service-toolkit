"""Pre-call public evidence IDs: avoid generated quotes without changing probe code."""

import hashlib
import json
import re


def anchors(issue):
    if not isinstance(issue, str) or not issue.strip():
        raise ValueError('public projected issue required')
    records = []
    for match in re.finditer(r'[^\n]+', issue):
        line = match.group().strip()
        if len(line) < 8:
            continue
        start = match.start() + len(match.group()) - len(match.group().lstrip())
        text = line[:300]
        digest = hashlib.sha256(text.encode()).hexdigest()
        records.append({'id': f'E{len(records) + 1}-{digest[:12]}', 'start': start,
                        'end': start + len(text), 'text': text, 'sha256': digest})
        if len(records) == 12:
            break
    return {'issue_sha256': hashlib.sha256(issue.encode()).hexdigest(), 'records': records}


def decode_pair(raw, issue, frozen_anchors):
    if anchors(issue) != frozen_anchors:
        raise ValueError('pre-call issue anchor registry changed')
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {'normal_source', 'target_source', 'issue_anchor_id'}:
        raise ValueError('only paired programs and a registered evidence ID are allowed')
    matches = [r for r in frozen_anchors['records'] if r['id'] == value['issue_anchor_id']]
    if len(matches) != 1:
        raise ValueError('unknown public evidence anchor')
    record = matches[0]
    if issue[record['start']:record['end']] != record['text']:
        raise ValueError('anchor is not its exact public source span')
    if any(not isinstance(value[k], str) for k in ('normal_source', 'target_source')):
        raise ValueError('paired program strings required')
    # No post-hoc matching/quote repair; the model selects a pre-call frozen ID.
    return json.dumps({'normal_source': value['normal_source'], 'target_source': value['target_source'],
                       'issue_quote': record['text']}, ensure_ascii=False)
