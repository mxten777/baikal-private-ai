# ===========================================
# BAIKAL Private AI - Windows 초기 설정
# PowerShell에서 실행: .\scripts\setup.ps1
# ===========================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " BAIKAL Private AI - 초기 설정" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. 환경변수 파일 확인
if (-not (Test-Path ".env")) {
    Write-Host "[1] .env 파일 생성..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "  -> .env 생성 완료" -ForegroundColor Green
} else {
    Write-Host "[1] .env 파일 확인 완료" -ForegroundColor Green
}

# 2. Docker Compose 실행
Write-Host "[2] 서비스 시작..." -ForegroundColor Yellow
docker-compose up -d

# 3. Ollama 모델 다운로드
Write-Host "[3] Ollama 준비 확인 중..." -ForegroundColor Yellow
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    $result = docker exec baikal-ollama ollama list 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Ollama 준비 완료" -ForegroundColor Green
        $ready = $true
        break
    }
    Write-Host "  대기 중... ($i/30)" -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
if (-not $ready) {
    Write-Host "Ollama 시작 실패. 'docker logs baikal-ollama' 로 확인하세요." -ForegroundColor Red
    exit 1
}

Write-Host "  LLM 모델 (qwen2.5:7b) 다운로드... (수 분 소요)" -ForegroundColor Yellow
docker exec baikal-ollama ollama pull qwen2.5:7b

Write-Host "  Embedding 모델 (bge-m3) 다운로드... (수 분 소요)" -ForegroundColor Yellow
docker exec baikal-ollama ollama pull bge-m3

Write-Host ""
Write-Host "=========================================="
Write-Host " 설정 완료!" -ForegroundColor Green
Write-Host ""
Write-Host " 접속: http://localhost" -ForegroundColor White
Write-Host " 관리자 계정: .env 파일에서 설정한 값 사용" -ForegroundColor White
Write-Host ""
Write-Host " ⚠️  .env 파일의 SECRET_KEY, POSTGRES_PASSWORD," -ForegroundColor Red
Write-Host "    DEFAULT_ADMIN_PASSWORD를 반드시 변경하세요!" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Cyan
