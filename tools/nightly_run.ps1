# YoRuu nightly report wrapper (PHASE 6 M6.4)
param(
    [string]$Config = "config/yoruu.yaml",
    [string]$LogDir = "logs"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$logFile = Join-Path $LogDir "nightly_run.log"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$ts] start nightly generate" | Add-Content -Path $logFile -Encoding utf8
uv run yoruu nightly generate --config $Config 2>&1 | Add-Content -Path $logFile -Encoding utf8
$code = $LASTEXITCODE
"[$ts] exit=$code" | Add-Content -Path $logFile -Encoding utf8
exit $code
