# E1-C evaluation_2：公共API对照输入与规格支持缺口

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（限快照与参数声明，非全行为证明）
- Version Label: pair_input_contract_results_v1

## 1. 本轮实际推进

provider calls/tokens **0/0**，Gold读取0。两个新离线诊断容器分别运行原normal/target脚本一次，readonly挂载且字节未改；不是重跑旧模型/评分批次。固定四参考：3不适用、1公共API对照，DEV12分母仍12。原资格2机制候选/1行为候选/1unknown、machine trusted0、旧Gold4/4、异常对应3/4保持。

调用可能在参数装饰器中被拒，所以仪器从冻结源码自动定位顶层API调用行，在调用前捕获有限Name/Constant参数，不假称函数体已经进入；所有参数表达式必须无副作用。生产API文件验证host LF、exact-base Git与runtime一致；隔离network none/read-only/pull never、90秒硬超时，原model probe/source/input不变，不输出值/对象repr。

| 字段或结果 | 真实观察 | 结论边界 |
|---|---|---|
| normal / target | 返回码0 / 1，各一次快照 | 不将两次仪器诊断当新的可信任务成绩 |
| feature_names | 两路都是精确ndarray、typed SHA相同 | 只证明本轮捕获的限定表示一致，不证明原公开完整数组 |
| max_depth | 两路int、typed SHA相同；来自冻结literal | 不误称literal是从local读取 |
| positional_0 分类器对象 | 不支持的custom对象，unknown | `all_inputs_match=false`，不能称全部输入一致 |

11专项覆盖type/shape/dtype/content差异、bool/int、list/tuple、object-array/subclass/custom对象、循环/预算、错调用/副作用/缺快照/异常outcome等；只支持明确有界原生表示。[协议](E1C2_PAIR_INPUT_OBSERVER_V1_PROTOCOL_2026-10-07.md)记录限制。ndarray按C-order字节表示计算，依据[NumPy官方文档](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.tobytes.html)，摘要本身不是语义证书。

## 2. 新发现：期待缺口不能靠输入相等填补

随后按[参数文档协议](E1C2_PARAMETER_CONTRACT_V1_PROTOCOL_2026-10-07.md)只读提取NumPy-style Parameters声明，**不序列化Returns/Examples/断言/输出答案**，6专项验证源行、有限语法及未知。原producer seal/source SHA/base Git均核验。

冻结源码中，`export_graphviz`和`export_text`对`feature_names`都写`list of str, default=None`，而模型样本为ndarray。报告`documentation_scope_gap`/`observed_type_not_explicitly_documented`，不是“输入非法”或“该task不是bug”。文档可能过时、明确公共API改动请求可覆盖base文档；正常API接受ndarray不能单独证明target也承诺接受，公开比较报告的completion仍需显式假设。两API的max_depth分别声明int，观察为int，得到有限类型支持。

此发现解释了为什么Gold消除故障、两路共享值相同，仍不能直接认证公共行为意图。不能回填旧Gold/资格，也不能通过继续付费采样解决未定义的期待。

## 3. 下一轮顺序

1. 先冻结行为资格分支与正负例：显式接口变更请求、已有生产文档承诺、比较/回归报告的条件假设分账。明确公共请求不能被旧文档错误否定；未明确的类型扩展不要冒称原承诺。
2. 定义每个分支最小可观测义务及支持范围。优先验证行为/机制，不先扩展任意对象序列化；只有某个契约必须核对训练状态时才另版加受限状态投影，保持unknown和分母。
3. 把定位/生成/规范性合同窗口/scope/各observer/判别与预算完整冻结，再同版旧DEV/native验证，不按task-ID补规则。
4. DEV可信gate实际通过才全历史排除的新canary一次≥2/3；再Agent patch/独立official grade，最后旧DEV30、另授权Fresh30/E2。当前不开新canary/TEST/C5/Fresh30/privateTest500/repair/E2，不保证一周完美或30/30。

当前无新的付费命令可放行；未来仍Flash、先列次数/精确命令/≤100,000 provider tokens、retry0。无需下载，不删除镜像、不重启Docker、不改IPC/VHD/registry/proxy/tunnel/key。旧日志/输入/预算/state/ledger/seal/备份保持，raw/probe/Gold/test/key不上Git。[公开收据](../../data/e1c_evaluation_2_pair_input_contract_results.json)绑定证据。

最终Ruff、重点36项与合成compact preflight通过；完整回归 **1519 passed / 4 skipped / 33 warnings（105.28秒）**。先前1513-pass回归保留；工程passed不是可信复现或修复率。首轮unused import和测试import排序在对应审计freeze前修正，不改已冻结源码/结果，不重跑审计。
