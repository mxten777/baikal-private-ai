#!/bin/bash
# ===========================================
# BAIKAL Private AI - 초기 설정 스크립트
# 설치 후 최초 1회 실행
# ===========================================

set -e

echo "=========================================="
echo " BAIKAL Private AI - 초기 설정"
echo "=========================================="

# 1. 환경변수 파일 확인
if [ ! -f ".env" ]; then
  echo "[1] .env 파일 생성..."
  cp .env.example .env
  echo "  → .env 생성 완료 (필요 시 수정하세요)"
else
  echo "[1] .env 파일 확인 완료"
fi

# 2. Docker Compose 실행
echo "[2] 서비스 시작..."
docker-compose up -d

# 3. Ollama 모델 확인 및 다운로드
echo "[3] Ollama 준비 확인 중..."
for i in $(seq 1 30); do
  if docker exec baikal-ollama ollama list > /dev/null 2>&1; then
    echo "  Ollama 준비 완료"
    break
  fi
  echo "  대기 중... ($i/30)"
  sleep 5
done

echo "  LLM 모델 (qwen2.5:7b) 다운로드... (수 분 소요)"
docker exec baikal-ollama ollama pull qwen2.5:7b

echo "  Embedding 모델 (bge-m3) 다운로드... (수 분 소요)"
docker exec baikal-ollama ollama pull bge-m3

echo ""
echo "=========================================="
echo " 설정 완료!"
echo ""
echo " 접속: http://localhost"
echo " 관리자 계정: .env 파일에서 설정한 값 사용"
echo ""
echo " ⚠️  .env 파일의 SECRET_KEY, POSTGRES_PASSWORD,"
echo "    DEFAULT_ADMIN_PASSWORD를 반드시 변경하세요!"
echo "=========================================="
