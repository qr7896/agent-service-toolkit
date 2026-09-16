"""阶段 20：容器配置的静态校验（不需要 Docker）。

镜像构建本身在当前环境无法验证（本机没装 Docker），所以这里只做**能确定性验证**的部分：
文件齐备、COPY 源存在、compose 能解析、挂载点与代码里的真实路径一致，以及
"镜像里的目录层级是否会让 __file__ 推导出的路径失准"。
"""

from __future__ import annotations

import re
import posixpath
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

import yaml  # noqa: E402

DOCKERFILES = {
    "upstream": PROJECT_DIR / "docker" / "Dockerfile.service",
    "local": PROJECT_DIR / "docker" / "Dockerfile.service.local",
}
CODE_TOOLS_IN_REPO = Path("src/agents/code_tools.py")
TOOLS_IN_REPO = Path("src/agents/tools.py")


def copy_map(dockerfile: Path) -> dict[str, str]:
    """把 Dockerfile 的 COPY 指令解析成 {源: 目标}，用来推算文件在镜像里的位置。"""
    mapping: dict[str, str] = {}
    for raw in dockerfile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.upper().startswith("COPY "):
            continue
        parts = line.split()[1:]
        if len(parts) < 2:
            continue
        sources, dest = parts[:-1], parts[-1]
        for source in sources:
            if source.startswith("--"):
                continue
            name = source.rstrip("/")
            if dest.endswith("/") or len(parts) > 2:
                # COPY src/ ./src/  ->  src/agents/x.py 落到 ./src/agents/x.py
                mapping[name + "/"] = dest.rstrip("/") + "/"
            else:
                mapping[name] = dest
    return mapping


def workdir_of(dockerfile: Path) -> str:
    """COPY 的相对目标是按 WORKDIR 解析的，所以推算镜像路径时必须带上它。"""
    for raw in dockerfile.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.upper().startswith("WORKDIR "):
            return line.split(None, 1)[1].strip()
    return "/"


def image_path(repo_path: Path, mapping: dict[str, str], workdir: str = "/app") -> str | None:
    """按 COPY 规则算出某个仓库文件在镜像中的绝对路径。"""
    text = repo_path.as_posix()
    for source, dest in mapping.items():
        dest = dest if dest.startswith("/") else posixpath.join(workdir, dest)
        if source.endswith("/") and text.startswith(source):
            return posixpath.normpath(dest + "/" + text[len(source) :])
        if not source.endswith("/") and text == source:
            return posixpath.normpath(dest)
    return None


def derived_root(image_file: str) -> str:
    """复刻 `Path(__file__).resolve().parents[2]`：文件所在目录再往上两层。"""
    # 镜像是 Linux，必须用 POSIX 语义，否则 Windows 上会把 /app 渲染成 \app
    return posixpath.normpath(posixpath.dirname(posixpath.dirname(posixpath.dirname(image_file))))


def load_compose() -> dict:
    return yaml.safe_load((PROJECT_DIR / "compose.local-models.yaml").read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    for label, path in DOCKERFILES.items():
        if not path.exists():
            failures.append(f"{label}: missing {path.name}")
    if failures:
        print("\n".join(failures))
        return 1

    for label, path in DOCKERFILES.items():
        mapping = copy_map(path)
        for source in mapping:
            candidate = PROJECT_DIR / source.rstrip("/")
            if not candidate.exists():
                failures.append(f"{label}: COPY source missing -> {source}")
        print(f"[{label}] COPY 规则 {len(mapping)} 条，源文件均存在")

        workdir = workdir_of(path)
        image_code_tools = image_path(CODE_TOOLS_IN_REPO, mapping, workdir)
        image_tools = image_path(TOOLS_IN_REPO, mapping, workdir)
        if image_code_tools is None:
            failures.append(f"{label}: {CODE_TOOLS_IN_REPO} 没有被 COPY 进镜像")
            continue
        root = derived_root(image_code_tools)
        model_dir = posixpath.join(derived_root(image_tools), "models", "bge-m3")
        print(f"    code_tools -> {image_code_tools}")
        print(f"    PROJECT_ROOT 推导结果 -> {root}")
        print(f"    默认模型路径推导结果 -> {model_dir}")

    compose = load_compose()
    service = (compose.get("services") or {}).get("agent_service") or {}
    volumes = [v for v in service.get("volumes") or [] if isinstance(v, str)]
    env = [e for e in service.get("environment") or [] if isinstance(e, str)]

    if service.get("build", {}).get("dockerfile") != "docker/Dockerfile.service.local":
        failures.append("compose 覆盖层没有指向 Dockerfile.service.local")

    for needle, why in (
        ("/app/models/bge-m3", "本地 BGE-M3 模型必须挂载（约 2.3GB，不打进镜像）"),
        ("/app/src/chroma_db", "已灌好的知识库必须挂载（服务用相对 CWD 的 ./chroma_db）"),
        ("/app/.codex", "轨迹 / 经验库 / 沙箱必须挂载，否则重建容器就全丢"),
    ):
        if not any(needle in v for v in volumes):
            failures.append(f"缺少挂载 {needle}：{why}")
    print(f"[compose] 挂载 {len(volumes)} 条，包含模型 / 向量库 / .codex")

    if not any(e.startswith("EMBEDDING_MODEL_PATH=") for e in env):
        failures.append("必须在容器里覆盖 EMBEDDING_MODEL_PATH（.env 里是 Windows 路径）")
    if "EMBEDDING_MODEL_PATH=D:/codex/working/models/bge-m3" in (PROJECT_DIR / ".env").read_text(
        encoding="utf-8"
    ):
        print("[compose] 已确认 .env 里是 Windows 绝对路径，容器内必须覆盖")

    local_text = DOCKERFILES["local"].read_text(encoding="utf-8")
    for needle, why in (
        ("sentence-transformers", "本项目的 embedding 依赖不在 uv.lock 里，必须显式安装"),
        ("git", "git_diff 工具依赖 git 命令"),
        ("/app/src", "必须保留 src/ 层级，否则 __file__ 推导的路径失准"),
    ):
        if needle not in local_text:
            failures.append(f"local Dockerfile 缺少 {needle}：{why}")

    if (PROJECT_DIR / "docker" / "Dockerfile.service.local").exists():
        upstream_root = derived_root(
            image_path(CODE_TOOLS_IN_REPO, copy_map(DOCKERFILES["upstream"]), workdir_of(DOCKERFILES["upstream"])) or ""
        )
        local_root = derived_root(
            image_path(CODE_TOOLS_IN_REPO, copy_map(DOCKERFILES["local"]), workdir_of(DOCKERFILES["local"])) or ""
        )
        print(f"[结论] 上游镜像里 PROJECT_ROOT = {upstream_root}（失准）；本 fork = {local_root}")
        if local_root != "/app":
            failures.append(f"local 镜像里 PROJECT_ROOT 应为 /app，实际 {local_root}")

    if failures:
        print("\n失败项：")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("\n静态校验全部通过（注意：镜像构建本身未验证，本机没有 Docker）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
