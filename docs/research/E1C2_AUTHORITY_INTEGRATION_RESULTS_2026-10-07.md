# E1-C evaluation_2：辅助源码身份接入与剩余门槛

日期：2026-10-07。Material Passport：ANALYZED；材料为既有四缓存、已核验生产源码身份、零调用资格结果及本轮回归。不是新生成实验、独立 canary 或通用语义证书。

## 1. 实际结果

本轮新增 provider calls/tokens **0/0**，Gold 读取 **0**，machine trusted **0**。旧报告锚版本 Gold 4/4、异常对应 3/4不改。[公开哈希收据](../../data/e1c_evaluation_2_authority_integration_results.json)绑定私有结果；原模型输入、窗口、seal、账本、失败记录不回填。

| 原缓存任务 | 资格 v3 | 解释 |
|---|---|---|
| scikit-learn-13496 | mechanism_supported_candidate | 受限机制支持候选，不是完整语义可信 |
| scikit-learn-26289 | behavior_candidate_mechanism_unproven | 辅助源码身份补齐；行为候选不证明原报告机制 |
| marshmallow-1252 | unknown | 辅助源码身份补齐；公开示例省略 import，范围仍未证明 |
| marshmallow-1359 | mechanism_supported_candidate | 受限机制支持候选，不是完整语义可信 |

接入 `_classes.py` 与 `schema.py` 的 authority：校验 receipt SHA、任务/base/image、原 host 字节、仅 CRLF→LF 投影、exact-base Git blob及已记录 runtime 同摘要。来源仅进入资格审计 overlay，不声称原模型看到额外文件。错误 base/image/digest/path、变更源码与错误 Git blob有负例检查，共8项新单测。

## 2. 仍未解决

公开 Foo/Schema/DateTime 示例省略命名空间：已提出有限范围推断方案，**尚未接受或接入**。同结构与库上下文只能支持显式条件假设，不能把省略 import 当原文承诺、把同名对象当同一语义对象。SK26289 原机制也未证明。

下一步先冻结范围推断/unknown边界，校准歧义、同名影射、修改字面量等跨仓库正负例；再冻结资格、observer、双源码身份、输入与预算的完整方法，按同版 DEV 验证。可信门槛实际通过才选历史排除的新 canary 一次验证 ≥2/3，随后 Agent patch 与独立官方评分。当前不开 canary、sealed TEST、C5、Fresh30、私有 Test500、repair/E2，不保证30/30或一周完美。

## 3. 工程验证与保全

初次 V3 合成 preflight 复制工作区时，服务 SQLite `checkpoints.db-wal/-shm` 瞬时消失导致失败；保留原诊断。修复只在根目录快照复制中排除运行态数据库及两个 sidecar，不删除数据库，不排除嵌套 fixture，不改 E1-C 冻结方法源。

最终 Ruff、预算/V3重点19项通过，合成 preflight `ready=true`；完整回归 **1462 passed / 4 skipped / 33 warnings（89.41秒）**。首次修复前完整回归1461也保留。工程回归不是可信复现或修复成功率。

无新下载、镜像删除、Docker 重启、IPC/VHD/注册表/代理/tunnel/密钥修改。公开同步限源码、单测和脱敏结果；私有 raw/probe/Gold/test/key及本机证据不上传。日志只写集中续档，两份 Roadmap维护当前入口。
