# 第二批 canary：终端直连下载交接（2026-09-30）

第二批身份已在读取题目正文前固定：`mwaskom__seaborn-2846`、`marshmallow-code__marshmallow-1343`、`pytest-dev__pytest-8861`。方法冻结 SHA-256 `fd58671dcdb923e70b7f018362682802849c54651655e21d051828e1d6f4d14b`，身份 SHA-256 `a22311ffc4dd41c379e839e5618bccb35164367b35b9a3797bf5f17bb3dba997`；与上一批、DEV12 均无重叠。官方 `task.yaml` 小型元数据已核对；**官方 Docker Hub manifest 直连认证端点当前 TLS 连接被重置**，因此还未形成权威镜像摘要/可下载的传输 seal，镜像 0/3，模型调用 0。镜像站单独返回的压缩量只是估算，不可据此跳过官方比较：Seaborn 1,188,953,663 字节（1.11 GiB）、Marshmallow 984,586,489 字节（0.92 GiB）、pytest 974,545,975 字节（0.91 GiB），合计约 **2.93 GiB**。当前 D: 空闲约 **42.9 GiB**；解压、Docker 导入与临时归档会占更多空间，不能把压缩量当最终磁盘增量。

用户终端复跑已证实同一阻塞：`transport` 在 `auth.docker.io` TLS 握手被重置，随后 PowerShell 的 `throw` 是预期停机守卫；`Stop-Transcript` 正常保存日志。核对现场 `image_transport.json` 不存在、`acquire/` 不存在，**没有开始镜像层下载**。不得把此失败解释为 Docker 导入或层摘要问题。

请先关闭 VPN 的全局/TUN 路由，确认 Docker Desktop 为 **No proxy**。下载脚本自身对 Python HTTPS 请求安装空 `ProxyHandler({})`，镜像层只从摘要一致的直连 `docker.1panel.live` 获取；它不能证明操作系统级 VPN/TUN 没接管路由。可先运行 `Test-NetConnection docker.1panel.live -Port 443 | Select-Object InterfaceAlias,SourceAddress,TcpTestSucceeded` 辅助核对，但 WLAN 名称也不是绝对的无 VPN 证明。

在 PowerShell 终端执行以下完整命令；`transport` 必须先成功，失败时不会开始大文件下载：

```powershell
Set-Location 'D:\codex\working\project20260827'
$canaryLog = 'D:\codex\working\project20260827\.codex\e1c\evaluation_2\canary-v2\download.log'
Start-Transcript -Path $canaryLog -Append
try {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_stage transport
    if ($LASTEXITCODE -ne 0) { throw '官方 Docker Hub manifest 直连核验失败：没有开始下载；勿跳过此门槛。' }
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_stage download --timeout-per-image 21600
    if ($LASTEXITCODE -ne 0) { throw '镜像批次中断：已核验的层和镜像留存，可在查明错误后原命令续跑。' }
} finally {
    Stop-Transcript
}
```

正常输出包含 `[1/3]` 至 `[3/3]`、逐层 `blob n/m`、每约 8 秒的已下载 MiB/速度/ETA、Docker 导入心跳及每张完成摘要。已有完整且核验过的层／镜像会复用；`.partial` 不会冒充成功。脚本每张开始前检查 D: 空闲是否高于 `20 GiB + 6 × 该张压缩 GiB`，不足即停；它不执行 Docker 全局清理，也不触碰活动 VHDX 或 tunnel。按直连 **1–3 MiB/s** 粗算纯传输约 **17–50 分钟**，加归档与导入保守留 **1–3 小时**；若只有 0.2 MiB/s，纯传输约 **4.1 小时**，断线/校验失败会更久。速度与 ETA 以终端实时输出为准。

如果 `transport` 在 `auth.docker.io` 或 `registry-1.docker.io` 仍被重置，可临时使用另一条**不经 VPN/代理的网络**（例如手机热点）只完成官方小型摘要核验，再切回普通直连网络执行 `download`；切网后先确认镜像站出口。不要改成镜像站自证、不要关摘要核验，也不要在未核验时运行官方评分或模型。下载成功后再由 Codex 做 3/3 image ID、exact-base、官方 Base/Gold、公开 issue 输入与冻结 live preflight。
