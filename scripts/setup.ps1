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
Write-Host "[3] Ollama 모델 확인 중... (30초 대기)" -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "  LLM 모델 (llama3) 다운로드..." -ForegroundColor Yellow
docker exec baikal-ollama ollama pull llama3

Write-Host "  Embedding 모델 (bge-m3) 다운로드..." -ForegroundColor Yellow
docker exec baikal-ollama ollama pull bge-m3

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " 설정 완료!" -ForegroundColor Green
Write-Host ""
Write-Host " 접속: http://localhost" -ForegroundColor White
Write-Host " 관리자: admin / admin1234" -ForegroundColor White
Write-Host ""
Write-Host " (비밀번호를 반드시 변경하세요)" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Cyan
