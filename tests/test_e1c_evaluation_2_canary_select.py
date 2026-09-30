import hashlib

from evals.e1c_evaluation_2_canary_select import SALT, _ids, select


def test_select_uses_fixed_repo_then_task_hash_and_excludes_all_seen_ids():
    rows = [
        {"instance_id": f"{repo}__{repo}-{number}"}
        for repo in ("alpha", "beta", "gamma", "delta")
        for number in (1, 2)
    ]
    excluded = {"alpha__alpha-1", "delta__delta-2"}
    result = select({"tasks": rows}, excluded)

    def rank(kind, value):
        return hashlib.sha256((SALT + "\0" + kind + "\0" + value).encode()).hexdigest(), value

    repos = sorted(("alpha", "beta", "gamma", "delta"), key=lambda repo: rank("repo", repo))[:3]
    expected = [
        min(
            (row for row in rows if row["instance_id"].startswith(repo + "__") and row["instance_id"] not in excluded),
            key=lambda row: rank("task", row["instance_id"]),
        )
        for repo in repos
    ]
    assert result == expected
    assert _ids({"rows": [{"task_id": "alpha__alpha-1"}, {"str": "not-an-id"}]}) == {"alpha__alpha-1"}
