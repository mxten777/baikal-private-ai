#!/bin/bash
# ===========================================
# BAIKAL Private AI - Docker 이미지 내보내기
# 인터넷이 되는 환경에서 실행
# ===========================================

set -e

EXPORT_DIR="./offline-package"
mkdir -p "$EXPORT_DIR"

echo "=========================================="
echo " BAIKAL Private AI - 오프라인 패키지 생성"
echo "=========================================="

# 1. Docker 이미지 빌드
echo "[1/4] Docker 이미지 빌드 중..."
docker-compose build

# 2. 필요한 이미지 Pull
echo "[2/4] 의존 이미지 Pull..."
docker pull pgvector/pgvector:pg16
docker pull ollama/ollama:latest
docker pull nginx:alpine

# 3. 이미지 저장
echo "[3/4] Docker 이미지 저장 중..."
docker save \
  pgvector/pgvector:pg16 \
  ollama/ollama:latest \
  nginx:alpine \
  baikal-private-ai-backend \
  baikal-private-ai-frontend \
  | gzip > "$EXPORT_DIR/baikal-images.tar.gz"

echo "  → $EXPORT_DIR/baikal-images.tar.gz"

# 4. 소스 복사
echo "[4/4] 설정 파일 복사..."
cp docker-compose.yml "$EXPORT_DIR/"
cp docker-compose.cpu.yml "$EXPORT_DIR/"
cp .env.example "$EXPORT_DIR/.env"
cp -r nginx "$EXPORT_DIR/"
cp -r scripts "$EXPORT_DIR/"

echo ""
echo "=========================================="
echo " 패키지 생성 완료!"
echo " 위치: $EXPORT_DIR/"
echo ""
echo " 폐쇄망으로 전송 후:"
echo "   cd offline-package"
echo "   bash scripts/import-images.sh"
echo "   bash scripts/import-models.sh"
echo "   docker-compose up -d"
echo "=========================================="
