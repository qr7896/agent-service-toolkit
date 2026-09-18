import json

SYSTEM = 'You are an autonomous code editor in an evaluation sandbox. Return JSON only, exactly {"patch": {"relative/path.py": "complete replacement content"}}. Use only the task and evidence supplied. Do not modify tests. Do not use or request gold answers. Make the smallest repair consistent with the problem statement and visible code.'


def build_messages(payload):
    return [("system", SYSTEM), ("human", json.dumps(payload, ensure_ascii=False))]


def content_text(response):
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in content)
    return str(content)


async def propose_patch(model, payload):
    response = await model.ainvoke(build_messages(payload))
    return content_text(response)
