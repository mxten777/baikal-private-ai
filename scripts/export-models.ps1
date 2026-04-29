# ============================================================
# BAIKAL Private AI - Ollama 모델 오프라인 내보내기 (Windows)
# ============================================================
#
# 사용법:
#   .\scripts\export-models.ps1
#   .\scripts\export-models.ps1 -OutputDir D:\baikal-offline -Models @("qwen2.5:7b","bge-m3")
#
[CmdletBinding()]
param(
    [string]$OutputDir = ".\offline-package",
    [string[]]$Models = @("qwen2.5:7b", "bge-m3")
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Ollama 모델 다운로드 및 패키징 (Windows)"                    -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Ollama 설치 확인
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Error "Ollama가 설치되어 있지 않습니다. https://ollama.com 에서 설치 후 재실행하세요."
    exit 1
}

# 모델 디렉토리 위치 (Windows 기본 경로)
$ollamaDir = Join-Path $env:USERPROFILE ".ollama"
if (-not (Test-Path $ollamaDir)) {
    Write-Error "Ollama 데이터 디렉토리 미발견: $ollamaDir"
    exit 1
}

# 모델 다운로드
Write-Host "[1/2] 모델 Pull..." -ForegroundColor Yellow
foreach ($m in $Models) {
    Write-Host "    pulling $m"
    ollama pull $m
    if ($LASTEXITCODE -ne 0) { throw "$m pull 실패" }
}

# 패키징
$null = New-Item -ItemType Directory -Path $OutputDir -Force
$tarPath = Join-Path $OutputDir "ollama-models.tar"
Write-Host "[2/2] 모델 디렉토리 압축: $tarPath" -ForegroundColor Yellow

# Windows 10+ 의 내장 tar 사용
$tarExe = Get-Command tar -ErrorAction SilentlyContinue
if (-not $tarExe) {
    Write-Error "tar.exe 를 찾을 수 없습니다. Windows 10 1803 이상 또는 MSYS2 tar 가 필요합니다."
    exit 1
}

# -C 로 디렉토리 변경 후 모든 내용 압축
& tar.exe -cf $tarPath -C $ollamaDir .
if ($LASTEXITCODE -ne 0) { throw "tar 실패" }

$sizeMB = [math]::Round((Get-Item $tarPath).Length / 1MB, 1)
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " 모델 패키지 완료"                                            -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host " 위치 : $tarPath ($sizeMB MB)"
Write-Host ""
Write-Host " 폐쇄망에서 압축 해제:"
Write-Host "   tar -xf ollama-models.tar -C `$env:USERPROFILE\.ollama"
Write-Host ""
