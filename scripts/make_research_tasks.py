"""Build and verify the 20-task Research Mode seed set without model calls.

Each task is a minimized reproducer of a real repository change.  The compact
fixtures keep the benchmark cheap while source_commit/base_commit preserve the
link to the original fix.  Gold evidence was checked against the fixture and
the referenced repository change before ``gold_verified`` was set.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.swe_tasks import grade, load_tasks, prepare  # noqa: E402

OUTPUT = ROOT / "evals" / "tasks" / "research_v0.jsonl"

LOADER = """\
import importlib.util
import sys
from pathlib import Path


def load(rel):
    path = Path(__file__).parent / rel
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["under_test"] = module
    spec.loader.exec_module(module)
    return module
"""


def task(
    instance_id: str,
    task_type: str,
    cluster: str,
    split: str,
    source_commit: str,
    base_commit: str,
    problem: str,
    path: str,
    before: str,
    after: str,
    test_body: str,
    symbols: list[str],
    *,
    extra_before: dict[str, str] | None = None,
    extra_after: dict[str, str] | None = None,
    callers: list[str] | None = None,
    context: list[str] | None = None,
) -> dict:
    test_file = f"test_{instance_id.replace('-', '_')}.py"
    setup = {path: before, **(extra_before or {})}
    gold = {path: after, **(extra_after or extra_before or {})}
    return {
        "instance_id": instance_id,
        "repo": "qr7896/agent-service-toolkit",
        "base_commit": base_commit,
        "source_commit": source_commit,
        "task_type": task_type,
        "cluster": cluster,
        "split": split,
        "gold_verified": True,
        "problem_statement": problem,
        "setup_files": setup,
        "test_files": {test_file: LOADER + "\n" + test_body},
        "gold_sources": gold,
        "FAIL_TO_PASS": [f"{test_file}::test_fix"],
        "PASS_TO_PASS": [f"{test_file}::test_regression"],
        "gold_files": [path, *(extra_after or extra_before or {})],
        "gold_symbols": symbols,
        "gold_callers": callers or ["test_fix"],
        "gold_tests": [f"{test_file}::test_fix"],
        "gold_context": context or [path, f"{test_file}::test_fix"],
    }


TASKS = [
    task(
        "research__test-command-guard-01",
        "T5",
        "validation",
        "train",
        "1df3c67",
        "179cb46",
        "测试工具应允许 pytest 与 python -m pytest，但拒绝任意 Python 脚本。",
        "src/agents/test_tools.py",
        "def allowed(command):\n    return command.startswith(('pytest', 'python'))\n",
        "import shlex\n\ndef allowed(command):\n    p = shlex.split(command)\n    return bool(p) and (p[0] == 'pytest' or p[:3] == ['python', '-m', 'pytest'])\n",
        "m = load('src/agents/test_tools.py')\n\ndef test_fix():\n    assert m.allowed('python -m pytest -q') and not m.allowed('python tool.py')\n\ndef test_regression():\n    assert m.allowed('pytest -q')\n",
        ["allowed"],
    ),
    task(
        "research__debug-prompt-no-hit-02",
        "T6",
        "memory-quality",
        "train",
        "5a14425",
        "d518a53",
        "没有经验命中时，debug 提示词必须与原提示逐字相同。",
        "src/agents/debugger.py",
        "def prompt(base, experiences):\n    return base + '\\n历史经验：' + '\\n'.join(experiences)\n",
        "def prompt(base, experiences):\n    return base if not experiences else base + '\\n历史经验：' + '\\n'.join(experiences)\n",
        "m = load('src/agents/debugger.py')\n\ndef test_fix():\n    assert m.prompt('修复失败测试', []) == '修复失败测试'\n\ndef test_regression():\n    assert '经验A' in m.prompt('修复', ['经验A'])\n",
        ["prompt"],
    ),
    task(
        "research__benchmark-cost-03",
        "T8",
        "observability",
        "train",
        "59e9bdd",
        "3367f2a",
        "基准汇总需要报告平均与总 estimated_tokens，并兼容缺失字段。",
        "evals/coding_benchmark.py",
        "def summarize(rows):\n    return {'tasks': len(rows)}\n",
        "def summarize(rows):\n    vals = [int(r.get('estimated_tokens') or 0) for r in rows]\n    return {'tasks': len(rows), 'avg_estimated_tokens': sum(vals) / len(vals) if vals else 0, 'total_estimated_tokens': sum(vals)}\n",
        "m = load('evals/coding_benchmark.py')\n\ndef test_fix():\n    assert m.summarize([{'estimated_tokens': 10}, {}])['total_estimated_tokens'] == 10\n\ndef test_regression():\n    assert m.summarize([])['tasks'] == 0\n",
        ["summarize"],
    ),
    task(
        "research__workflow-message-input-04",
        "T1",
        "input-normalization",
        "train",
        "3183ac9",
        "59e9bdd",
        "服务只传 messages 时工作流不能收到空输入；显式 workflow_input 仍应优先。",
        "src/agents/agent_workflow.py",
        "def user_input(state):\n    return state.get('workflow_input') or ''\n",
        "def user_input(state):\n    if state.get('workflow_input'):\n        return state['workflow_input']\n    for msg in reversed(state.get('messages') or []):\n        if msg.get('role') == 'user':\n            return str(msg.get('content') or '')\n    return ''\n",
        "m = load('src/agents/agent_workflow.py')\n\ndef test_fix():\n    assert m.user_input({'messages': [{'role': 'user', 'content': '修一下'}]}) == '修一下'\n\ndef test_regression():\n    assert m.user_input({'workflow_input': '显式', 'messages': [{'role': 'user', 'content': '消息'}]}) == '显式'\n",
        ["user_input"],
        callers=["_step_runner", "make_router_node"],
    ),
    task(
        "research__related-tests-05",
        "T9",
        "validation",
        "train",
        "fcbe49e",
        "2a7058e",
        "相关测试发现应只返回调用目标符号的测试，而不是所有 test_ 函数。",
        "src/agents/code_intel.py",
        "def related(symbol, callers):\n    return sorted(n for n in callers if n.startswith('test_'))\n",
        "def related(symbol, callers):\n    return sorted(n for n, called in callers.items() if n.startswith('test_') and symbol in called)\n",
        "m = load('src/agents/code_intel.py')\n\ndef test_fix():\n    c = {'test_add': {'add'}, 'test_sub': {'sub'}, 'main': {'add'}}\n    assert m.related('add', c) == ['test_add']\n\ndef test_regression():\n    assert m.related('missing', {}) == []\n",
        ["related"],
    ),
    task(
        "research__conflict-exit-06",
        "T10",
        "evidence-decision",
        "train",
        "994fd72",
        "3e7b27c",
        "权限策略冲突可静态判定；只有行为结果冲突才应进入昂贵实验。",
        "src/agents/conflict.py",
        "def classify(kind):\n    return 'experiment'\n",
        "def classify(kind):\n    return 'static' if kind in {'permission', 'schema', 'budget'} else 'experiment'\n",
        "m = load('src/agents/conflict.py')\n\ndef test_fix():\n    assert m.classify('permission') == 'static'\n\ndef test_regression():\n    assert m.classify('runtime') == 'experiment'\n",
        ["classify"],
    ),
    task(
        "research__dual-evidence-gates-07",
        "T7",
        "evidence-decision",
        "train",
        "28ab094",
        "e0f6219",
        "证据是否充分与继续检索是否值得必须分开，预算耗尽不能伪装成证据充分。",
        "src/agents/evidence.py",
        "def sufficient(score, threshold=.8):\n    return score >= threshold\n\ndef worth_more(score, rounds_left):\n    return not sufficient(score)\n",
        "def sufficient(score, threshold=.8):\n    return score >= threshold\n\ndef worth_more(score, rounds_left):\n    if sufficient(score): return False, 'sufficient'\n    if rounds_left <= 0: return False, 'budget_exhausted'\n    return True, 'continue'\n",
        "m = load('src/agents/evidence.py')\n\ndef test_fix():\n    assert m.worth_more(0.1, 0) == (False, 'budget_exhausted')\n\ndef test_regression():\n    assert m.sufficient(.9) is True\n",
        ["sufficient", "worth_more"],
        callers=["audit_plan"],
    ),
    task(
        "research__sandbox-result-08",
        "T8",
        "sandbox-output",
        "train",
        "3e7b27c",
        "28ab094",
        "沙箱回写结果必须同时返回 patch 与验证结果，不能只返回文件清单。",
        "src/agents/workspace.py",
        "def collect_result(patch, test_result=None):\n    return {'patch': patch}\n",
        "def collect_result(patch, test_result=None):\n    return {'patch': patch, 'verification': test_result or {}}\n",
        "m = load('src/agents/workspace.py')\n\ndef test_fix():\n    r = m.collect_result('diff', {'passed': True}); assert r == {'patch': 'diff', 'verification': {'passed': True}}\n\ndef test_regression():\n    assert m.collect_result('')['patch'] == ''\n",
        ["collect_result"],
        callers=["run_task"],
    ),
    task(
        "research__sandbox-gc-09",
        "T2",
        "sandbox-output",
        "train",
        "3e7b27c",
        "28ab094",
        "启动回收只能删除带沙箱标记的孤儿目录，不能误删普通目录。",
        "src/agents/workspace.py",
        "from pathlib import Path\n\ndef garbage(root):\n    return [p for p in Path(root).iterdir() if p.is_dir()]\n",
        "from pathlib import Path\n\ndef garbage(root):\n    return [p for p in Path(root).iterdir() if p.is_dir() and (p / '.codex-sandbox').exists()]\n",
        "m = load('src/agents/workspace.py')\n\ndef test_fix(tmp_path):\n    a=tmp_path/'a'; b=tmp_path/'b'; a.mkdir(); b.mkdir(); (a/'.codex-sandbox').touch(); assert m.garbage(tmp_path)==[a]\n\ndef test_regression(tmp_path):\n    assert m.garbage(tmp_path) == []\n",
        ["garbage"],
        extra_before={"src/agents/workspace_config.py": "SANDBOX_MARKER = '.codex-sandbox'\n"},
    ),
    task(
        "research__approval-id-10",
        "T3",
        "durable-approval",
        "train",
        "d76338f",
        "f65067b",
        "同一批 tool call 的 approval_id 必须与调用顺序无关，跨进程恢复才能幂等。",
        "src/agents/coding_agent.py",
        "import hashlib\n\ndef approval_id(thread_id, calls):\n    raw = thread_id + ''.join(c['id'] for c in calls)\n    return hashlib.sha1(raw.encode()).hexdigest()[:16]\n",
        "import hashlib\n\ndef approval_id(thread_id, calls):\n    raw = thread_id + ''.join(sorted(c['id'] for c in calls))\n    return hashlib.sha1(raw.encode()).hexdigest()[:16]\n",
        "m = load('src/agents/coding_agent.py')\n\ndef test_fix():\n    a=[{'id':'b'},{'id':'a'}]; assert m.approval_id('t', a)==m.approval_id('t', list(reversed(a)))\n\ndef test_regression():\n    assert len(m.approval_id('t', [{'id':'a'}])) == 16\n",
        ["approval_id"],
        callers=["approval_node"],
    ),
    task(
        "research__async-checkpointer-11",
        "T4",
        "durable-approval",
        "train",
        "d76338f",
        "f65067b",
        "异步图必须选择 AsyncSqliteSaver，不能把同步 saver 传给 ainvoke。",
        "src/memory/checkpoint.py",
        "def saver_name(async_graph):\n    return 'SqliteSaver'\n",
        "def saver_name(async_graph):\n    return 'AsyncSqliteSaver' if async_graph else 'SqliteSaver'\n",
        "m = load('src/memory/checkpoint.py')\n\ndef test_fix():\n    assert m.saver_name(True) == 'AsyncSqliteSaver'\n\ndef test_regression():\n    assert m.saver_name(False) == 'SqliteSaver'\n",
        ["saver_name"],
        callers=["ainvoke"],
    ),
    task(
        "research__experience-isolation-12",
        "T3",
        "memory-quality",
        "train",
        "ead5691",
        "d76338f",
        "经验至少命中 3 次且帮助率低于 0.34 时隔离；样本不足不能过早下判断。",
        "src/agents/experience.py",
        "def isolated(used, helped, minimum=3, floor=.34):\n    return used and helped / used < floor\n",
        "def isolated(used, helped, minimum=3, floor=.34):\n    return used >= minimum and helped / used < floor\n",
        "m = load('src/agents/experience.py')\n\ndef test_fix():\n    assert not m.isolated(2,0) and m.isolated(3,0)\n\ndef test_regression():\n    assert not m.isolated(4,4)\n",
        ["isolated"],
        callers=["compatibility"],
    ),
    task(
        "research__experience-survival-13",
        "T10",
        "memory-quality",
        "dev",
        "ead5691",
        "d76338f",
        "沙箱改动尚未落地应标为 not_applied，不能误判为 reverted。",
        "src/agents/experience.py",
        "def survival(applied, current, changed, baseline):\n    return 'intact' if current == changed else 'reverted' if current == baseline else 'modified'\n",
        "def survival(applied, current, changed, baseline):\n    if not applied: return 'not_applied'\n    return 'intact' if current == changed else 'reverted' if current == baseline else 'modified'\n",
        "m = load('src/agents/experience.py')\n\ndef test_fix():\n    assert m.survival(False, 'base', 'fix', 'base') == 'not_applied'\n\ndef test_regression():\n    assert m.survival(True, 'base', 'fix', 'base') == 'reverted'\n",
        ["survival"],
        callers=["reevaluate_survival"],
    ),
    task(
        "research__permission-ack-14",
        "T2",
        "policy-gate",
        "dev",
        "e196446",
        "ead5691",
        "敏感权限文件发生变化时必须要求显式确认；普通文档变化可直接通过。",
        "scripts/permission_diff_gate.py",
        "SENSITIVE = {'src/agents/code_tools.py'}\n\ndef allowed(paths, ack=False):\n    return True\n",
        "SENSITIVE = {'src/agents/code_tools.py'}\n\ndef allowed(paths, ack=False):\n    return ack or not (set(paths) & SENSITIVE)\n",
        "m = load('scripts/permission_diff_gate.py')\n\ndef test_fix():\n    assert not m.allowed(['src/agents/code_tools.py']) and m.allowed(['src/agents/code_tools.py'], True)\n\ndef test_regression():\n    assert m.allowed(['docs/README.md'])\n",
        ["allowed", "SENSITIVE"],
        extra_before={".github/workflows/permission-gate.yml": "name: permission-gate\n"},
    ),
    task(
        "research__blind-spot-metrics-15",
        "T9",
        "observability",
        "dev",
        "e196446",
        "ead5691",
        "盲区指标必须报告 AST 解析失败率，不能静默跳过坏文件。",
        "scripts/trajectory_metrics.py",
        "import ast\n\ndef failure_rate(sources):\n    for text in sources: \n        try: ast.parse(text)\n        except SyntaxError: pass\n    return 0.0\n",
        "import ast\n\ndef failure_rate(sources):\n    if not sources: return 0.0\n    failed=0\n    for text in sources:\n        try: ast.parse(text)\n        except SyntaxError: failed += 1\n    return failed / len(sources)\n",
        "m = load('scripts/trajectory_metrics.py')\n\ndef test_fix():\n    assert m.failure_rate(['x=1', 'def broken(']) == .5\n\ndef test_regression():\n    assert m.failure_rate([]) == 0\n",
        ["failure_rate"],
    ),
    task(
        "research__difficulty-calibration-16",
        "T5",
        "validation",
        "dev",
        "e196446",
        "ead5691",
        "所有实验臂首次通过率都为 0 或 1 时，校准必须报警。",
        "evals/coding_benchmark.py",
        "def degenerate(rates):\n    return False\n",
        "def degenerate(rates):\n    return bool(rates) and all(rate in {0, 1} for rate in rates)\n",
        "m = load('evals/coding_benchmark.py')\n\ndef test_fix():\n    assert m.degenerate([0,0,0]) and m.degenerate([1,1])\n\ndef test_regression():\n    assert not m.degenerate([0,.5,1])\n",
        ["degenerate"],
    ),
    task(
        "research__probe-expectation-17",
        "T1",
        "validation",
        "test",
        "cd6a3f3",
        "39ffc20",
        "探针门禁要逐条比较 expected_resolved，不能只检查判分器是否返回 True。",
        "evals/coding_benchmark.py",
        "def probe_ok(rows):\n    return all(r['resolved'] for r in rows)\n",
        "def probe_ok(rows):\n    return all(r['resolved'] == r['expected_resolved'] for r in rows)\n",
        "m = load('evals/coding_benchmark.py')\n\ndef test_fix():\n    assert m.probe_ok([{'resolved':True,'expected_resolved':True},{'resolved':False,'expected_resolved':False}])\n\ndef test_regression():\n    assert not m.probe_ok([{'resolved':True,'expected_resolved':False}])\n",
        ["probe_ok"],
    ),
    task(
        "research__inline-workflow-18",
        "T7",
        "workflow-composition",
        "test",
        "39ffc20",
        "e196446",
        "工作流步骤必须在 agent 引用和内联 mode 之间二选一，并限制递归深度。",
        "src/agents/agent_workflow.py",
        "def valid(agent=None, mode=None, depth=0):\n    return bool(agent or mode)\n",
        "MAX_DEPTH=4\n\ndef valid(agent=None, mode=None, depth=0):\n    return bool(agent) != bool(mode) and depth <= MAX_DEPTH\n",
        "m = load('src/agents/agent_workflow.py')\n\ndef test_fix():\n    assert not m.valid('a','parallel') and not m.valid(mode='loop', depth=5)\n\ndef test_regression():\n    assert m.valid(agent='a') and m.valid(mode='parallel')\n",
        ["valid", "MAX_DEPTH"],
        callers=["build_workflow"],
    ),
    task(
        "research__gold-field-split-19",
        "T4",
        "input-normalization",
        "test",
        "28c6b12",
        "cd6a3f3",
        "gold_files 是证据路径列表，标准修复内容必须使用 gold_sources，二者不能同名覆盖。",
        "evals/swe_tasks.py",
        "def parse(data):\n    return {'gold_sources': data.get('gold_files', {}), 'gold_files': data.get('gold_files', [])}\n",
        "def parse(data):\n    files=data.get('gold_files', [])\n    return {'gold_sources': data.get('gold_sources', {}), 'gold_files': files if isinstance(files,list) else []}\n",
        "m = load('evals/swe_tasks.py')\n\ndef test_fix():\n    r=m.parse({'gold_sources':{'a.py':'x'},'gold_files':['a.py']}); assert r=={'gold_sources':{'a.py':'x'},'gold_files':['a.py']}\n\ndef test_regression():\n    assert m.parse({}) == {'gold_sources':{},'gold_files':[]}\n",
        ["parse"],
    ),
    task(
        "research__legacy-gold-compat-20",
        "T6",
        "input-normalization",
        "test",
        "28c6b12",
        "cd6a3f3",
        "旧任务把源码 dict 放在 gold_files；新加载器应兼容读取但不把键误当证据列表。",
        "evals/swe_tasks.py",
        "def parse(data):\n    return data.get('gold_sources', {}), data.get('gold_files', [])\n",
        "def parse(data):\n    old=data.get('gold_files')\n    return data.get('gold_sources') or (old if isinstance(old,dict) else {}), old if isinstance(old,list) else []\n",
        "m = load('evals/swe_tasks.py')\n\ndef test_fix():\n    assert m.parse({'gold_files':{'a.py':'fixed'}}) == ({'a.py':'fixed'}, [])\n\ndef test_regression():\n    assert m.parse({'gold_files':['a.py']}) == ({}, ['a.py'])\n",
        ["parse"],
    ),
]


def write_tasks() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in TASKS),
        encoding="utf-8",
    )


def validate_metadata() -> None:
    assert len(TASKS) == 20
    assert len({row["instance_id"] for row in TASKS}) == 20
    assert Counter(row["task_type"] for row in TASKS) == {f"T{i}": 2 for i in range(1, 11)}
    assert Counter(row["split"] for row in TASKS) == {"train": 12, "dev": 4, "test": 4}
    assert all(row["gold_verified"] for row in TASKS)
    assert all(
        row[key]
        for row in TASKS
        for key in ("gold_files", "gold_symbols", "gold_callers", "gold_tests", "gold_context")
    )
    clustered = Counter(row["cluster"] for row in TASKS)
    assert sum(count >= 2 for count in clustered.values()) >= 6


def verify() -> None:
    validate_metadata()
    specs = load_tasks(OUTPUT)
    with tempfile.TemporaryDirectory(prefix="research-v0-") as temp:
        root = Path(temp)
        for spec in specs:
            case = root / spec.instance_id
            prepare(spec, case)
            before = grade(spec, case)
            shutil.rmtree(case)
            prepare(spec, case, with_gold=True)
            after = grade(spec, case)
            assert not before["resolved"], f"{spec.instance_id}: base unexpectedly passes"
            assert after["resolved"], f"{spec.instance_id}: gold failed: {after['detail']}"
    print("research_v0: 20/20 base fail + gold pass; metadata valid")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    write_tasks()
    validate_metadata()
    if args.verify:
        verify()
    else:
        print(f"wrote {len(TASKS)} tasks to {OUTPUT}")


if __name__ == "__main__":
    main()
