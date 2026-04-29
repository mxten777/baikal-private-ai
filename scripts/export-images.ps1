# ============================================================
# BAIKAL Private AI - Docker 이미지 오프라인 내보내기 (Windows)
# 인터넷이 되는 환경에서 실행하여 폐쇄망에 전달할 패키지 생성
# ============================================================
#
# 사용법:
#   .\scripts\export-images.ps1
#   .\scripts\export-images.ps1 -OutputDir D:\baikal-offline
#
# 산출물:
#   <OutputDir>/baikal-images.tar  (gzip 미사용 — Windows 호환)
#   <OutputDir>/SHA256SUMS.txt
#   <OutputDir>/docker-compose.cpu.yml, .env.example, nginx/, scripts/
#
[CmdletBinding()]
param(
    [string]$OutputDir = ".\offline-package",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BAIKAL Private AI - Windows 오프라인 패키지 생성"             -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 프로젝트 루트: $ProjectRoot"
Write-Host " 출력 디렉토리: $OutputDir"
Write-Host ""

# Docker 가용성 확인
try {
    docker version --format '{{.Server.Version}}' | Out-Null
}
catch {
    Write-Error "Docker 데몬에 접근할 수 없습니다. Docker Desktop이 실행 중인지 확인하세요."
    exit 1
}

# 출력 디렉토리 준비
$null = New-Item -ItemType Directory -Path $OutputDir -Force

# 1. 이미지 빌드 (옵션)
if (-not $SkipBuild) {
    Write-Host "[1/5] Docker 이미지 빌드..." -ForegroundColor Yellow
    Push-Location $ProjectRoot
    try {
        docker compose -f docker-compose.cpu.yml build
        if ($LASTEXITCODE -ne 0) { throw "빌드 실패" }
    }
    finally { Pop-Location }
}
else {
    Write-Host "[1/5] 빌드 스킵 (-SkipBuild)" -ForegroundColor DarkYellow
}

# 2. 베이스 이미지 Pull
Write-Host "[2/5] 의존 이미지 Pull..." -ForegroundColor Yellow
$baseImages = @(
    "pgvector/pgvector:pg16",
    "ollama/ollama:latest",
    "nginx:alpine"
)
foreach ($img in $baseImages) {
    Write-Host "    pulling $img"
    docker pull $img
    if ($LASTEXITCODE -ne 0) { throw "$img pull 실패" }
}

# 3. 빌드된 이미지 태그 추출 (compose project 이름은 디렉토리명)
Write-Host "[3/5] BAIKAL 빌드 이미지 확인..." -ForegroundColor Yellow
$buildImages = @(
    "baikal-private-ai-backend",
    "baikal-private-ai-frontend"
)
$existing = docker images --format '{{.Repository}}:{{.Tag}}'
$allImages = @()
$allImages += $baseImages
foreach ($img in $buildImages) {
    $match = $existing | Where-Object { $_ -like "$img*" } | Select-Object -First 1
    if (-not $match) {
        Write-Warning "$img 이미지가 없습니다. -SkipBuild 옵션을 제거하고 다시 실행하세요."
    }
    else {
        $allImages += $match
    }
}

# 4. tar로 저장 (gzip 미사용 — Windows에서 PowerShell만으로 풀 수 있도록)
$tarPath = Join-Path $OutputDir "baikal-images.tar"
Write-Host "[4/5] 이미지 저장: $tarPath" -ForegroundColor Yellow
docker save -o $tarPath @allImages
if ($LASTEXITCODE -ne 0) { throw "docker save 실패" }
$sizeMB = [math]::Round((Get-Item $tarPath).Length / 1MB, 1)
Write-Host "    저장 완료 ($sizeMB MB)"

# 5. 설정 파일 복사 + 체크섬
Write-Host "[5/5] 설정 파일 + SHA256 체크섬..." -ForegroundColor Yellow
Copy-Item (Join-Path $ProjectRoot "docker-compose.cpu.yml") $OutputDir -Force
Copy-Item (Join-Path $ProjectRoot ".env.example") (Join-Path $OutputDir ".env.example") -Force
Copy-Item (Join-Path $ProjectRoot "nginx") $OutputDir -Recurse -Force
Copy-Item (Join-Path $ProjectRoot "scripts") $OutputDir -Recurse -Force

# 체크섬 생성
$sumsPath = Join-Path $OutputDir "SHA256SUMS.txt"
$null = Remove-Item $sumsPath -ErrorAction SilentlyContinue
Get-ChildItem $OutputDir -Recurse -File | ForEach-Object {
    if ($_.Name -eq "SHA256SUMS.txt") { return }
    $rel = $_.FullName.Substring((Resolve-Path $OutputDir).Path.Length + 1)
    $hash = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLower()
    "$hash  $rel" | Out-File -FilePath $sumsPath -Append -Encoding utf8
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " 패키지 생성 완료"                                            -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host " 위치 : $OutputDir"
Write-Host " tar  : $tarPath ($sizeMB MB)"
Write-Host " 체크섬: $sumsPath"
Write-Host ""
Write-Host " 폐쇄망에서 검증:"
Write-Host "   Get-FileHash baikal-images.tar -Algorithm SHA256"
Write-Host ""
Write-Host " 폐쇄망에서 가져오기:"
Write-Host "   docker load -i baikal-images.tar"
Write-Host "   docker compose -f docker-compose.cpu.yml up -d"
Write-Host ""
