# 受限旧DEV v3：固定json_object格式元数据兼容

完整方法和选题继承[v1](E1C2_BOUNDED_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md)，降预算guard继承[v2](E1C2_BOUNDED_RUNTIME_DEV_V2_PROTOCOL_2026-10-07.md)。v1实际12请求24976tokens，全被单键schema拒绝。v2仅零模型准备与真实两仓库smoke完成，**没有freeze/付费run/评分**；缓存格式审计发现12条type不是动作名而是固定`json_object`，因此v2不兼容，原代码/smoke不修改、不重跑。先前“明确type动作标记”的诊断不准确，以本次实际值核验为准。

v3仅在`type == json_object`时剥离该固定格式标记，再接受唯一canonical动作或完整原七字段B合同；字段/source/quote/oracle/assertion不改。未知type、extra echo/execution/shell/缺字段/路径参数绕过仍拒绝。不丢弃任意metadata、不读取Gold、不修现有30题断言，不把缓存解码成功报成新生成成绩。

新目录`bounded-runtime-dev-v3`、`bounded-runtime-zero-smoke-v3`；三题身份/issue/source/prompt不变。Flash最多12请求/每题4，整批60000/每题20000/输出2000，temp0/nonthinking/retry0，实际budgeted invoke与freeze一致。先相关单测/完整回归、12缓存格式零调用审计和另立真实两仓库smoke通过，再冻结、列精确live命令后按用户≤100000授权边界一次运行；v1的费用与v3分账。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v3 smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v3 preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v3 run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev_v3 gold
```

每个入口once，失败留存；已有state/ledger不重跑，SDK错误不重试，固定分母screen3/原DEV12不变。仅源码窗口与自生成执行反馈允许进入模型，评分侧Gold只独立判别；semantic audit仍单列、机器trusted=false。合成通过/格式解码/工程tests不是repro或repair成绩，不按v1/v3成功项best-of合并。完整旧DEV、四参考、独立canary≥2/3与Agent repair还未过gate，TEST/C5/Fresh30/private Test500/E2继续关闭。
