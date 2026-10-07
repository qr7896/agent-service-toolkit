# E1-C evaluation_2：行为分支校准与旧版本对照前置阻塞

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: ANALYZED（行为分支审计；旧版本执行未发生）
- Version Label: behavior_version_results_v1

## 1. 本轮结果

模型调用/tokens **0/0**，Gold读取0，新诊断容器启动0。原资格2机制候选/1行为候选/1unknown、machine trusted0、旧Gold4/4与异常对应3/4均保持。未打开canary、TEST、C5、Fresh30、私有Test500、repair/E2。

按[行为协议](E1C2_BEHAVIOR_GATE_V1_PROTOCOL_2026-10-07.md)对全部四缓存审计，原producer/qualification/exception/pair/doc哈希收据核验：

| 四参考 | 结果 | 限制 |
|---|---|---|
| scikit-learn-13496 | 显式bool构造器keyword接受子义务获得支持 | 非default/增量训练/整个issue可信证明 |
| scikit-learn-26289 | 比较completion假设 | keyword一致但receiver状态未知，ndarray未在base文档明确支持 |
| marshmallow-1252 | 回归假设 | 旧版本行为未执行验证；public namespace约束未知 |
| marshmallow-1359 | 回归假设 | 旧版本行为未执行验证 |

显式请求优先于base文档；一个支持子义务不是可信1/4。闭合签名缺请求keyword、明确bool域、qualified API、normal只差请求参数、原编译AST、源/base身份、该调用行TypeError/同keyword均核验。16专项包含三个合成API名及wrong module/error/line/signature/normal/probe/source反例；合成正例不是三个新真实任务。

## 2. 旧版本对照：准备成功、执行被阻断

[旧版本协议](E1C2_VERSION_WITNESS_V1_PROTOCOL_2026-10-08.md)仅采用公共quote中唯一==/<=旧版，查询本地tag或最多80条包init祖先历史，不下载、不fetch、不看旧tests/Gold。自动导出生产Python包，严格校验每个archive文件字节等canonical Git blob，再计划将原probe只读挂载到同一原镜像中。

MM1359的公开旧版3.0.0rc8已准备：**11份生产文件、152,704 bytes**，原source工作树未变。但随后Docker engine准入失败：当前context为desktop-linux，`dockerDesktopLinuxEngine`命名管道不存在；只读进程检查未见Docker Desktop/backend。**没有driver、没有task执行freeze、没有旧probe执行或完整版本批次result**。不能说旧版成功、失败或完成四条任务；前置失败单独记INFRA_BLOCKED。

初次新增canonical archive检查的专项1failed/40passed，暴露Windows Git换行转换；修复仅在archive命令单次指定core.autocrlf=false/core.eol=lf，保留字节相等断言、不改全局Git。随后重点41项通过。历史rename/delete的缺失blob仅作源不可用继续有限查询，不当probe失败。行为namespace已完成、version namespace已started并失败，两者不重跑；原冻结源码不改。

## 3. 恢复与剩余任务

1. 用户先手动打开Docker Desktop，等Engine running。当前进程未运行，不做IPC/注册表/VHD修复，不复用旧“备份改名并启动一次”授权。若软件启动报错，先提供报错再限定处理，不反复重启。
2. Engine恢复后，另冻resume-only身份/协议，核对原source快照与失败receipt，只推进尚未执行的版本对照；**不要再运行已started的version-witness v1命令**。不下载新镜像，不修改旧freeze/state/result。
3. 旧版实际成功也仅支持同一model程序在该版本完成，不证明全部更早版本、完整公开fixture或全义务。公开报告、source-doc承诺、显式变更请求和实际witness分账；需原base重复失败与独立评分另计，不能best-of。
4. 统一定位/生成/契约窗口/各observer/判别/预算的完整method先冻，再同版DEV/native；完整DEV可信gate实际通过才新历史排除canary一次≥2/3、Agent patch/official，最后旧DEV30/Fresh30/E2。不保证完美或30/30。

目前没有可放行的付费命令；未来仍Flash、精确命令/次数/≤100,000 provider tokens、retry0。无需新镜像下载。没有删除、Docker启动重启、IPC/VHD/registry/proxy/tunnel/key修改；源码旧快照只是约149KiB。原数据/负结果/备份保留，raw/probe/Gold/test/key不上传。[公开收据](../../data/e1c_evaluation_2_behavior_version_results.json)绑定本轮证据。

最终Ruff、预算/V3重点41项与合成preflight通过；完整回归 **1541 passed / 4 skipped / 33 warnings（104.58秒）**，XML及两个冻结method摘要见收据。工程回归不依赖Docker运行，不等于版本对照已执行或repair成功。
