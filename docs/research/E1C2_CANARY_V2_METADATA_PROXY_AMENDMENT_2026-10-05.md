# 第二批 canary：小型官方元数据代理传输修订

日期：2026-10-05。用户明确允许仅小型官方元数据使用本机 7892 代理。新基础设施执行身份为 `e1c2-canary-v2-metadata-proxy-v1`，产物另存 `.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/`。

原 v2 的 14 份方法文件、方法 freeze、选择身份及原目录保留。本修订继续使用已选三题，固定分母 3；这是同一 cohort 的基础设施修订，不是重新抽样的新 canary。修订在新题正文、生产源码、Gold、官方测试及模型结果均未读取时封存。定位、v4 提示、模型参数、14,000/42,000 provider token 上限和 ≥2/3 门槛继续来自原协议。未来 live 必须另冻包含本修订摘要的执行身份，不能直接运行原 v2 live 命令并声称全程直连。

## 传输范围

代理固定 `http://127.0.0.1:7892`，仅限 HTTPS `auth.docker.io/token` 和 `registry-1.docker.io/v2/.../manifests/...`。每响应最多 200,000 字节，官方最多 9 次请求、累计响应正文最多 2,000,000 字节；禁止跳转、无自动重试，不记录令牌。响应正文预算不包含 HTTP/TLS 开销。镜像站 manifest 仍经空 ProxyHandler 直连；代理客户端拒绝 blob URL。官方/镜像站顶层与 linux/amd64 摘要、层数量和压缩量须完全相同才写 seal。

下载阶段复用原 SHA/大小、解压 diff-id 和 Docker image ID 校验器，始终从 `docker.1panel.live` 直连镜像层；先核对本地 Docker engine，随后逐张检查磁盘余量。urllib 明确绕过系统 HTTP 代理；用户必须关闭 VPN 全局/TUN，应用代码不能证明 OS 路由未经过 VPN。Docker 保持 No proxy。下载与导入由用户终端执行，零 provider 调用。

## 执行入口

先在允许本机 7892 访问的网络下执行一次小型核验：

```powershell
Set-Location 'D:\codex\working\project20260827'
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy freeze
if ($LASTEXITCODE -eq 0) {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy transport
}
```

seal 写成后关闭 VPN 全局/TUN，切回普通网络；以下新命令只读取已保存 seal 并直连镜像站，不再请求官方 registry：

```powershell
Set-Location 'D:\codex\working\project20260827'
$imageLog = 'D:\codex\working\project20260827\.codex\e1c\evaluation_2\canary-v2-metadata-proxy-v1\download.log'
Start-Transcript -Path $imageLog -Append
try {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy download --timeout-per-image 21600
    if ($LASTEXITCODE -ne 0) { throw '下载停止；完整核验层与已加载镜像保留。请保留输出供检查。' }
} finally {
    Stop-Transcript
}
```

终端有 `[1/3]`、每层 MiB/速度/ETA、解压/归档进度和 Docker 导入心跳。压缩总量以核验记录为准；临时归档和解压后磁盘占用更高。按 1–3 MiB/s 估计纯下载约 17–50 分钟，归档/导入保守预留 1–3 小时；0.2 MiB/s 的纯传输约 4.1 小时。核验失败、低磁盘余量或 engine 未就绪均原位停止。

下载完成后由 Codex 核对 3/3 image ID，再运行本模块 `admit` 和 `public` 零模型阶段。尚无修订绑定的付费 runner freeze；sealed TEST/C5/Fresh30 继续关闭。原 direct-only 传输尝试保留为基础设施负记录，不是实验失败样本结果。
