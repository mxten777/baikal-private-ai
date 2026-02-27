# BAIKAL Private AI

폐쇄망 설치형 문서검색·답변 AI 플랫폼

> **Last Updated**: 2026-02-27  
> **Version**: 1.0.0-beta  
> **Status**: MVP 완료 + 프리미엄 UI + 모바일 반응형

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 구조도](#시스템-구조도)
3. [기술 스택](#기술-스택)
4. [개발 진행 현황](#개발-진행-현황)
5. [UI/UX 구현 상세](#uiux-구현-상세)
6. [빠른 시작](#빠른-시작)
7. [폴더 구조](#폴더-구조)
8. [DB 테이블 설계](#db-테이블-설계)
9. [API 목록](#api-목록)
10. [RAG 파이프라인](#rag-파이프라인)
11. [폐쇄망 설치 방법](#폐쇄망-설치-방법)
12. [향후 보완 과제](#향후-보완-과제)

---

## 프로젝트 개요

**BAIKAL Private AI**는 폐쇄망(에어갭) 환경에서 운영 가능한 문서 기반 AI 질의응답 플랫폼입니다.

- **외부 API 의존 제로**: Ollama 기반 로컬 LLM + 임베딩
- **RAG 파이프라인**: 문서 업로드 → 청킹 → 벡터화 → 유사도 검색 → LLM 답변
- **실시간 스트리밍**: SSE 기반 토큰 단위 실시간 AI 답변
- **다중 사용자**: JWT 인증, 관리자/일반 사용자 역할 분리
- **프리미엄 UI**: 글래스모피즘, 그래디언트, 마이크로 애니메이션 적용
- **모바일 반응형**: 햄버거 메뉴, 슬라이드 사이드바, 적응형 테이블

---

## 시스템 구조도

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                           │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │  Nginx   │───▶│   Frontend   │    │     PostgreSQL       │   │
│  │  :80     │    │   React 18   │    │     + pgvector       │   │
│  │          │───▶│   :3000      │    │     :5432            │   │
│  └──────────┘    └──────────────┘    └─────────────────────┘   │
│       │                                        ▲               │
│       │          ┌──────────────┐               │               │
│       └─────────▶│   Backend    │───────────────┘               │
│                  │   FastAPI    │                               │
│                  │   :8000      │──────┐                       │
│                  └──────────────┘      │                       │
│                                        ▼                       │
│                               ┌──────────────┐                │
│                               │    Ollama     │                │
│                               │    :11434     │                │
│                               │  - llama3     │                │
│                               │  - bge-m3     │                │
│                               └──────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| **Frontend** | React + Tailwind CSS | 18.3.1 / 3.4.13 |
| **UI 라이브러리** | react-icons (Heroicons v2), react-hot-toast, react-dropzone, react-markdown | - |
| **Backend** | FastAPI (Python) | 0.115.0 |
| **DB** | PostgreSQL + pgvector | 16.x / 0.3.5 |
| **AI/LLM** | Ollama – llama3 | 0.17.0 |
| **Embedding** | Ollama – bge-m3 (1024차원) | - |
| **인증** | JWT (python-jose + bcrypt) | - |
| **배포** | Docker Compose | - |

---

## 개발 진행 현황

### Phase 1: 인프라 및 기반 구축 ✅

| 항목 | 상태 | 설명 |
|------|------|------|
| PostgreSQL + pgvector | ✅ 완료 | 16.x 로컬 설치, pgvector 0.8.2 확장 |
| Ollama 설치 | ✅ 완료 | llama3 (4.7GB) + bge-m3 (1.2GB) 모델 |
| FastAPI 백엔드 | ✅ 완료 | 비동기 SQLAlchemy, 자동 테이블 생성 |
| React 프론트엔드 | ✅ 완료 | CRA + Tailwind CSS + Router v6 |
| Docker Compose | ✅ 완료 | CPU/GPU 분리 설정 |
| .env 환경변수 관리 | ✅ 완료 | DATABASE_URL, OLLAMA_BASE_URL, SECRET_KEY |

### Phase 2: 핵심 기능 ✅

| 항목 | 상태 | 설명 |
|------|------|------|
| JWT 인증 (로그인/로그아웃) | ✅ 완료 | 액세스 토큰 + 리프레시 토큰 |
| 사용자 관리 (CRUD) | ✅ 완료 | admin/user 역할, 활성/비활성 토글 |
| 문서 업로드 | ✅ 완료 | PDF, DOCX, XLSX (최대 100MB) |
| 문서 텍스트 추출 | ✅ 완료 | PyPDF2, python-docx, openpyxl |
| 텍스트 청킹 | ✅ 완료 | 500자 단위, 50자 오버랩 |
| 벡터 임베딩 | ✅ 완료 | bge-m3 모델 (1024차원) |
| pgvector 저장/검색 | ✅ 완료 | 코사인 유사도 Top-5 검색 |
| AI 질의응답 (RAG) | ✅ 완료 | 컨텍스트 주입 + llama3 응답 |
| SSE 스트리밍 | ✅ 완료 | 실시간 토큰 단위 응답 |
| 채팅 세션 관리 | ✅ 완료 | 세션별 대화 기록 저장 |
| 문서 검색 | ✅ 완료 | 벡터 기반 의미 검색 |

### Phase 3: 프리미엄 UI/UX ✅

| 항목 | 상태 | 설명 |
|------|------|------|
| 디자인 시스템 | ✅ 완료 | baikal 컬러 팔레트 (50~950), surface 컬러, accent 컬러 |
| 커스텀 CSS | ✅ 완료 | 380행 index.css – 글래스모피즘, 그래디언트, shimmer |
| 애니메이션 | ✅ 완료 | 14개 커스텀 애니메이션 (fade-in, slide-up, glow 등) |
| 로그인 페이지 | ✅ 완료 | 좌측 브랜딩 + 우측 폼, 글래스 효과 |
| 채팅 페이지 | ✅ 완료 | 세션 사이드바, AI/사용자 아바타, 실시간 타이핑 인디케이터 |
| 문서 관리 | ✅ 완료 | 통계 카드, 상태 뱃지, 드래그 앤 드롭 업로드 |
| 검색 페이지 | ✅ 완료 | 유사도 점수 표시, 카드형 결과 |
| 사이드바 내비게이션 | ✅ 완료 | 그래디언트 아이콘 박스, 액티브 액센트 바 |
| 관리자 페이지 | ✅ 완료 | 사용자/문서 관리, 통계 대시보드 |

### Phase 4: 모바일 반응형 ✅

| 항목 | 상태 | 적용 브레이크포인트 |
|------|------|------|
| Layout – 햄버거 메뉴 + 슬라이드 사이드바 | ✅ 완료 | `lg` (1024px) |
| Sidebar – onClose + 닫기 버튼 | ✅ 완료 | `lg` (1024px) |
| ChatPage – 세션 토글 오버레이 | ✅ 완료 | `md` (768px) |
| ChatMessage – 반응형 패딩 + 코드 스크롤 | ✅ 완료 | `sm` (640px) |
| DocumentsPage – 그리드/테이블 적응형 | ✅ 완료 | `sm` / `md` |
| DocumentUpload – 반응형 패딩 | ✅ 완료 | `sm` (640px) |
| SearchPage – 폼 스택 + 버튼 풀 너비 | ✅ 완료 | `sm` (640px) |
| UsersPage – 그리드/폼/테이블 적응형 | ✅ 완료 | `sm` (640px) |
| AdminDocumentsPage – 4열→2열 그리드 | ✅ 완료 | `sm` (640px) |
| LoginPage – 분할 레이아웃 | ✅ 완료 | `lg` (1024px) |

---

## UI/UX 구현 상세

### 디자인 시스템

```
컬러 팔레트:
  Primary :  baikal-600 (#4f46e5, Indigo 계열)
  Surface :  #fafbfc → #f4f6f8
  Accent  :  purple-600, fuchsia-500

타이포그래피:
  Font    :  Inter (Google Fonts)
  Title   :  font-extrabold, tracking-tight
  Label   :  text-[10px] uppercase tracking-[0.1em]

컴포넌트:
  Card    :  rounded-2xl, border-gray-100, hover:shadow-soft
  Button  :  rounded-xl~2xl, gradient, shadow-sm→md transition
  Input   :  rounded-xl, bg-gray-50 → focus:bg-white + ring
  Badge   :  rounded-lg, 상태별 색상 코딩 (emerald/amber/red/blue)
  Avatar  :  rounded-xl, gradient 배경, 이니셜 표시
```

### 반응형 전략

```
브레이크포인트:
  sm (640px)  : 단일 → 다단 그리드 전환, 폼 레이아웃 변경
  md (768px)  : 채팅 세션 사이드바 전환
  lg (1024px) : 메인 사이드바 전환 (고정 ↔ 슬라이드)

패턴:
  패딩      : p-4 sm:p-6 lg:p-8
  제목      : text-xl sm:text-[28px]
  그리드    : grid-cols-1 sm:grid-cols-2~3 lg:grid-cols-4
  테이블    : overflow-x-auto + hidden sm:table-cell
  폼       : flex-col sm:flex-row
  버튼      : w-full sm:w-auto
  사이드바   : fixed + translate-x + overlay (모바일)
              relative + 항상 표시 (데스크탑)
```

---

## 빠른 시작

### 로컬 개발 (Windows)

```powershell
# 사전 요구사항: PostgreSQL 16, Ollama, Node.js, Python 3.11+

# 1. 환경변수
$env:PATH += ";C:\Program Files\PostgreSQL\16\bin;$env:LOCALAPPDATA\Programs\Ollama"

# 2. Ollama 모델 준비
ollama pull llama3
ollama pull bge-m3

# 3. DB 준비 (최초 1회)
psql -U postgres -c "CREATE DATABASE baikal_ai;"
psql -U postgres -c "CREATE USER baikal WITH PASSWORD 'baikal_secret_2024';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE baikal_ai TO baikal;"
psql -U postgres -d baikal_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 4. 백엔드 실행
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. 프론트엔드 실행 (새 터미널)
cd frontend
npm install
npm start
# → http://localhost:3000 (기본 관리자: admin / admin1234)
```

### Docker 배포

```bash
# 1. 클론
git clone <repo-url> && cd baikal-private-ai

# 2. 환경변수 설정
cp .env.example .env

# 3. 실행 (GPU가 있으면 docker-compose.yml, 없으면 cpu 버전)
docker-compose up -d

# 4. 접속 → http://localhost (기본 관리자: admin / admin1234)
```

---

## 폴더 구조

```
baikal-private-ai/
├── docker-compose.yml
├── .env.example
├── nginx/
│   └── nginx.conf
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── document.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   └── chat.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── documents.py
│   │   │   ├── chat.py
│   │   │   └── search.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   ├── rag_service.py
│   │   │   └── llm_service.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   └── retriever.py
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── security.py
│   │       └── deps.py
│   └── uploads/
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.js
    ├── public/
    └── src/
        ├── App.jsx
        ├── index.js
        ├── api/
        │   └── client.js
        ├── contexts/
        │   └── AuthContext.jsx
        ├── pages/
        │   ├── LoginPage.jsx
        │   ├── ChatPage.jsx
        │   ├── DocumentsPage.jsx
        │   ├── SearchPage.jsx
        │   └── admin/
        │       ├── UsersPage.jsx
        │       └── AdminDocumentsPage.jsx
        └── components/
            ├── Layout.jsx
            ├── Sidebar.jsx
            ├── ChatMessage.jsx
            ├── DocumentUpload.jsx
            └── ProtectedRoute.jsx
```

## DB 테이블 설계

### users
| 컬럼 | 타입 | 설명 |
|-------|------|------|
| id | UUID (PK) | 사용자 ID |
| username | VARCHAR(50) UNIQUE | 로그인 ID |
| password_hash | VARCHAR(255) | bcrypt 해시 |
| role | VARCHAR(20) | admin / user |
| is_active | BOOLEAN | 활성 여부 |
| created_at | TIMESTAMP | 생성일 |

### documents
| 컬럼 | 타입 | 설명 |
|-------|------|------|
| id | UUID (PK) | 문서 ID |
| filename | VARCHAR(255) | 원본 파일명 |
| filepath | VARCHAR(500) | 저장 경로 |
| file_type | VARCHAR(20) | pdf/docx/xlsx |
| file_size | BIGINT | 파일 크기(bytes) |
| status | VARCHAR(20) | uploading/processing/completed/failed |
| uploaded_by | UUID (FK) | 업로더 |
| created_at | TIMESTAMP | 업로드일 |
| error_message | TEXT | 실패 시 에러 |

### document_chunks
| 컬럼 | 타입 | 설명 |
|-------|------|------|
| id | UUID (PK) | 청크 ID |
| document_id | UUID (FK) | 문서 ID |
| chunk_index | INTEGER | 청크 순서 |
| content | TEXT | 청크 텍스트 |
| embedding | VECTOR(1024) | 임베딩 벡터 |
| created_at | TIMESTAMP | 생성일 |

### chat_sessions
| 컬럼 | 타입 | 설명 |
|-------|------|------|
| id | UUID (PK) | 세션 ID |
| user_id | UUID (FK) | 사용자 ID |
| title | VARCHAR(200) | 대화 제목 |
| created_at | TIMESTAMP | 생성일 |

### chat_messages
| 컬럼 | 타입 | 설명 |
|-------|------|------|
| id | UUID (PK) | 메시지 ID |
| session_id | UUID (FK) | 세션 ID |
| role | VARCHAR(20) | user / assistant |
| content | TEXT | 메시지 내용 |
| sources | JSONB | 참고 문서 목록 |
| created_at | TIMESTAMP | 생성일 |

## API 목록

### 인증 API
| Method | Path | 설명 |
|--------|------|------|
| POST | /api/auth/login | 로그인 (JWT 발급) |
| POST | /api/auth/refresh | 토큰 갱신 |
| GET | /api/auth/me | 현재 사용자 정보 |

### 사용자 API (Admin)
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/users | 사용자 목록 |
| POST | /api/users | 사용자 생성 |
| DELETE | /api/users/{id} | 사용자 삭제 |
| PATCH | /api/users/{id} | 사용자 수정 (권한 등) |

### 문서 API
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/documents | 문서 목록 |
| POST | /api/documents/upload | 문서 업로드 |
| DELETE | /api/documents/{id} | 문서 삭제 (Admin) |
| GET | /api/documents/{id}/download | 문서 다운로드 |
| GET | /api/documents/{id}/status | 문서 상태 조회 |

### 채팅 API
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/chat/sessions | 채팅 세션 목록 |
| POST | /api/chat/sessions | 새 세션 생성 |
| GET | /api/chat/sessions/{id}/messages | 메시지 목록 |
| POST | /api/chat/ask | 질문 (RAG 답변) |
| DELETE | /api/chat/sessions/{id} | 세션 삭제 |

### 검색 API
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/search?q=keyword | 문서 검색 |

## RAG 파이프라인

```
[문서 업로드]
    │
    ▼
[텍스트 추출]  ─── PDF: PyPDF2
    │              DOCX: python-docx
    │              XLSX: openpyxl
    ▼
[텍스트 청킹]  ─── 500자 단위, 50자 오버랩
    │
    ▼
[임베딩 생성]  ─── Ollama bge-m3 (1024차원)
    │
    ▼
[Vector 저장]  ─── PostgreSQL pgvector
    │
    ▼
[질문 시]
    │
    ▼
[질문 임베딩]  ─── 동일 모델로 벡터화
    │
    ▼
[유사도 검색]  ─── cosine similarity, Top-5
    │
    ▼
[프롬프트 생성] ── 시스템 프롬프트 + 컨텍스트 + 질문
    │
    ▼
[LLM 답변]    ─── Ollama llama3/mistral
    │
    ▼
[응답 반환]   ─── 답변 + 참고 문서 목록
```

## 폐쇄망 설치 방법

```bash
# 인터넷 있는 환경에서 준비
./scripts/export-images.sh   # Docker 이미지 저장
./scripts/export-models.sh   # Ollama 모델 저장

# USB/네트워크로 폐쇄망 전송 후
./scripts/import-images.sh   # Docker 이미지 로드
./scripts/import-models.sh   # Ollama 모델 로드
docker-compose up -d          # 실행
```

---

## MVP 완료 기준

- [x] docker-compose up -d 로 전체 시스템 기동
- [x] 로그인/로그아웃 동작
- [x] PDF/DOCX/XLSX 업로드 및 자동 분석
- [x] 문서 기반 AI 질문응답 (RAG)
- [x] SSE 실시간 스트리밍 답변
- [x] 문서 검색 (벡터 유사도)
- [x] 관리자: 사용자/문서 관리
- [x] 프리미엄 UI/UX 디자인
- [x] 모바일 반응형 (전 페이지)
- [x] 폐쇄망 설치 가능 (Ollama 기반)

---

## 향후 보완 과제

### 🔴 우선순위 높음 (P0)

| # | 과제 | 설명 | 분류 |
|---|------|------|------|
| 1 | **다국어 LLM 모델 교체** | llama3는 한국어 성능이 제한적. `EEVE-Korean-10.8B`, `Qwen2.5` 등 한국어 특화 모델로 교체 필요 | AI |
| 2 | **청킹 전략 고도화** | 현재 고정 500자 청킹 → 의미 단위(Semantic) 청킹, 문단/섹션 기반 분할 도입 | RAG |
| 3 | **비밀번호 변경 기능** | 사용자 본인 비밀번호 변경 UI/API 미구현 | 보안 |
| 4 | **에러 핸들링 강화** | 네트워크 단절, Ollama 미응답, DB 연결 실패 등 엣지케이스 처리 | 안정성 |
| 5 | **프로덕션 빌드 검증** | `npm run build` 정적 빌드 + Nginx 프록시 통합 테스트 | 배포 |

### 🟡 우선순위 중간 (P1)

| # | 과제 | 설명 | 분류 |
|---|------|------|------|
| 6 | **대화 컨텍스트 유지** | 현재 단일 질의 기반. 이전 대화 히스토리를 LLM 프롬프트에 포함하여 맥락 유지 | AI |
| 7 | **문서 삭제 시 벡터 정리** | 문서 삭제 시 관련 document_chunks 및 벡터 인덱스 완전 제거 확인 | DB |
| 8 | **검색 필터링** | 파일 형식, 업로드 날짜, 업로더별 필터. 키워드 + 벡터 하이브리드 검색 | 검색 |
| 9 | **문서 미리보기** | PDF 문서 인라인 뷰어, 검색 결과 하이라이팅 | UX |
| 10 | **페이지네이션** | 문서/사용자/검색 결과 목록 페이지네이션 (현재 전체 로드) | 성능 |
| 11 | **rate limiting** | API 요청 속도 제한 (특히 AI 질의), 동시 업로드 제한 | 보안 |
| 12 | **Dockerfile 최적화** | 멀티스테이지 빌드, 레이어 캐싱, 이미지 사이즈 축소 | 배포 |
| 13 | **접근성(a11y) 개선** | aria-label, 키보드 내비게이션, 스크린리더 지원, 포커스 트랩 | UX |

### 🟢 우선순위 낮음 (P2 — 향후 확장)

| # | 과제 | 설명 | 분류 |
|---|------|------|------|
| 14 | **다중 모델 지원** | Ollama 모델 선택 UI (llama3, mistral, qwen 등), 모델별 성능 비교 | AI |
| 15 | **대화 내보내기** | 채팅 기록 PDF/Markdown 내보내기 | UX |
| 16 | **문서 재처리** | 실패한 문서 재분석, 임베딩 모델 변경 후 일괄 재벡터화 | RAG |
| 17 | **사용자 활동 로그** | 로그인/문서 업로드/질의 기록. 감사 추적(audit trail) | 관리 |
| 18 | **대시보드 통계** | 일일 질의 수, 활성 사용자, 문서 증가 추세 차트 | 관리 |
| 19 | **다크 모드** | Tailwind dark: 변형 기반 테마 전환 | UX |
| 20 | **HWP 지원** | 한/글 문서 파싱 (pyhwp 또는 hwp5 라이브러리) | 문서 |
| 21 | **OCR 통합** | 이미지/스캔 PDF 텍스트 추출 (Tesseract OCR) | 문서 |
| 22 | **GPU 가속 (CUDA)** | docker-compose.yml GPU 프로파일 활성화, Ollama GPU 모드 | 성능 |
| 23 | **LDAP/AD 연동** | 기업 디렉토리 서비스 인증 통합 | 보안 |
| 24 | **SSL/TLS 설정** | Nginx 자체 서명 인증서 또는 내부 CA 연동 | 보안 |
| 25 | **자동 테스트** | 백엔드 pytest 단위/통합 테스트, 프론트엔드 React Testing Library | 품질 |
| 26 | **CI/CD 파이프라인** | GitHub Actions 또는 내부 Jenkins 연동 | 배포 |

### 기술 부채

| 항목 | 현재 상태 | 개선 방향 |
|------|----------|----------|
| 프론트엔드 상태 관리 | Context API 단순 사용 | Zustand 또는 React Query 도입 |
| API 에러 처리 | 개별 try/catch | Axios 인터셉터 + 글로벌 에러 핸들러 |
| 타입 안전성 | JSX (JavaScript) | TypeScript 마이그레이션 |
| CSS 관리 | Tailwind + 380행 커스텀 CSS | CSS-in-JS 또는 컴포넌트 분리 |
| 환경 변수 | .env 파일 직접 관리 | Docker Secrets 또는 Vault 연동 |
| DB 마이그레이션 | 자동 테이블 생성 (metadata.create_all) | Alembic 마이그레이션 도입 |
| 로깅 | print/toast 위주 | 구조화된 로깅 (structlog) |
