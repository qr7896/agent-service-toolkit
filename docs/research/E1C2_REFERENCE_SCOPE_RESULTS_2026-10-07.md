# E1-C evaluation_2：条件范围与静态重导出链结果

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（零调用静态审计，非运行时语义复现）
- Version Label: reference_scope_results_v1

## 1. 本轮实际完成

新增模型调用/tokens **0/0**，Gold读取0。原资格v3仍是2机制支持候选、1行为候选、1unknown，machine trusted0；旧Gold4/4与异常对应3/4不改。未运行新容器故障实验，不打开新canary、sealed TEST、C5、Fresh30、私有Test500、repair/E2。

按[范围协议](E1C2_REFERENCE_SCOPE_V1_PROTOCOL_2026-10-07.md)执行四缓存审计：3项显式结构支持、1项条件结构支持。后者仅说明公开输入结构可在列明假设的namespace中一致，不是可信复现。完整引用路径、唯一生产定义、冻结host SHA与LF/exact-base Git身份均检查；同末尾名称不足以通过。原public facts/model输入不修改，未知不回填为PASS。

按[重导出链协议](E1C2_EXPORT_CHAIN_V1_PROTOCOL_2026-10-07.md)自动审计该条件样本的两个引用：`marshmallow.Schema → marshmallow.schema.Schema`与`marshmallow.fields.DateTime`均得到静态链支持，每个节点host LF均等exact-base Git blob。没有task-ID→文件表或人工选文件；这是**两条引用链，不是两道新任务通过**。静态链不证明公开省略namespace的意图、装饰器/metaclass/副作用或实际运行对象。

23项新增单测（范围11、export链12）；范围正例为两个合成库，不冒称两个新真实仓库实验。负例包含完整路径错位、改字面量、外部同名库、alias/定义影射、star/条件/动态/循环/多重export、base变化和模块位置歧义；模型alias拼写变化、同一限定对象的直接import保留。

## 2. 异常及保全

初次范围单测1 failed/9 passed：错误fixture把同一个`alpha.fields.DateTime`的直接import当成不同对象。改为真正不同的`alpha.DateTime`反例，并新增同一对象正例，保留拒绝断言与覆盖；随后11项通过。

首轮Ruff发现import排序，但范围审计已开始。原运行源码完整保存在私有`reference-scope-zero-v1/source-snapshot.py`，SHA与原freeze一致；公开源码仅交换两个import顺序，另记SHA与可重建差异，**没有重跑或修改审计结果/原freeze**。后续Ruff通过。export链在专项检查通过后才开始，源码不再改。

## 3. 剩余门槛与下一步

1. 将静态链与原模型probe实际使用对象对应；需要另版离线instrumentation协议，不能从静态链跳到runtime证书。路径选择由本轮链输出自动派生，不手选、不开网络、无Gold提示。
2. 对有限的公开行为义务做正负校准：显式接口请求、同输入API对照、带版本/依赖条件的回归分别处理；有条件假设与报告原机制分账。缺意图证据仍unknown，不按旧题补规则。
3. 完整方法（定位、生成、scope、observer、source身份、判别及预算）统一冻结，再同版旧DEV/native验证。四参考不能报全DEV12，旧九准入与固定12分母分别列出。
4. DEV可信门槛实际达成，才冻结历史排除的新canary一次≥2/3；通过后才Agent patch/独立official grade，最后旧DEV30与另授权Fresh30/E2。

当前没有新的付费命令可放行。任何未来调用仍Flash、明确次数、≤100,000 provider tokens、retry0；不以无限调参保证完美或30/30。无下载/删除镜像、Docker重启、IPC/VHD/注册表/代理/tunnel/密钥改动。

工程验证及哈希见[公开收据](../../data/e1c_evaluation_2_reference_scope_results.json)；日志只集中续档，历史负结果、source/state/ledger/seal与备份保留。

最终Ruff通过，范围/authority/预算V3重点38项通过，合成compact preflight `ready=true`；完整回归 **1485 passed / 4 skipped / 33 warnings（84.67秒）**，不是修复成功率。
