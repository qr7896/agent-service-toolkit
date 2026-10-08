# Manual, fixed public release acquisition. No install, no Docker, no credentials.
# Exit VPN/TUN/global routing first: --noproxy disables curl proxies, not OS routes.
$ErrorActionPreference = 'Stop'
$taskRepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskSourceDir = [IO.Path]::GetFullPath((Join-Path $taskRepoRoot '.codex/e1c/evaluation_2/public-version-source/marshmallow-2.19.3'))
if (-not $taskSourceDir.StartsWith($taskRepoRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output directory escaped the project.'
}
$taskFileName = 'marshmallow-2.19.3-py2.py3-none-any.whl'
$taskExpectedSHA = 'cb1e88b8b098ee6d0fb984e40762cb94e200c067426e43496e55b82b563feabf'
$taskExpectedBytes = 49981
$taskReleaseURL = 'https://files.pythonhosted.org/packages/67/21/5655668f3725fbb9872a77e409fabe2530fd3024c7e5c666b5ca2d6178fa/marshmallow-2.19.3-py2.py3-none-any.whl'
$taskFinalFile = Join-Path $taskSourceDir $taskFileName
New-Item -ItemType Directory -Path $taskSourceDir -Force | Out-Null
if (Test-Path -LiteralPath $taskFinalFile) {
    if ((Get-Item -LiteralPath $taskFinalFile).Length -ne $taskExpectedBytes -or
        (Get-FileHash -LiteralPath $taskFinalFile -Algorithm SHA256).Hash -ne $taskExpectedSHA) {
        throw 'Existing file differs; preserved without overwrite. Report this path.'
    }
    Write-Host "Already verified: $taskFinalFile"
    return
}
$taskPartialFile = Join-Path $taskSourceDir ($taskFileName + '.partial-' + [Guid]::NewGuid().ToString('N'))
Write-Host 'Direct curl (no proxy), 49 KiB. Usually seconds; connection timeout 15s, hard timeout 180s, retry 0.'
& curl.exe --noproxy '*' --proto '=https' --proto-redir '=https' --fail --show-error --location `
    --connect-timeout 15 --max-time 180 --max-filesize $taskExpectedBytes --progress-bar `
    --output $taskPartialFile $taskReleaseURL
if ($LASTEXITCODE -ne 0) { throw "Download stopped; partial file preserved: $taskPartialFile" }
if ((Get-Item -LiteralPath $taskPartialFile).Length -ne $taskExpectedBytes -or
    (Get-FileHash -LiteralPath $taskPartialFile -Algorithm SHA256).Hash -ne $taskExpectedSHA) {
    throw "Size/SHA256 mismatch; untrusted file preserved, never installed: $taskPartialFile"
}
Move-Item -LiteralPath $taskPartialFile -Destination $taskFinalFile
Write-Host "VERIFIED size=$taskExpectedBytes SHA256=$taskExpectedSHA"
Write-Host "Source-only archive saved (not installed): $taskFinalFile"
