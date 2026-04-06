FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cross-encoder 모델 사전 다운로드 (폐쇄망 환경 대비 이미지에 포함)
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# 앱 복사
COPY . .

# 업로드 디렉토리
RUN mkdir -p /app/uploads

EXPOSE 8000

# --workers 4: 동시 요청 처리 (LLM 요청이 다른 API를 블로킹하지 않도록)
# Python 3.11+ 에서 uvicorn --workers 네이티브 지원
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
