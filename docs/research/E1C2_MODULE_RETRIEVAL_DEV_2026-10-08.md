# E1C2：模块函数检索根因修复，小额DEV预注册

## Material Passport

- 日期：2026-10-08；模式：旧DEV执行研究，非独立canary。
- 根因：旧检索把`module.function`左侧全部当class owner，公开生产模块函数因此零匹配；不是模型没有所需source。
- 通用修订：先保留原Class.method/裸symbol逻辑；零结果且未超预算时再裸symbol扫描，筛选生产文件basename与module一致的顶层定义。来源标记module-name hint、alias_binding_proven=false；不证明公开alias意图，不改变qualification或公共输入，不用任务ID→文件表。至多两次原32MiB扫描，总64MiB/检索、三候选原上限，保持路径安全与排除测试。
- 沿用环境事实实链、公开interface解释、normal binding守卫。父generation seal只读，Gold不进入模型。两旧DEV来源固定，不扩九准入或canary。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_module_retrieval_dev freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_module_retrieval_dev run
```

`deepseek-flash`、thinking disabled；最多6calls/每题3，总40,000 provider tokens/单题24,000/output2,000/input estimated hard24k/reserve1.4/retry0。新source/namespace `module-retrieval-flash-dev-v1`；原费用独立保留。paid前报告精确命令，用户既有每实验≤100k委托；HTTP失败不重试，不再次run started namespace。冻结前须实际inner hook/真实生产函数检索/下一Human零调用验收。

生成封存后有有限候选才可零模型`... module_retrieval_dev gold`检验；评分隔离、不提升语义或repair。source basename提示不是唯一alias证明，仍未知保持未知。不开canary/C5/TEST/Fresh30/privateTest500/repair/E2，不保证30/30或完美。无大文件下载/系统配置修改。
