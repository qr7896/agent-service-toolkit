# 边界验证独立dispatch/execution零调用接线

日期：2026-10-09。之前completion wrapper原normal/target各两次完成，但boundary阶段分别因输出alias影响paid输入回查、dispatch目录被legacy sweep误当started而未执行。两个已开始零调用身份及其原源码/失败保留，不重跑；不影响已完成official F2P1/1/P2P37/37。

新身份`completion-public-sweep-zero-v3`先完整核验paid snapshot与生成seal、已完成own probe，写dispatch-freeze；legacy helper的输出指向独立且尚不存在的execution子目录。保持snapshot在改变alias前验证，只用它作该调用preflight，前后SHA再核验。复用原21变体/base/成功模型patch/公开旧版运行，模型patch/原probe不改，原own四次不重播、provider0。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_completion_sweep_zero
```

offline/no-pull/只读host、原资源/90秒/child10秒约束，phase driver身份校验范围保持；不读official答案/Gold，不称21新task/值等价/泛化。started identity不重跑，失败留存停止。不改系统/代理/tunnel/key，不下载/删除或启用canary/TEST/Fresh30/E2。新专项验证dispatch存在而execution未创建时可以首次运行，且context结束旧配置恢复；不是削弱legacy的no-retry判断。
