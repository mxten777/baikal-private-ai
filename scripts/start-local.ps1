param([switch]$Stop)

$ROOT = Split-Path $PSScriptRoot -Parent
$PID_FILE = "$ROOT\.pids"

# ── STOP ──────────────────────────────────────────────────────────
if ($Stop) {
    Write-Host ">> Stopping services..." -ForegroundColor Yellow
    if (Test-Path $PID_FILE) {
        $pids = Get-Content $PID_FILE
        foreach ($p in $pids) {
            try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
        }
        Remove-Item $PID_FILE -Force
    }
    @(8000, 3000) | ForEach-Object {
        $proc = Get-NetTCPConnection -LocalPort $_ -State Listen -ErrorAction SilentlyContinue |
                Select-Object -First 1 -ExpandProperty OwningProcess
        if ($proc) { Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue }
    }
    Write-Host ">> Done." -ForegroundColor Green
    exit 0
}

# ── BANNER ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "       BAIKAL Private AI  -  Local Demo      " -ForegroundColor Cyan
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""

# ── [1] PRE-FLIGHT ────────────────────────────────────────────────
Write-Host "[1/4] Pre-flight checks..." -ForegroundColor Yellow

$models = ollama list 2>$null | Select-String "qwen2.5:7b|bge-m3"
if (($models | Measure-Object).Count -lt 2) {
    Write-Host "  [!] Pulling Ollama models (this may take a while)..." -ForegroundColor Red
    ollama pull qwen2.5:7b
    ollama pull bge-m3
} else {
    Write-Host "  [ok] Ollama models ready  (qwen2.5:7b, bge-m3)" -ForegroundColor Green
}

$pgSvc = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Where-Object Status -eq "Running"
if (-not $pgSvc) {
    Write-Host "  [!] Starting PostgreSQL..." -ForegroundColor Yellow
    $svcName = (Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1).Name
    if ($svcName) { Start-Service $svcName; Start-Sleep -Seconds 3 }
    else { Write-Host "  [x] PostgreSQL not found." -ForegroundColor Red; exit 1 }
} else {
    Write-Host "  [ok] PostgreSQL running" -ForegroundColor Green
}

@(8000, 3000) | ForEach-Object {
    $proc = Get-NetTCPConnection -LocalPort $_ -State Listen -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty OwningProcess
    if ($proc) {
        Write-Host "  [!] Port $_ in use (PID $proc) -> killing..." -ForegroundColor Yellow
        Stop-Process -Id $proc -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

# ── [2] BACKEND ───────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Starting Backend (FastAPI :8000)..." -ForegroundColor Yellow

$backendJob = Start-Process powershell -ArgumentList @(
    "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command",
    "Set-Location '$ROOT\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | Out-Null"
) -PassThru

$backendReady = $false
for ($i = 1; $i -le 15; $i++) {
    $pct = [int](($i / 15) * 100)
    Write-Progress -Activity "Backend" -Status "Waiting for FastAPI to respond... ($i/15)" -PercentComplete $pct
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-RestMethod http://127.0.0.1:8000/api/health -TimeoutSec 2 -ErrorAction Stop
        if ($resp.status -eq "ok") { $backendReady = $true; break }
    } catch {}
}
Write-Progress -Activity "Backend" -Completed

if ($backendReady) {
    Write-Host "  [ok] Backend ready" -ForegroundColor Green
} else {
    Write-Host "  [x] Backend failed to start." -ForegroundColor Red
    Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# ── [3] FRONTEND ──────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Starting Frontend (React :3000)..." -ForegroundColor Yellow

$frontendJob = Start-Process powershell -ArgumentList @(
    "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command",
    "Set-Location '$ROOT\frontend'; `$env:BROWSER='none'; npm start 2>&1 | Out-Null"
) -PassThru

$frontendReady = $false
for ($i = 1; $i -le 20; $i++) {
    $pct = [int](($i / 20) * 100)
    Write-Progress -Activity "Frontend" -Status "Waiting for React dev server... ($i/20)" -PercentComplete $pct
    Start-Sleep -Seconds 3
    $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 3000 -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null
    if ($conn) { $frontendReady = $true; break }
}
Write-Progress -Activity "Frontend" -Completed

if ($frontendReady) {
    Write-Host "  [ok] Frontend ready" -ForegroundColor Green
} else {
    Write-Host "  [x] Frontend failed to start." -ForegroundColor Red
}

@($backendJob.Id, $frontendJob.Id) | Set-Content $PID_FILE

# ── [4] OPEN BROWSER ─────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
Start-Process "http://localhost:3000"

# ── READY BANNER ─────────────────────────────────────────────────
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "  [READY] BAIKAL Private AI is running!" -ForegroundColor Green
Write-Host ""
Write-Host "  URL   : http://localhost:3000" -ForegroundColor White
Write-Host "  API   : http://localhost:8000" -ForegroundColor White
Write-Host "  Login : admin / admin1234" -ForegroundColor White
Write-Host ""
Write-Host "  Stop  : .\scripts\start-local.ps1 -Stop" -ForegroundColor DarkGray
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host ""