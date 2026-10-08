# 零调用补证检查安全续接

2026-10-08。acquisition-context-zero-v1已冻结source后，在读取缓存第二轮compiler.json时失败，尚未执行任何自动source acquisition/模型/probe；原身份和代码不改、不重跑。

新identity acquisition-context-zero-resume-v1先绑定原失败freeze、已seal producer及本driver/协议。仅读已seal generation文件按255个SHA复制到新私有view（不含Gold目录），仅对prefix-replay轮次补上原109-file prefix已绑定的compiler/contract/execution原始bytes。所有副本逐字节对应，不伪造compiler或源，不重执行probe；新增SHA单独收据。继承原SourceCheck，使用新view和namespace继续未执行的Controller源码取得/下一messages与旧/新预算估计。旧gen seal及原层保持。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_acquisition_check_resume
```

0 provider/容器/Gold读，不下载或改系统，started不重试。只零调用实际接线与预算测量，不算模型新生成/品质收益。新paid还需完整method/budget freeze；TEST/canary/Fresh30不打开。
