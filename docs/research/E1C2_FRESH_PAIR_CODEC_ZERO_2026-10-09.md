# Fresh pair 已封存响应的零调用解码审计

本次授权paid完整结果已封存：两个来源配对执行门槛均过，原official 1/2；一条repair被固定schema拒绝。新零调用身份`fresh-pair-codec-zero-v1`，只诊断已知JSON元字段，**不是原冻结系统或新模型实验成绩**。

1. 先核验原方法/input freeze、全部producer seal、完成result固定分母/顺序。绑定原freeze/seal/result/paid ledger以及零调用源码、既有canonical_response源码、本协议；不修改原文件。
2. 遍历原两来源，仅选择 operational_pair_valid、received repair且尚未写patch的响应。复用已存在精确兼容器：只接受恰为`type+edits`且`type=json_object`，删元字段；原path/old/new代码字符串完全不改，未知字段继续拒绝。
3. 用原exact source编译器核验公开暴露old文本/base唯一/AST/patch预算。无人工补丁编辑、无新调用、无题号→文件表。不修改probe/正常控制/断言、optional条件。
4. 候选在原两个生成probe上各两次离线验证，使用相同image/base、host只读、network none/pull never。原成功候选不重复生成或评分。
5. 所有零调用生成与执行封存后才调用既有接受显式row/root的独立grade_one，不改全局OUT/preflight；原official反馈不进入任何模型。F2P/P2P/源/log/rc分别记录。
6. 再核验原全部绑定/producer seal字节未变，输出posthoc单独分母；不回填原1/2，不称2/2独立泛化，full_issue_trusted保持false。失败停止不retry。零调用不会消费或扩展paid授权。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fresh_pair_codec_zero
```

该审计验证通用schema兼容价值，不等于新统一方法已完成。之后仅把精确兼容规则纳入新的完整方法/预算freeze，另获精确模型命令授权。完整义务与独立canary门槛尚未过，不启用TEST/Fresh30/E2。没有下载、系统/代理/tunnel或密钥更改。
