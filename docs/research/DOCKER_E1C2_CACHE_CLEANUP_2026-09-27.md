# E1-C evaluation_2 双盘缓存清理记录（2026-09-27）

## 清理前保护范围

- 保留项目 `data/`、`.codex/e1c/`、`docs/`、`evals/`、测试、Git 工作区、密钥及 `D:\codex\working\webcodex-docker-bridge\` 整目录。
- 保留当前活动 VHDX：`D:\DockerDesktopData\wsl\disk\docker_data.vhdx`。
- 保留旧 VHDX：`D:\docker_related\DockerDesktopWSL\disk\docker_data.vhdx.inactive-20260927.bak`。其约 67.2 GiB，含最终旧 DEV30 等镜像缓存；无可用的已验证外置归档，不能以“对 DEV12 无直接作用”为由直接删除。
- 保留当前盘的旧 DEV/开发见证镜像：`sympy-14711`、`django-15569`、`django-11734`、`scikit-learn-13313`；保留 7.81 MB 的 `alpine:3.20` 作为零下载 Docker smoke。
- Bridge `docker_status` 查询的 frozen strict-v5 三张镜像 `xarray-3993`、`sympy-15308`、`django-16092` 清理前即未安装；本轮不动隧道进程、密钥、配置、桥接服务、Docker Desktop 设置。

## 清理前只读基线

- Docker Desktop / Engine：29.4.0 / 29.4.0，15 张镜像，0 容器，0 volume，0 build cache。
- Docker image store 逻辑 SIZE 37.61 GB；`docker system df` 报 reclaimable 32 GB。该数字不是 Windows VHDX 文件保证缩小的字节数。
- 本机 bridge `python -m unittest -v test_bridge.py`：5 passed；`mcp_server.docker_status()`：`docker_ready=True`，三张 frozen 镜像 local digest 为空（与清理前相同）。
- D 盘空闲 4.56 GiB。两个本地 `tunnel-client` 健康/就绪端点 200；App 内私有连接返回 `not connected`，因此**没有 WebCodex 端到端可用的正向基线**，后验也不能声称云端连接成功。

## 本轮精确移除候选

仅对下列 `docker image rm --no-prune <精确仓库:latest>` 操作；不使用 `-f`、通配符、`prune -a` 或文件系统层面的删除。官方 image RepoDigest 已由清理前 `docker image ls -a --digests` 核对；研究证据文件保留。

| 批次 | 实例 | 清理前 Image ID | 理由 |
|---|---|---|---|
| A | `django-12453` | `fa05aa7f64f9` | source-contract 独立 canary 已封存阴性 |
| A | `sympy-13761` | `8ac08d2e47b3` | source-contract 独立 canary 已封存阴性 |
| A | `matplotlib-21559` | `3b8b7c1be982` | 同一已封存 canary；官方准入结果在仓库 |
| B | `matplotlib-26291` | `757855ad838f` | 旧 CTI canary，未进入 evaluation_2 DEV12 |
| B | `sphinx-7757` | `2ec63928131f` | 旧 CTI canary，未进入 evaluation_2 DEV12 |
| B | `astropy-12962` | `7ebf14d6cfcf` | 旧 CTI canary，未进入 evaluation_2 DEV12 |
| B | `pvlib-python-1239` | `826fb5ebc109` | 旧 CTI2 canary，未进入 evaluation_2 DEV12 |
| B | `scikit-learn-25370` | `9a89a72861b2` | 旧 CTI2 canary，未进入 evaluation_2 DEV12 |
| B | `xarray-4939` | `1b9d7be7b6d5` | 旧 CTI2 canary，未进入 evaluation_2 DEV12 |
| B | `requests-1327` | `aa951213f128` | 旧 CTI2 canary，未进入 evaluation_2 DEV12 |

这些镜像不匹配 DEV12 任一实例，也不是当前 bridge 的三张 frozen 目标；删除会失去这些旧实验的**本地离线重跑缓存**，但不会删除其仓库内身份、准入、结果与封存证据。后续若要回放，需按已记录的官方 digest 重新获取镜像。旧盘镜像仅有名称级元数据，不能当作这些被删镜像的可靠备份。

## 执行结果与复验

- 批次 A 三张、批次 B 七张均逐张执行 `docker image rm --no-prune <精确仓库:latest>`，**10/10 返回成功**；未使用 `-f` 或全局 prune。仅通过 Docker 删除当前 store 的镜像引用/层；没有手工删除/修改 VHDX、volume、项目或 tunnel 文件。Docker 正常操作必然更新活动 VHDX 的内部数据；旧镜像的离线回放缓存不再保留于当前 store，必要时须按历史 RepoDigest 重拉。
- 当前剩余 5 张：`sympy-14711` (`bba8a91b93b4`)、`django-15569` (`748d48e2832b`)、`django-11734` (`d88512b06833`)、`scikit-learn-13313` (`8fab0814156a`)、`alpine:3.20` (`bf8527eb54c3`)。`docker system df` 镜像逻辑 SIZE **37.61 → 9.285 GB**，0 容器/volume/build cache。
- Docker Client/Engine 均 29.4.0；`docker run --pull=never --rm alpine:3.20 /bin/true` 成功。Bridge 本机单测 **5 passed**、本机 `docker_status()` 仍 `docker_ready=True`，其三张 frozen strict-v5 镜像的本地 digest 仍为空，与清理前相同。项目 E1-C evaluation_2 + 旧 gate/preflight 专项 **21 passed**。
- 两个原有 tunnel-client 进程仍在；本地 `/healthz` 和 `/readyz` 均 200。App 私有连接复查仍为清理前相同的 `not connected`；因此只能证明本机 bridge/隧道进程未受破坏，**不能把它表述成 WebCodex 云端端到端控制已验证**。
- D 盘空闲 **4.56 → 4.56 GiB**；活动 VHDX 文件仍 **65,345,159,168 B**，旧盘仍 **72,170,340,352 B**。本轮没有获得 Windows 主机可见的空闲空间，尽管 Docker 内部镜像占用已降约 28.325 GB。
- 旧盘没有外置备份目标（本机仅 C: 33.68 GiB、D: 4.56 GiB 空闲，均不足以存放 67.2 GiB 原盘）；因此**未删除旧盘**。当前非管理员且无 `Optimize-VHD` 命令，活动 Docker/WSL 与 tunnel 仍在运行；未尝试停机、压缩或手工处理 Docker 内部 overlay2/containerd。冷启动复验会中断当前 tunnel，本轮未做；当前打开/运行状态已验证。

## 尚待用户环境具备时的安全后续

1. 若要真正释放旧盘占用的约 67.2 GiB，先提供容量足够的外置盘，复制旧 `.bak` 并比对长度/SHA-256。确认其不是活动盘、验证归档与 Docker 可用后，才讨论删除单个旧 `.bak`；否则保留历史回放能力。
2. 若要把当前盘内释放的镜像层空间返还给 Windows D:，使用官方支持的**离线** VHDX 收缩流程：先备份活动盘或建立可恢复镜像，退出 Docker、关闭 WSL、确认 VHDX 未附加，再在具备相应权限和工具时处理；之后冷启动 Docker 并复查 bridge/tunnel。当前缺少备份空间与管理员条件，故不执行。
3. App 私有连接需在 ChatGPT/WebCodex 中重新选择/连接并实际调用 `docker_status` 验证；两个本地进程 ready 不能替代云端工具调用成功。

## 2026-09-28 — 用户确认仅删除旧 `.bak`，本环境执行受限

用户明确确认仅删除 `D:\docker_related\DockerDesktopWSL\disk\docker_data.vhdx.inactive-20260927.bak`，不删除活动盘。删除前核对：旧文件为普通文件、72,170,340,352 B、最后写入 2026-09-26；活动盘为 `D:\DockerDesktopData\wsl\disk\docker_data.vhdx`，65,345,159,168 B、仍在更新；Docker Client/Engine 29.4.0，本机 bridge `docker_ready=True`，两个 tunnel-client 进程存在。精确单文件 `Remove-Item -LiteralPath` 请求在执行前被当前工具安全策略拒绝；**未改用其他方式绕过**。复核旧/活动文件均仍存在，D: 空闲仍 4.56 GiB，Docker 和本机 bridge 正常。本机手动删除需由用户在文件管理器核对完整文件名后操作；此条记录不代表旧盘已删除。

## 2026-09-28 — 用户手动删除后的复验

用户报告已手动删除旧 `.bak`。本机复核旧文件不存在、活动 `D:\DockerDesktopData\wsl\disk\docker_data.vhdx` 仍存在，D: 空闲 **71.78 GiB**。Docker Client/Engine 均为 29.4.0；`docker run --pull=never --rm alpine:3.20 /bin/true` 成功。Bridge 本机 5 项测试通过，`docker_status()` 返回 `docker_ready=True` 且三张 frozen strict-v5 镜像状态与删除前相同。两个 tunnel-client 进程仍在，两个本地 `/healthz` 与 `/readyz` 均为 200；App 私有连接工具仍返回删除前已有的 `not connected`，故**云端端到端控制未验证**。本轮未冷重启 Docker Desktop；已验证当前运行和容器启动，未验证重启后的状态。旧盘里的离线镜像缓存现已不可本机直接恢复，项目研究文件与活动 VHDX 未删除。
