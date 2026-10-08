# 三组原始响应的零调用解码与独立评分诊断

日期：2026-10-08；身份 `three-arm-decoding-zero-v1`。原三cell试验已完成，3请求/15,764tokens：standard/strict因额外`type: json_object`字段被拒，standard_evidence给出同值替换，被编译为无改动。没有真实候选容器评分；原试验固定1旧DEV/3cell，成功0，结果和seal不改。

本轮用户授权继续改进。先不新增付费，验证是否被传输外壳阻断：仅当JSON对象恰为`type`与`edits`且`type == json_object`时删除元字段；只有`edits`的对象原样接受，其余拒绝。所有path/old/new字符串不改，原production/exposure/唯一替换/AST约束保持。相同old/new输出仍是abstain，不能包装成候选或成功。

从原已seal输入和response生成新独立诊断产物，冻结自身方法/协议、原freeze/seal/result/source SHA；全部转译产物seal后才调用原独立official scorer，在同一冻结镜像/base、无网络/no-pull容器测试唯一非空候选。原paid账本不修改，新ledger为空，不调用模型；没有人工写补丁、追加测试答案或Gold代码输入。official材料仍仅scorer读取。

精确零模型命令：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_decode_audit
```

既定评分timeout=900秒；started namespace不重跑。结果是**后验解码诊断**，不是原冻结系统成功、重新生成、独立泛化或三组正式效应。即使补丁修复成功也不得回填原0/3；下一次真正采用兼容解码，须单独整体freeze和精确付费命令授权。不开canary、TEST、Fresh30、E2；不改Docker配置/代理/tunnel/密钥、不下载/删除。
