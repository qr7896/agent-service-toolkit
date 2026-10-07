"""Lossless production-window overlap encoding; not a semantic summarizer."""

from __future__ import annotations

import copy
import hashlib
import json

from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import (
    assert_production_relative_path,
    audit_repair_visible_payload,
)


def restore(value):
    value = copy.deepcopy(value)
    segments = {row["id"]: row for row in value.pop("source_segments")}
    for row in value["windows"]:
        ref = row.pop("text_ref")
        row["text"] = segments[ref["segment"]]["text"][ref["offset"]:ref["offset"] + ref["length"]]
    return value


def encode_windows(value, workspace):
    original = copy.deepcopy(value)
    if "source_segments" in original or any("text_ref" in row for row in original["windows"]):
        raise ValueError("reserved_lossless_encoding_fields")
    groups = {}
    for index, row in enumerate(original["windows"]):
        key = (row["path"], row["source_sha256"])
        if key not in groups:
            assert_production_relative_path(row["path"])
            path = workspace / row["path"]
            if path.is_symlink():
                raise ValueError("source_symlink")
            path = assert_agent_path(path, workspace=workspace)
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != row["source_sha256"]:
                raise ValueError("source_hash_changed")
            groups[key] = {"source": "\n".join(raw.decode("utf-8", errors="replace").splitlines()), "ranges": []}
        group = groups[key]
        lines = group["source"].split("\n")
        if type(row["start_line"]) is not int or not 1 <= row["start_line"] <= len(lines):
            raise ValueError("invalid_source_window_line")
        start = sum(len(line) + 1 for line in lines[:row["start_line"] - 1])
        end = start + len(row["text"])
        if group["source"][start:end] != row["text"]:
            raise ValueError("window_not_exact_source_slice")
        group["ranges"].append((start, end, index))
    encoded = copy.deepcopy(original)
    encoded["source_segments"] = []
    for key, group in sorted(groups.items()):
        merged = []
        for start, end, index in sorted(group["ranges"]):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
                merged[-1][2].append((start, end, index))
            else:
                merged.append([start, end, [(start, end, index)]])
        for start, end, spans in merged:
            identity = f"s{len(encoded['source_segments'])}"
            encoded["source_segments"].append({"id": identity, "path": key[0], "source_sha256": key[1],
                                               "text": group["source"][start:end]})
            for left, right, index in spans:
                row = encoded["windows"][index]
                row.pop("text")
                row["text_ref"] = {"segment": identity, "offset": left - start, "length": right - left}
    if restore(encoded) != original:
        raise ValueError("lossless_rehydration_failed")
    audit_repair_visible_payload(encoded)
    return encoded, {"schema": "e1c2-lossless-window-encoding-v1", "rehydrated_equal": True,
                     "source_content_added": False, "metadata_dropped": False,
                     "original_sha256": audit_repair_visible_payload(original),
                     "original_chars": len(input_json(original)), "encoded_chars": len(input_json(encoded))}


def compact_data_message(content, workspace):
    original = json.loads(content)
    encoded, proof = encode_windows(original, workspace)
    if len(input_json(encoded)) >= len(content):
        return content, {**proof, "applied": False, "no_size_gain": True}
    return input_json(encoded), {**proof, "applied": True, "no_size_gain": False}
