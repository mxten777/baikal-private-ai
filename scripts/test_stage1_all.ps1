# Stage 1 회귀 일괄 실행
# 1.1 streaming, 1.2b indexing perf, 1.3 restart retry

$ErrorActionPreference = 'Stop'
$results = @()
$start = Get-Date

function Run-Test($name, $script, $params = @{}) {
    Write-Host "`n========================================" -ForegroundColor Yellow
    Write-Host " RUN: $name" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    $t0 = Get-Date
    try {
        & $script @params
        $code = $LASTEXITCODE
    } catch {
        $code = 1
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
    $sec = [int]((Get-Date) - $t0).TotalSeconds
    $script:results += [pscustomobject]@{ Name = $name; ExitCode = $code; Seconds = $sec }
}

Run-Test "Stage 1.1 streaming"      ".\scripts\test_stage1_streaming.ps1"
Run-Test "Stage 1.2b indexing perf" ".\scripts\test_stage1_indexing_perf.ps1" @{ FilePath = "demo_docs/바이칼_취업규칙.pdf"; MaxSec = 180 }
Run-Test "Stage 1.3 restart retry"  ".\scripts\test_stage1_restart_retry.ps1"

$total = [int]((Get-Date) - $start).TotalSeconds
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host " Stage 1 회귀 결과 (총 ${total}s)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
$results | Format-Table -AutoSize
$failed = @($results | Where-Object { $_.ExitCode -ne 0 })
if ($failed.Count -eq 0) {
    Write-Host "ALL PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host "FAIL: $($failed.Count) test(s)" -ForegroundColor Red
    exit 1
}
