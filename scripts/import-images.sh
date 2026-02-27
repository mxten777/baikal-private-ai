#!/bin/bash
# ===========================================
# BAIKAL Private AI - Docker 이미지 가져오기
# 폐쇄망에서 실행
# ===========================================

set -e

echo "=========================================="
echo " BAIKAL Private AI - Docker 이미지 로드"
echo "=========================================="

if [ ! -f "baikal-images.tar.gz" ]; then
  echo "ERROR: baikal-images.tar.gz 파일을 찾을 수 없습니다."
  echo "export-images.sh 로 생성된 패키지를 이 디렉토리에 복사하세요."
  exit 1
fi

echo "Docker 이미지 로드 중... (수 분 소요될 수 있습니다)"
gunzip -c baikal-images.tar.gz | docker load

echo ""
echo "이미지 로드 완료!"
docker images | grep -E "pgvector|ollama|nginx|baikal"
