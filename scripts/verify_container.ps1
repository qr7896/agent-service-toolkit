# 容器化验证脚本（在装有 Docker 的机器上执行）。
#
# 为什么单独留一个脚本：开发机没有 Docker / podman，WSL 也未安装发行版，
# 所以"镜像能不能构建、容器能不能起来"在本机无法执行。这里把要验的东西固定成脚本，
# 换台机器直接跑，不用每次靠回忆敲命令。
#
# 用法：powershell -ExecutionPolicy Bypass -File scripts/verify_container.ps1

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$compose = @('-f', 'compose.yaml', '-f', 'compose.local-models.yaml')
$failed = @()

function Step($name, [scriptblock]$body) {
    Write-Host "== $name" -ForegroundColor Cyan
    try { & $body; Write-Host "   OK" -ForegroundColor Green }
    catch { Write-Host "   FAIL: $($_.Exception.Message)" -ForegroundColor Red; $script:failed += $name }
}

Step 'docker 可用' {
    docker version --format '{{.Server.Version}}' | Out-Null
}

Step '构建镜像' {
    docker compose @compose build agent_service
}

Step '启动服务' {
    docker compose @compose up -d agent_service
}

Step '服务能起来（/health 探活）' {
    $ok = $false
    foreach ($i in 1..30) {
        try {
            $resp = Invoke-WebRequest -Uri 'http://localhost:8080/health' -TimeoutSec 5 -UseBasicParsing
            if ($resp.StatusCode -eq 200) { $ok = $true; break }
        } catch { Start-Sleep -Seconds 3 }
    }
    if (-not $ok) { throw '30 次探活都没通' }
}

Step 'Agent 列表包含 coding-agent' {
    $info = Invoke-RestMethod -Uri 'http://localhost:8080/info' -TimeoutSec 10
    if (-not ($info.agents.key -contains 'coding-agent')) { throw '缺少 coding-agent' }
}

Step '容器内模型与向量库已挂载' {
    $probe = 'import os, pathlib; m = pathlib.Path(os.environ["EMBEDDING_MODEL_PATH"]); assert m.exists(), m; assert pathlib.Path("/app/src/chroma_db").exists(); print("mounted", m)'
    docker compose @compose exec -T agent_service python -c $probe | Out-Null
}

Step '.codex 数据在容器重建后仍然存在' {
    docker compose @compose exec -T agent_service python -c "import pathlib; pathlib.Path('/app/.codex/probe.txt').write_text('x')" | Out-Null
    docker compose @compose restart agent_service | Out-Null
    Start-Sleep -Seconds 5
    $check = docker compose @compose exec -T agent_service python -c "import pathlib; print(pathlib.Path('/app/.codex/probe.txt').exists())"
    if ($check.Trim() -ne 'True') { throw '重建后 .codex 数据丢失' }
}

Step '收尾：停止容器' {
    docker compose @compose down
}

if ($failed.Count -gt 0) {
    Write-Host "`n未通过：$($failed -join '、')" -ForegroundColor Red
    exit 1
}
Write-Host "`n容器化验证全部通过" -ForegroundColor Green
