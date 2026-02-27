#!/bin/bash
# ===========================================
# BAIKAL Private AI - Ollama 모델 내보내기
# 인터넷이 되는 환경에서 실행
# ===========================================

set -e

EXPORT_DIR="./offline-package"
mkdir -p "$EXPORT_DIR"

echo "=========================================="
echo " Ollama 모델 다운로드 및 내보내기"
echo "=========================================="

# Ollama 실행 확인
if ! command -v ollama &> /dev/null; then
  echo "Ollama가 설치되어 있지 않습니다."
  echo "https://ollama.com 에서 설치 후 다시 실행하세요."
  exit 1
fi

# 모델 다운로드
echo "[1/3] LLM 모델 다운로드..."
ollama pull llama3

echo "[2/3] Embedding 모델 다운로드..."
ollama pull bge-m3

# 모델 파일 복사
echo "[3/3] 모델 파일 패키징..."
OLLAMA_DIR="$HOME/.ollama"

if [ -d "$OLLAMA_DIR" ]; then
  tar -czf "$EXPORT_DIR/ollama-models.tar.gz" -C "$OLLAMA_DIR" .
  echo "  → $EXPORT_DIR/ollama-models.tar.gz"
else
  echo "WARNING: Ollama 데이터 디렉토리를 찾을 수 없습니다: $OLLAMA_DIR"
  echo "수동으로 Ollama 모델 디렉토리를 패키징하세요."
fi

echo ""
echo "모델 내보내기 완료!"
