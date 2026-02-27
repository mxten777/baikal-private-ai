#!/bin/bash
# ===========================================
# BAIKAL Private AI - Ollama 모델 가져오기
# 폐쇄망에서 실행
# ===========================================

set -e

echo "=========================================="
echo " BAIKAL Private AI - Ollama 모델 로드"
echo "=========================================="

if [ ! -f "ollama-models.tar.gz" ]; then
  echo "ERROR: ollama-models.tar.gz 파일을 찾을 수 없습니다."
  exit 1
fi

# Docker volume에 모델 복사
echo "Ollama 모델 복사 중..."

# Ollama 컨테이너의 볼륨 디렉토리 확인
VOLUME_PATH=$(docker volume inspect baikal-private-ai_ollama_data -f '{{.Mountpoint}}' 2>/dev/null || echo "")

if [ -z "$VOLUME_PATH" ]; then
  echo "볼륨이 없습니다. docker-compose up -d ollama 로 먼저 Ollama를 시작하세요."
  echo "시작 후 이 스크립트를 다시 실행하세요."
  
  echo ""
  echo "대안: 수동 복사"
  echo "  docker-compose up -d ollama"
  echo "  docker cp ollama-models.tar.gz baikal-ollama:/tmp/"
  echo "  docker exec baikal-ollama sh -c 'cd /root/.ollama && tar -xzf /tmp/ollama-models.tar.gz'"
  exit 1
fi

# 볼륨에 직접 압축 해제
tar -xzf ollama-models.tar.gz -C "$VOLUME_PATH"

echo ""
echo "모델 로드 완료!"
echo "Ollama를 재시작하세요: docker-compose restart ollama"
