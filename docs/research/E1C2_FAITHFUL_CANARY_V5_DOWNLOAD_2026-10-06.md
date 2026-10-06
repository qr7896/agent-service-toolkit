# Faithful canary v5：用户终端直连下载

方法先冻结、metadata-only排除304历史身份后选SymPy-22080、Sphinx-9180、pytest-7749，固定三题无替补；这是新独立canary，不是Fresh30，也不是重新测试已看样本。官方/直连mirror摘要3/3一致，官方Docker小metadata经已授权7892共7请求/25899正文bytes；issue/Gold未读，blob/model0。[摘要收据](../../data/e1c_evaluation_2_faithful_canary_v5_transport_receipt.json)。

压缩层合计3162964124bytes≈2.946GiB（十进制3.163GB），每题1.018/1.020/0.908GiB；安装/临时占用更大，不能把压缩层量当Docker数据盘增量。D现场约38.64GiB，逐张运行空间守卫，最大要求约26.123GiB空闲；后续镜像、源码和缓存增长可能触发停止，不能保证后两张必够。不做prune/删镜像/VHD，保留所有IPC备份。

按平均1–5MiB/s，纯传输约10–50分钟，加校验/导入粗估25–90分钟；0.2MiB/s纯传输约4.2小时。实际以逐层速率/ETA为准；每张硬上限6小时不是时间承诺。输出包括第几张、总字节/百分比/速度/ETA和Docker导入心跳；哈希不符或磁盘守卫触发即停，已核验缓存保留。

先关闭VPN全局与TUN/透明转发，Docker Desktop保持No proxy，并确认Docker正常Running。空ProxyHandler能绕开显式/系统代理，**不能证明系统级TUN或路由没有走VPN**。下载读取已经缓存的官方seal，blob只从`docker.1panel.live`直连，不走7892、不请求官方大blob。不要运行旧v4下载命令。

复制到PowerShell：

```powershell
Set-Location 'D:\codex\working\project20260827'
Start-Transcript -Path '.codex\e1c\evaluation_2\faithful-canary-v5\download.log' -Append
try {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_canary_v5 download --timeout-per-image 21600
    if ($LASTEXITCODE -ne 0) { throw '下载中断：保留缓存和日志，不启动模型。' }
} finally {
    Stop-Transcript
}
```

这里`--offline`只限制uv依赖解析，不表示镜像脚本离线；脚本的直连策略由空代理opener与cached seal控制。成功最后应见`verified_loaded: 3`、`fixed_denominator: 3`、`provider_calls: 0`。不要把进度100%当整个镜像已导入；需等每张verified import complete。

下载完成后只回复结果/日志；下一步本机admit（六项官方Base/Gold，失败仍留分母）→public（仅双准入题公开输入/生产）→preflight→列精确Flash付费命令/≤6请求/60000token→一次run/gold。不自动provider重试，不在canary调参。≥2/3且行为审查一致后才能另冻Agent repair，TEST/C5/Fresh30/E2仍关闭。不能只凭DEV5/12或工程1151passed跳过独立门槛。

WebCodex缺本机identity/seal/cache/镜像/源工作区或受限桥接执行器即报告INFRA_BLOCKED，不重新抽题、不制造stub结果、不向聊天索要密钥；方法或文件SHA不同也停止。原始metadata/seal在本机`.codex`，公开Git仅有安全摘要/身份/方法，不含Gold或密钥。
