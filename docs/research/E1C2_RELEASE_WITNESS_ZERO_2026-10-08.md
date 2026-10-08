# E1C2：2.19.3公开发行源码对照，零模型预注册

## Material Passport

- 日期2026-10-08；Origin Skill: academic-research-suite / experiment-agent；Mode: run。
- 用户已手动下载固定公开wheel，49,981bytes/SHA256 `cb1e88b8b098ee6d0fb984e40762cb94e200c067426e43496e55b82b563feabf`。
- 只匹配source-evidence-zero中expected_quote明确`==2.19.3`且单一生产package的旧DEV来源，不用任务ID选文件；没有新canary/TEST/Fresh30。
- 原same control/target源字节、镜像、base、optional阻断不变；仅只读挂载旧发行包生产Python。发行源码不是canonical Git snapshot/官方评分，不读Gold，不输入模型，不安装本机/容器，不运行setup.py或下载。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_release_witness
```

0calls/0provider tokens；新namespace `public-release-witness-zero-v1`先冻结源/协议/wheel/父result/原generation seal/manifest。

zip目录项拒绝绝对/反斜杠/冒号/..路径、symlink和重复生产路径，排除dist-info与外包内容、不读取tests；生产Python1MB/file、64files/2MB总量、archive1MB，实际AST声明版本必须匹配，所有验证发生在落盘前。host只读AST/字节，不import包。

4次预注册容器（normal两次、target两次），每次network none/read-only/pull never/90秒超时、retry0。driver核验release源SHA、原probe SHA、实际package版本和/e1c2_release导入路径，并确认相同optional import强制失败；每次自己的source marker，先通过preflight才计program rc。preflight失败/基础设施失败/timeout留档停止，不自动重试namespace。语义失败不伪装infra；完整对照记录保留。

旧版normal/target同probe四次rc0才记reported-version witness supported；若旧版失败则如实记负证据。两者均不自动证明公开namespace意图、完整issue语义、Agent修复或canonical旧Git内容。当前完整资格口径保持、trusted/repair/canary=false，结果回写日志/收据，不修改旧trial或Gold结果。
