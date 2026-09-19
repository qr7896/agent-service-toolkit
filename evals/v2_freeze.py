from __future__ import annotations
import argparse, json
from pathlib import Path
from evals.v2_dataset import load_jsonl
from evals.v2_distribution import distribution_report
from evals.v2_manifest import build_dataset_manifest


def freeze_dataset(dataset: Path, sources: list[Path], manifest_path: Path, report_path: Path, *, min_records=200):
    records=load_jsonl(dataset)
    report=distribution_report(records,min_records=min_records)
    if not report["validation"]["ready_for_replay"]:
        raise RuntimeError("dataset is not replay-ready; freeze refused")
    manifest=build_dataset_manifest(dataset,sources,min_records=min_records)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return manifest,report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset",type=Path,required=True); ap.add_argument("--source",type=Path,action="append",default=[])
    ap.add_argument("--manifest",type=Path,required=True); ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--min-records",type=int,default=200); args=ap.parse_args()
    freeze_dataset(args.dataset,args.source,args.manifest,args.report,min_records=args.min_records)


if __name__=="__main__": main()
