import json

SYSTEM = 'You are an autonomous code editor in an evaluation sandbox. Return JSON only, exactly {"patch": {"relative/path.py": "complete replacement content"}}. Use only the task and evidence supplied. Do not modify tests. Do not use or request gold answers. Make the smallest repair consistent with the problem statement and visible code. Before answering, check every supplied evidence item, identify every visible file whose current content must change for the stated behavior, preserve behavior not contradicted by the task, and include all required files in one patch rather than stopping after the first plausible edit.'
REVIEW_SYSTEM = 'You are the final patch reviewer in an evaluation sandbox. Return JSON only, exactly {"patch": {"relative/path.py": "complete replacement content"}}. You receive the public task, the same bounded evidence, and a candidate patch. Do not use or request tests, grader output, or gold answers. Check the candidate against the problem statement and every visible evidence item, correct missing companion-file edits, incorrect state/value mappings, async error handling, and regressions implied by the visible code, then return the smallest complete corrected patch.'


def build_messages(payload):
    return [("system", SYSTEM), ("human", json.dumps(payload, ensure_ascii=False))]


def build_review_messages(payload, candidate_patch):
    review_payload = {"task": payload, "candidate_patch": candidate_patch}
    return [("system", REVIEW_SYSTEM), ("human", json.dumps(review_payload, ensure_ascii=False))]


def content_text(response):
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in content)
    return str(content)


def usage_tokens(response):
    usage = getattr(response, "usage_metadata", None) or {}
    metadata = getattr(response, "response_metadata", None) or {}
    fallback = metadata.get("token_usage", {})
    input_tokens = int(usage.get("input_tokens") or fallback.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or fallback.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or fallback.get("total_tokens") or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens or input_tokens + output_tokens,
    }


async def propose_patch(model, payload):
    response = await model.ainvoke(build_messages(payload))
    return content_text(response)
