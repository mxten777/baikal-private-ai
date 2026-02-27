# BAIKAL Private AI — 관리자 매뉴얼

> **문서 버전**: 1.0  
> **최종 수정일**: 2026-02-27  
> **대상 독자**: 시스템 관리자, IT 운영팀

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [시스템 요구사항](#2-시스템-요구사항)
3. [설치 및 배포](#3-설치-및-배포)
4. [환경 변수 설정](#4-환경-변수-설정)
5. [시스템 시작 및 종료](#5-시스템-시작-및-종료)
6. [초기 설정](#6-초기-설정)
7. [사용자 관리](#7-사용자-관리)
8. [문서 관리](#8-문서-관리)
9. [AI 모델 관리](#9-ai-모델-관리)
10. [시스템 모니터링](#10-시스템-모니터링)
11. [백업 및 복구](#11-백업-및-복구)
12. [폐쇄망 설치](#12-폐쇄망-설치)
13. [문제 해결 가이드](#13-문제-해결-가이드)
14. [보안 설정 가이드](#14-보안-설정-가이드)
15. [FAQ](#15-faq)

---

## 1. 시스템 개요

### 1.1 BAIKAL Private AI란?

BAIKAL Private AI는 **폐쇄망(에어갭) 환경**에서 운영 가능한 **문서 기반 AI 질의응답 플랫폼**입니다. 외부 클라우드 API에 의존하지 않고, 모든 AI 처리를 로컬 서버에서 수행합니다.

### 1.2 시스템 구성요소

| 구성요소 | 역할 | 포트 |
|----------|------|------|
| **Nginx** | 리버스 프록시, 정적 파일 서빙 | 80 |
| **Frontend** | React 웹 애플리케이션 | 3000 (내부) |
| **Backend** | FastAPI REST API 서버 | 8000 |
| **PostgreSQL** | 데이터베이스 + 벡터 검색(pgvector) | 5432 |
| **Ollama** | 로컬 LLM 및 임베딩 엔진 | 11434 |

### 1.3 시스템 구조도

```
사용자(브라우저)
     │
     ▼
┌──────────┐     ┌───────────┐     ┌─────────────┐
│  Nginx   │────▶│ Frontend  │     │ PostgreSQL  │
│  :80     │     │ React     │     │ + pgvector  │
│          │────▶│           │     │  :5432      │
└──────────┘     └───────────┘     └──────┬──────┘
     │                                     │
     │           ┌───────────┐             │
     └──────────▶│ Backend   │─────────────┘
                 │ FastAPI   │
                 │  :8000    │──────┐
                 └───────────┘      │
                                    ▼
                            ┌───────────┐
                            │  Ollama   │
                            │  :11434   │
                            │ qwen2.5   │
                            │ bge-m3    │
                            └───────────┘
```

### 1.4 데이터 흐름

1. 사용자가 문서를 업로드합니다
2. Backend가 텍스트를 추출하고 500자 단위로 청킹합니다
3. Ollama(bge-m3)가 각 청크를 1024차원 벡터로 임베딩합니다
4. 벡터가 PostgreSQL(pgvector)에 저장됩니다
5. 사용자가 질문하면, 질문도 벡터로 변환됩니다
6. 코사인 유사도로 관련 문서 청크 Top-5를 검색합니다
7. 검색된 컨텍스트 + 질문을 LLM(qwen2.5:7b)에 전달합니다
8. LLM이 한국어로 답변을 생성하여 실시간 스트리밍합니다

---

## 2. 시스템 요구사항

### 2.1 하드웨어 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| **CPU** | 4코어 | 8코어 이상 |
| **메모리** | 16GB | 32GB 이상 |
| **디스크** | 50GB SSD | 100GB SSD 이상 |
| **GPU** | 없어도 가능 (CPU 모드) | NVIDIA GPU 8GB+ VRAM |

### 2.2 소프트웨어 요구사항

**Docker 배포 시:**
| 소프트웨어 | 버전 |
|-----------|------|
| Docker | 20.10 이상 |
| Docker Compose | 2.0 이상 |

**로컬 개발 시:**
| 소프트웨어 | 버전 |
|-----------|------|
| Python | 3.11 이상 |
| Node.js | 18 이상 |
| PostgreSQL | 16 이상 |
| Ollama | 0.17 이상 |

### 2.3 네트워크 요구사항

- **인터넷 환경**: 초기 설치 시 Docker 이미지 및 AI 모델 다운로드 필요 (약 12GB)
- **폐쇄망 환경**: USB 또는 내부 네트워크를 통한 오프라인 이미지 전송 필요
- **내부 포트**: 80(웹), 5432(DB), 8000(API), 11434(Ollama) 사용

---

## 3. 설치 및 배포

### 3.1 Docker Compose 배포 (권장)

#### 단계 1: 저장소 클론

```bash
git clone https://github.com/mxten777/baikal-private-ai.git
cd baikal-private-ai
```

#### 단계 2: 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 반드시 다음 항목을 변경하세요:

```dotenv
# 반드시 변경해야 하는 항목
SECRET_KEY=여기에-랜덤-문자열-입력-최소-32자
DEFAULT_ADMIN_PASSWORD=강력한-비밀번호-입력
POSTGRES_PASSWORD=DB-비밀번호-입력
```

#### 단계 3: 시스템 시작

**GPU가 있는 서버:**
```bash
docker-compose up -d
```

**CPU만 사용하는 서버:**
```bash
docker-compose -f docker-compose.cpu.yml up -d
```

#### 단계 4: AI 모델 다운로드

```bash
# Ollama 컨테이너가 시작된 후 (약 30초 대기)
docker exec baikal-ollama ollama pull qwen2.5:7b
docker exec baikal-ollama ollama pull bge-m3
```

> **참고**: qwen2.5:7b는 약 4.7GB, bge-m3는 약 1.2GB입니다. 다운로드에 네트워크 환경에 따라 수분~수십분이 소요됩니다.

#### 단계 5: 접속 확인

브라우저에서 `http://서버IP` 접속 → 로그인 화면이 표시되면 설치 성공입니다.

### 3.2 Windows 로컬 설치

```powershell
# 환경변수 설정
$env:PATH += ";C:\Program Files\PostgreSQL\16\bin;$env:LOCALAPPDATA\Programs\Ollama"

# DB 준비 (최초 1회)
psql -U postgres -c "CREATE DATABASE baikal_ai;"
psql -U postgres -c "CREATE USER baikal WITH PASSWORD 'baikal_secret_2024';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE baikal_ai TO baikal;"
psql -U postgres -d baikal_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Ollama 모델 다운로드
ollama pull qwen2.5:7b
ollama pull bge-m3

# 백엔드 실행
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드 실행 (새 터미널)
cd frontend
npm install
npm start
```

### 3.3 자동 설정 스크립트

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

---

## 4. 환경 변수 설정

### 4.1 전체 환경 변수 목록

`.env` 파일에 설정하는 모든 환경 변수입니다.

| 변수명 | 기본값 | 설명 | 변경 필요 |
|--------|--------|------|-----------|
| `POSTGRES_USER` | baikal | DB 사용자명 | 선택 |
| `POSTGRES_PASSWORD` | baikal_secret_2024 | DB 비밀번호 | **필수** |
| `POSTGRES_DB` | baikal_ai | DB 이름 | 선택 |
| `DATABASE_URL` | (자동 구성) | DB 접속 주소 | 선택 |
| `SECRET_KEY` | (기본값) | JWT 서명 키 | **필수** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | 액세스 토큰 만료(분) | 선택 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | 리프레시 토큰 만료(일) | 선택 |
| `OLLAMA_BASE_URL` | http://ollama:11434 | Ollama 서버 주소 | 환경별 |
| `LLM_MODEL` | qwen2.5:7b | LLM 모델명 | 선택 |
| `EMBEDDING_MODEL` | bge-m3 | 임베딩 모델명 | 선택 |
| `DEFAULT_ADMIN_USERNAME` | admin | 초기 관리자 ID | 선택 |
| `DEFAULT_ADMIN_PASSWORD` | admin1234 | 초기 관리자 비밀번호 | **필수** |
| `UPLOAD_DIR` | /app/uploads | 업로드 파일 저장 경로 | 선택 |
| `MAX_UPLOAD_SIZE_MB` | 100 | 최대 업로드 크기(MB) | 선택 |
| `CHUNK_SIZE` | 500 | 텍스트 청킹 크기(자) | 선택 |
| `CHUNK_OVERLAP` | 50 | 청크 간 오버랩(자) | 선택 |
| `TOP_K` | 5 | 벡터 검색 결과 수 | 선택 |

### 4.2 보안 관련 필수 변경 사항

**프로덕션 배포 시 반드시 변경해야 합니다:**

```dotenv
# 1. JWT 비밀키 - 최소 32자 랜덤 문자열
SECRET_KEY=Xk9m2PqR7wLz4vNc8jT1aB5dG0hY6eKfW3iU0rS9bN2mQ4p

# 2. 관리자 비밀번호 - 강력한 비밀번호
DEFAULT_ADMIN_PASSWORD=MyStr0ng!P@ssw0rd

# 3. DB 비밀번호
POSTGRES_PASSWORD=Db$ecure_P@ss_2024
```

### 4.3 LLM 모델 변경

사용 가능한 모델을 변경하려면:

```dotenv
# 한국어 성능이 좋은 모델들
LLM_MODEL=qwen2.5:7b          # 권장 (한국어 우수, 4.7GB)
LLM_MODEL=qwen2.5:14b         # 더 높은 품질 (GPU 권장)
LLM_MODEL=llama3               # 영어 중심 (한국어 제한적)
LLM_MODEL=mistral              # 범용 (한국어 보통)
```

모델 변경 후 반드시 해당 모델을 다운로드해야 합니다:
```bash
docker exec baikal-ollama ollama pull <모델명>
```

---

## 5. 시스템 시작 및 종료

### 5.1 시스템 시작

```bash
# 전체 시스템 시작
docker-compose up -d

# 개별 서비스 시작
docker-compose up -d postgres
docker-compose up -d ollama
docker-compose up -d backend
docker-compose up -d frontend
docker-compose up -d nginx
```

### 5.2 시스템 종료

```bash
# 전체 시스템 종료 (데이터 보존)
docker-compose down

# 전체 시스템 종료 + 볼륨 삭제 (주의: 모든 데이터 삭제!)
docker-compose down -v
```

### 5.3 시스템 재시작

```bash
# 전체 재시작
docker-compose restart

# 특정 서비스 재시작
docker-compose restart backend
docker-compose restart ollama
```

### 5.4 컨테이너 상태 확인

```bash
docker-compose ps
```

정상 상태 예시:
```
NAME               STATUS         PORTS
baikal-postgres    Up (healthy)   5432:5432
baikal-ollama      Up             11434:11434
baikal-backend     Up             8000:8000
baikal-frontend    Up             3000:80
baikal-nginx       Up             80:80
```

---

## 6. 초기 설정

### 6.1 최초 로그인

1. 브라우저에서 `http://서버IP` (또는 `http://localhost`) 접속
2. 기본 관리자 계정으로 로그인:
   - **ID**: `admin`
   - **비밀번호**: `admin1234` (또는 `.env`에 설정한 값)

### 6.2 관리자 비밀번호 변경 (필수!)

1. 로그인 후 좌측 사이드바 하단의 사용자 프로필 영역에 마우스를 올립니다
2. **열쇠 아이콘(🔑)** 을 클릭합니다
3. 비밀번호 변경 모달에서:
   - 현재 비밀번호: `admin1234`
   - 새 비밀번호: 4자 이상의 안전한 비밀번호 입력
   - 비밀번호 확인: 새 비밀번호 재입력
4. **"비밀번호 변경"** 버튼 클릭
5. "비밀번호가 변경되었습니다" 확인 메시지 표시

### 6.3 추가 관리자 계정 생성

단일 관리자 계정에 의존하지 않도록 백업 관리자를 생성하는 것을 권장합니다.

1. 좌측 메뉴 → **관리자** 섹션 → **"사용자 관리"** 클릭
2. 우측 상단 **"새 사용자"** 클릭
3. 사용자 정보 입력:
   - 사용자명: 고유한 ID (예: `admin2`)
   - 비밀번호: 안전한 비밀번호
   - 역할: **관리자** 선택
4. **"생성"** 버튼 클릭

---

## 7. 사용자 관리

### 7.1 사용자 관리 페이지 접근

- 좌측 메뉴 → **관리자** → **"사용자 관리"**
- 관리자 권한(role: admin)이 있는 계정만 접근 가능합니다

### 7.2 사용자 생성

1. **"새 사용자"** 버튼 클릭
2. 필수 정보 입력:
   - **사용자명**: 영문/숫자 조합 (중복 불가)
   - **비밀번호**: 4자 이상
   - **역할**: `사용자` 또는 `관리자`
3. **"생성"** 클릭 → 즉시 활성화

### 7.3 사용자 수정

사용자 테이블에서 해당 사용자의 행에 있는 수정 옵션을 사용합니다:

- **역할 변경**: `사용자` ↔ `관리자` 전환 가능
- **비밀번호 초기화**: 새 비밀번호 설정 가능
- **계정 비활성화**: 비활성화 시 로그인 불가 (데이터는 보존)

### 7.4 사용자 삭제

- 사용자 행의 **삭제** 버튼 클릭
- 자기 자신의 계정은 삭제할 수 없습니다 (안전 장치)
- **주의**: 삭제 시 해당 사용자의 채팅 기록도 삭제됩니다

### 7.5 역할 권한 비교

| 기능 | 일반 사용자 | 관리자 |
|------|:-----------:|:------:|
| AI 질문응답 | ✅ | ✅ |
| 문서 업로드 | ✅ | ✅ |
| 본인 문서 조회 | ✅ | ✅ |
| 전체 문서 조회 | ❌ | ✅ |
| 문서 삭제 | ❌ | ✅ |
| 문서 검색 | ✅ | ✅ |
| 채팅 세션 관리 | ✅ (본인) | ✅ (본인) |
| 사용자 관리 | ❌ | ✅ |
| 비밀번호 변경 | ✅ (본인) | ✅ (본인) |

---

## 8. 문서 관리

### 8.1 문서 관리 페이지 접근

- **관리자용**: 좌측 메뉴 → **관리자** → **"문서 관리"** (전체 문서 열람 및 삭제)
- **일반 사용자용**: 좌측 메뉴 → **"문서 관리"** (본인 문서만 열람)

### 8.2 지원 파일 형식

| 형식 | 확장자 | 텍스트 추출 방법 |
|------|--------|-----------------|
| PDF | .pdf | PyPDF2 라이브러리 |
| Word | .docx | python-docx 라이브러리 |
| Excel | .xlsx | openpyxl 라이브러리 |

- **최대 파일 크기**: 100MB (.env의 `MAX_UPLOAD_SIZE_MB`로 조정 가능)
- **이미지 전용 PDF**: 텍스트 추출이 제한적입니다 (OCR 미지원)

### 8.3 문서 처리 상태

| 상태 | 설명 | 색상 |
|------|------|------|
| **uploading** | 업로드 중 | 파랑 |
| **processing** | 텍스트 추출 + 임베딩 생성 중 | 노랑/주황 |
| **completed** | 처리 완료, AI 질의응답 가능 | 초록 |
| **failed** | 처리 실패 (에러 메시지 확인) | 빨강 |

### 8.4 문서 처리 과정

업로드된 문서는 백그라운드에서 자동으로 처리됩니다:

```
1. 파일 저장 → 서버 uploads/ 디렉토리
2. 텍스트 추출 → PDF/DOCX/XLSX 파서
3. 텍스트 청킹 → 500자 단위, 50자 오버랩
4. 벡터 임베딩 → bge-m3 모델 (1024차원)
5. DB 저장 → document_chunks 테이블
6. 상태 업데이트 → completed
```

> **처리 시간**: 파일 크기와 서버 성능에 따라 다릅니다. 일반적으로 10페이지 PDF 기준 30초~2분 소요됩니다.

### 8.5 문서 삭제 (관리자)

1. 관리자 → 문서 관리 페이지 접근
2. 삭제할 문서의 **삭제 버튼** 클릭
3. 삭제 시 해당 문서의 파일, 텍스트 청크, 벡터 임베딩이 모두 제거됩니다

### 8.6 문서 다운로드

- 문서 목록에서 해당 문서의 **다운로드** 버튼 클릭
- 원본 파일이 그대로 다운로드됩니다

---

## 9. AI 모델 관리

### 9.1 설치된 모델 확인

```bash
# Docker 환경
docker exec baikal-ollama ollama list

# 로컬 환경
ollama list
```

### 9.2 모델 다운로드

```bash
# Docker 환경
docker exec baikal-ollama ollama pull <모델명>

# 로컬 환경
ollama pull <모델명>
```

### 9.3 권장 모델 구성

| 용도 | 모델명 | 크기 | 설명 |
|------|--------|------|------|
| **LLM (답변 생성)** | qwen2.5:7b | 4.7GB | 한국어 성능 우수, CPU/GPU 호환 |
| **임베딩** | bge-m3 | 1.2GB | 다국어 임베딩, 1024차원 |

### 9.4 모델 교체

1. 새 모델 다운로드:
   ```bash
   docker exec baikal-ollama ollama pull qwen2.5:14b
   ```

2. `.env` 파일에서 모델명 변경:
   ```dotenv
   LLM_MODEL=qwen2.5:14b
   ```

3. 백엔드 재시작:
   ```bash
   docker-compose restart backend
   ```

> **주의**: 임베딩 모델(`EMBEDDING_MODEL`)을 변경하면 기존 문서의 벡터와 호환되지 않으므로, 모든 문서를 재업로드/재처리해야 합니다.

### 9.5 불필요한 모델 삭제

```bash
docker exec baikal-ollama ollama rm <모델명>
```

---

## 10. 시스템 모니터링

### 10.1 헬스체크 API

```bash
curl http://localhost/api/health
```

정상 응답 예시:
```json
{
  "status": "ok",
  "service": "BAIKAL Private AI",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "ollama": "connected"
  }
}
```

상태 값:
| status | 의미 |
|--------|------|
| `ok` | 모든 구성요소 정상 |
| `degraded` | Ollama 연결 실패 (DB는 정상) |
| `error` | DB 연결 실패 |

### 10.2 로그 확인

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs ollama
docker-compose logs postgres

# 실시간 로그 추적
docker-compose logs -f backend
```

### 10.3 리소스 사용량 확인

```bash
# 컨테이너별 CPU/메모리 사용량
docker stats
```

### 10.4 DB 상태 확인

```bash
# DB 접속
docker exec -it baikal-postgres psql -U baikal -d baikal_ai

# 테이블별 레코드 수 확인
SELECT 'users' as tbl, count(*) FROM users
UNION ALL SELECT 'documents', count(*) FROM documents
UNION ALL SELECT 'document_chunks', count(*) FROM document_chunks
UNION ALL SELECT 'chat_sessions', count(*) FROM chat_sessions
UNION ALL SELECT 'chat_messages', count(*) FROM chat_messages;

# 벡터 인덱스 크기 확인
SELECT pg_size_pretty(pg_total_relation_size('document_chunks'));
```

---

## 11. 백업 및 복구

### 11.1 데이터베이스 백업

```bash
# 전체 DB 백업
docker exec baikal-postgres pg_dump -U baikal baikal_ai > backup_$(date +%Y%m%d).sql

# 압축 백업
docker exec baikal-postgres pg_dump -U baikal -Fc baikal_ai > backup_$(date +%Y%m%d).dump
```

### 11.2 데이터베이스 복구

```bash
# SQL 파일에서 복구
docker exec -i baikal-postgres psql -U baikal baikal_ai < backup_20260227.sql

# 압축 백업에서 복구
docker exec -i baikal-postgres pg_restore -U baikal -d baikal_ai < backup_20260227.dump
```

### 11.3 업로드 파일 백업

```bash
# 업로드 파일 볼륨 백업
docker cp baikal-backend:/app/uploads ./uploads_backup

# 복구
docker cp ./uploads_backup/. baikal-backend:/app/uploads/
```

### 11.4 전체 백업 스크립트 (예시)

```bash
#!/bin/bash
BACKUP_DIR="/backup/baikal/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# DB 백업
docker exec baikal-postgres pg_dump -U baikal -Fc baikal_ai > $BACKUP_DIR/db.dump

# 업로드 파일 백업
docker cp baikal-backend:/app/uploads $BACKUP_DIR/uploads

# 환경 설정 백업
cp .env $BACKUP_DIR/env_backup

echo "백업 완료: $BACKUP_DIR"
```

### 11.5 Ollama 모델 백업

```bash
# 모델 데이터 볼륨 백업
docker run --rm -v baikal-private-ai_ollama_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama_models.tar.gz -C /data .
```

---

## 12. 폐쇄망 설치

### 12.1 인터넷 환경에서 사전 준비

#### 단계 1: Docker 이미지 저장

```bash
# 이미지 빌드
docker-compose build

# 이미지 저장 (tar 파일)
./scripts/export-images.sh
```

`export-images.sh`는 다음 이미지를 저장합니다:
- `pgvector/pgvector:pg16`
- `ollama/ollama:latest`
- `nginx:alpine`
- `baikal-backend` (빌드된 이미지)
- `baikal-frontend` (빌드된 이미지)

#### 단계 2: Ollama 모델 저장

```bash
./scripts/export-models.sh
```

이 스크립트는 `.ollama` 디렉토리의 모델 파일을 tar로 패키징합니다.

#### 단계 3: 미디어로 전송

모든 파일을 USB 또는 내부 네트워크로 폐쇄망 서버에 전송합니다:
- Docker 이미지 tar 파일들
- Ollama 모델 tar 파일
- 프로젝트 소스 코드 (docker-compose.yml, .env 포함)

### 12.2 폐쇄망 서버에서 설치

```bash
# 1. Docker 이미지 로드
./scripts/import-images.sh

# 2. Ollama 모델 로드
./scripts/import-models.sh

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 4. 시스템 시작
docker-compose up -d
```

### 12.3 폐쇄망 설치 시 주의사항

- Docker 이미지 파일 총 크기: 약 8~10GB
- Ollama 모델 파일 크기: 약 6GB (qwen2.5:7b + bge-m3)
- USB 최소 16GB 이상 권장
- 대용량 파일 전송 시 파일 무결성 검증(SHA256) 권장

---

## 13. 문제 해결 가이드

### 13.1 서비스 시작 실패

**증상**: `docker-compose up -d` 후 컨테이너가 종료됨

```bash
# 로그 확인
docker-compose logs backend
```

| 에러 메시지 | 원인 | 해결 방법 |
|-------------|------|----------|
| `DB 연결 실패` | PostgreSQL 미시작 | `docker-compose restart postgres` 후 재시도 |
| `Connection refused :5432` | DB 포트 충돌 | 호스트의 5432 포트 사용 여부 확인 |
| `Secret key too short` | SECRET_KEY 미설정 | `.env`에 SECRET_KEY 설정 |

### 13.2 AI 응답 오류

**증상**: "AI 서비스가 사용할 수 없습니다" 또는 "Ollama 서버에 연결할 수 없습니다"

```bash
# Ollama 상태 확인
docker exec baikal-ollama ollama list

# Ollama 서버 확인
curl http://localhost:11434/api/tags
```

| 원인 | 해결 방법 |
|------|----------|
| Ollama 컨테이너 미시작 | `docker-compose restart ollama` |
| 모델 미다운로드 | `docker exec baikal-ollama ollama pull qwen2.5:7b` |
| 메모리 부족 | 시스템 메모리 확인, 더 작은 모델 사용 |
| GPU 드라이버 오류 | CPU 모드(`docker-compose.cpu.yml`) 사용 |

### 13.3 문서 업로드 실패

| 증상 | 원인 | 해결 방법 |
|------|------|----------|
| "지원하지 않는 파일 형식" | pdf/docx/xlsx 외 파일 | 지원 형식으로 변환 후 재업로드 |
| 파일 크기 초과 | 100MB 초과 | `.env`의 `MAX_UPLOAD_SIZE_MB` 조정 |
| 처리 상태 "failed" | 텍스트 추출 실패 | 파일 손상 확인, 다른 뷰어로 열리는지 확인 |
| 임베딩 생성 실패 | Ollama 연결 문제 | Ollama 상태 확인 (13.2 참조) |

### 13.4 로그인 불가

| 원인 | 해결 방법 |
|------|----------|
| 비밀번호 분실 | DB에서 직접 초기화 (아래 참조) |
| 계정 비활성화 | 다른 관리자가 활성화 또는 DB 직접 수정 |
| 토큰 만료 | 브라우저 캐시/쿠키 삭제 후 재로그인 |

**관리자 비밀번호 초기화 (DB 직접):**
```bash
docker exec -it baikal-postgres psql -U baikal -d baikal_ai
```
```sql
-- 비밀번호를 'admin1234'로 초기화 (bcrypt 해시)
UPDATE users SET password_hash = '$2b$12$LJ3m4ys7Ot0IhVHoOVJQr.Bn7XCq3fCJj6OUoGFpM5N2JwPVPqFsK'
WHERE username = 'admin';
```
> **참고**: 위 해시는 예시입니다. 실제로는 Python에서 `from passlib.context import CryptContext; CryptContext(schemes=["bcrypt"]).hash("admin1234")` 로 생성한 해시를 사용하세요.

### 13.5 성능 저하

| 증상 | 원인 | 해결 방법 |
|------|------|----------|
| AI 응답 느림 | CPU 모드에서 대형 모델 | 더 작은 모델 또는 GPU 사용 |
| 검색 느림 | 벡터 인덱스 과다 | document_chunks 수 확인, 불필요 문서 삭제 |
| 전반적 느림 | 메모리 부족 | 서버 메모리 확인 (docker stats) |

---

## 14. 보안 설정 가이드

### 14.1 필수 보안 조치

1. **기본 비밀번호 변경**: admin 계정 비밀번호 즉시 변경
2. **SECRET_KEY 설정**: `.env`에 32자 이상 랜덤 문자열 설정
3. **DB 비밀번호 변경**: 기본 `baikal_secret_2024` 변경

### 14.2 JWT 토큰 정책

| 설정 | 기본값 | 설명 |
|------|--------|------|
| 액세스 토큰 만료 | 60분 | 짧을수록 안전 (15~60분 권장) |
| 리프레시 토큰 만료 | 7일 | 장기 세션 유지 (1~30일) |
| 알고리즘 | HS256 | 변경 불필요 |

### 14.3 네트워크 보안

- 외부에서 DB 포트(5432), Ollama 포트(11434) 직접 접근 차단 권장
- 방화벽에서 80(HTTP) 포트만 허용
- HTTPS가 필요한 경우 Nginx에 SSL 인증서 설정

### 14.4 데이터 보안

- 모든 비밀번호는 **bcrypt**로 해싱되어 저장됩니다
- JWT 토큰은 서버 서명으로 위변조가 불가능합니다
- 업로드 파일은 서버 로컬(또는 Docker 볼륨)에 저장됩니다
- 외부 API 호출이 전혀 없으므로 데이터 유출 위험이 없습니다

---

## 15. FAQ

### Q1. GPU 없이도 사용할 수 있나요?
**A:** 네, CPU만으로 운영이 가능합니다. `docker-compose.cpu.yml`을 사용하세요. 다만 AI 응답 생성 속도가 GPU 대비 느릴 수 있습니다 (7B 모델 기준 CPU: 10~30초, GPU: 1~5초).

### Q2. 동시 사용자는 몇 명까지 지원하나요?
**A:** 하드웨어 사양에 따라 다릅니다. 일반적으로 CPU 서버(8코어, 32GB)에서 5~10명, GPU 서버에서 20~50명 수준의 동시 질의를 처리할 수 있습니다. AI 답변 생성은 순차 처리되므로, 동시 질문이 많으면 대기 시간이 발생합니다.

### Q3. 기존 데이터를 유지하면서 업데이트하려면?
**A:** Docker 볼륨에 데이터가 저장되므로 `docker-compose down` → 새 코드 pull → `docker-compose up -d --build`로 업데이트하면 데이터가 보존됩니다.

### Q4. 사용자가 직접 비밀번호를 변경할 수 있나요?
**A:** 네, 사이드바 하단의 사용자 영역에서 열쇠 아이콘을 클릭하면 비밀번호 변경 모달이 열립니다. 현재 비밀번호 인증 후 변경할 수 있습니다.

### Q5. HWP(한글) 파일은 지원하나요?
**A:** 현재 버전에서는 지원하지 않습니다. PDF로 변환 후 업로드해 주세요. HWP 지원은 향후 업데이트 예정입니다.

### Q6. 어떤 LLM 모델을 사용하는 것이 좋나요?
**A:** 한국어 문서가 주를 이루는 환경에서는 `qwen2.5:7b`를 권장합니다. GPU(8GB+ VRAM)가 있다면 `qwen2.5:14b`로 더 높은 품질을 얻을 수 있습니다.

---

> **문서 끝** | BAIKAL Private AI 관리자 매뉴얼 v1.0
