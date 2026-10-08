# E1C2：公开旧版本2.19.3，同probe对照结果

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；Origin Mode: run；日期2026-10-08。
- 状态：新零模型版本对照completed；非新生成/Agent修复/独立测试，完整可信门槛未改。
- 用户已下载并核验wheel；本轮仅安全读取14个生产Python/153,698bytes，不安装、不运行setup、不读测试/Gold、不下载新镜像。
- [预注册](E1C2_RELEASE_WITNESS_ZERO_2026-10-08.md)、[实际收据及SHA](../../data/e1c_evaluation_2_release_witness_results.json)。

## 1. 同一程序与条件下的实际观察

| 来源 | 正常对照两次 | 目标两次 | 身份/条件 |
|---|---|---|---|
| 当前base（既有封存观察） | 0、0 | 1、1 | 原validated control/target源、原image/base、dateutil阻断 |
| 官方发行源码2.19.3（本轮新运行） | 0、0 | 0、0 | 四次均验证release版本/路径、manifest、同probe SHA与相同阻断 |

这里0/1是进程returncode。新driver先核验每个只读挂载生产文件SHA、原model probe SHA、实际`__version__`/`__file__`，并实际测试optional import强制失败，再输出nonce marker并运行原probe。4次normal/target正常完成，**公开报告的旧版执行见证得到支持**。没有把错误preflight计作软件故障，没有替换公共值/quote/Oracle、换镜像、安装旧包、清除旧记录。

只改变目标package的公开发行源码（14文件），不是定位到唯一bug修复commit的因果证明；发行包也不是canonical旧Git snapshot。既有base故障/正常观察通过原sealed生成源与本轮source-evidence结果身份核对，不重新计旧实验。单个旧DEV来源的source counterfactual不是完整DEV12、canary或Fresh30成绩。

## 2. 安全与回归

固定wheel49,981bytes/SHA核对；zip原始目录项检查后才落盘，拒绝路径escape/反斜杠/非规范别名/symlink/重复/超预算，排dist-info/外包内容和测试，AST确认版本。首次Ruff E702仅测试语句排版；首两重点各有1个Windows backslash反例失败，未开始容器。根因是ZipInfo写/读自动规范化，改validator读orig_filename与fixture保留raw spelling，断言未削弱；之后13新专项/重点32全过再freeze/run。容器network none/read-only/pull never，90秒硬超时，retry0，无失败重启。

完整 **1680 passed / 4 skipped / 33 warnings，103.79秒**，Ruff/合成compact preflight ready，XML SHA见收据；不是修复率。旧八个generation seal、父zero源码/result、新release源manifest/method/protocol都核验保持。无新增paid/agent下载、镜像删除、Docker重启、IPC/VHD/注册表/代理/tunnel/key更改；全部原始运行日志/源码留本机，Git只脱敏收据/代码/测试/协议。

## 3. 当前已补齐与下一步决定

生产检索→实际复现→normal/target→自动依赖取得→限定属性依赖→公开内层异常对应→条件scope/运行关系→公开旧版本对照，已逐层有实证。并非每一环均有新模型一体化验证：最新两步是封存probe在新方法上的零模型诊断，不偷换成独立成绩。

仍没有公开短名省略import时的作者namespace意图证明，SK另有default/增量等未覆盖义务。现有有限gate故意full_issue_trusted/repair=false；不能因版本对照通过或Gold消除就改True，也不能承诺30/30。

**下一步需要明确资格范围，不再需要下载或盲目付费：**

1. 默认继续完整门槛：保留条件解释unknown，逐项寻找明确公共namespace/全部义务证据；现有证据不足则如实报告。
2. 若用户明确选择另立“有限机制可信”协议：预注册可审计条件、反例、机制证据/完整可信/官方修复三层指标，绑定新整体method与预算；先旧DEV主链正负验收，再不重叠canary。不得回填旧分数、把有限改名完整，或直接开TEST/Fresh30。

所有started source-evidence/release-witness/paid/gold namespace禁止重跑。当前没有新paid/canary/repair命令获准，资格口径未确认前保持严格；0新增模型调用/0tokens。两Roadmap与WebCodex交接已更新，日志集中归档。
