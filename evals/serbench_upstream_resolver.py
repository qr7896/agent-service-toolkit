from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def resolve(explicit: Path | None = None) -> dict:
    if explicit:
        candidates = [explicit]
    else:
        candidates = []
        env = os.environ.get("SERBENCH_ROOT")
        if env:
            candidates.append(Path(env))
        candidates += [Path(".external/SERBench"), Path("../SERBench")]
    for root in candidates:
        if not root.exists():
            continue
        pkg = (
            (root / "src" / "serbench")
            if (root / "src" / "serbench").exists()
            else root / "serbench"
        )
        readme = root / "README.md"
        pyproject = root / "pyproject.toml"
        return {
            "found": True,
            "root": str(root.resolve()),
            "has_package": pkg.exists(),
            "has_readme": readme.exists(),
            "has_pyproject": pyproject.exists(),
            "ready": pkg.exists() and readme.exists() and pyproject.exists(),
        }
    return {
        "found": False,
        "root": None,
        "has_package": False,
        "has_readme": False,
        "ready": False,
        "remediation": "Provide an upstream SERBench checkout via --root or SERBENCH_ROOT; do not vendor benchmark data into this repository.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path)
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    r = resolve(a.root)
    if a.output:
        a.output.write_text(json.dumps(r, indent=2), encoding="utf-8")
    print(json.dumps(r))
    sys.exit(0 if r["ready"] else 2)


if __name__ == "__main__":
    main()
