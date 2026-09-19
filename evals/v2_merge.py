from __future__ import annotations
import json
from pathlib import Path
from evals.v2_dataset import canonical_record_sha256, validate_records


def merge_jsonl(sources, output: Path, *, min_records=200):
    merged=[]; seen=set(); duplicate_sources=0
    for source in sources:
        for line in Path(source).read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            row=json.loads(line); h=canonical_record_sha256(row)
            if h in seen:
                duplicate_sources += 1
                continue
            seen.add(h); merged.append(row)
    validation=validate_records(merged,min_records=min_records)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in merged),encoding="utf-8")
    return {**validation,"sources":[Path(s).as_posix() for s in sources],"source_duplicates_removed":duplicate_sources}
