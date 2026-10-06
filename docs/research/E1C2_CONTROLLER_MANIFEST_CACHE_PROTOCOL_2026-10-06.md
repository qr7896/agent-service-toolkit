# Controller-owned execution grammar：旧DEV零付费兼容回放

## Material Passport

2026-10-06。V2新生成12请求36689tokens已完整结束，Gold区分3/12、未保留四参考，原响应/状态/账本/评分封存。本次不是新生成，不更改V2源码/方法/输入/响应，不调用provider，不把结果合称新V3模型成绩。只旧DEV，不看五批canary/TEST/C5/Fresh30。

机制：执行manifest由controller语法确定，而不是把元数据格式遵守率当缺陷复现能力。模型A/source与B七合同字段仍旧schema；缓存响应中可忽略唯一execution字段，但不能忽略其他多余字段/输入回显。B固定direct；A正常脚本direct，若整个模块只有imports/普通定义/文档字符串则仅尝试唯一无参同步入口，旧prepare_source仍拒绝参数/装饰/注解/多入口，native fixture API/别名/源码安全/production identity/无网络/正对照/oracle锁定/STOP不变。不根据task ID或测试答案选择文件/入口，不自动hydrate pytester/testdir。

缓存仅原12份raw响应逐字、SHA绑定，任何新需要角色未收集则标controller cache-missing、不补模型调用。upstream usage与new provider0分开，原生成仍是V2的36689tokens。前置method/input须与源freeze逐项相等，真实engine/image每请求/候选检查复用（缓存无SDK请求）。新目录controller-manifest-cache-dev-v3，dummy cache model不读真实API钥匙、不发HTTP，独立preflight/run/gold各一次；缺缓存/旧冻结变更即不宣称完整效果。

差异只能由controller兼容/编译引起，不能归因新模型prompt提升。报告固定12、四参考、Gold区分、机器trusted/人工审查分别列；不是Agent repair、独立泛化或新模型生成。只在该机制验收并有收益后，才另冻真正新生成方法/提示词/预算再做一次完整旧DEV；仍不得马上抽第6批。旧V2 3/12和所有负结果永久保留。
