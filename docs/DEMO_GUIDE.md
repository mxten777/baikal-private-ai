# BAIKAL Private AI — 로컬 데모 가이드

> **대상**: 고객사 방문 데모 / 내부 시연  
> **환경**: Windows 10/11 (로컬 직접 실행, Docker 불필요)  
> **소요 시간**: 최초 설정 10분 / 이후 데모 당일 1분

---

## 목차

1. [사전 준비 (최초 1회)](#1-사전-준비-최초-1회)
2. [데모 당일 — 원클릭 실행](#2-데모-당일--원클릭-실행)
3. [데모 시나리오 (15분)](#3-데모-시나리오-15분)
4. [데모 종료](#4-데모-종료)
5. [트러블슈팅](#5-트러블슈팅)

---

## 1. 사전 준비 (최초 1회)

### 1-1. 필수 소프트웨어 확인

| 소프트웨어 | 버전 | 확인 명령 |
|------------|------|-----------|
| Python | 3.11 이상 | `python --version` |
| Node.js | 18 이상 | `node --version` |
| PostgreSQL | 16 | 서비스 관리자에서 확인 |
| Ollama | 최신 | `ollama --version` |

### 1-2. Ollama 모델 다운로드

```powershell
ollama pull qwen2.5:7b   # LLM (4.7 GB) — 처음 한 번만
ollama pull bge-m3        # 임베딩 (1.2 GB) — 처음 한 번만
```

> 모델이 이미 있으면 스크립트가 자동으로 건너뜁니다.

### 1-3. DB 초기화 (최초 1회)

```powershell
$env:PGPASSWORD = "baikal_secret_2024"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h 127.0.0.1 -c "CREATE DATABASE baikal_ai;" 2>$null
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h 127.0.0.1 -c "CREATE USER baikal WITH PASSWORD 'baikal_secret_2024';" 2>$null
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h 127.0.0.1 -c "GRANT ALL PRIVILEGES ON DATABASE baikal_ai TO baikal;" 2>$null
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h 127.0.0.1 -d baikal_ai -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>$null
```

> 이미 설정되어 있으면 생략해도 됩니다.

### 1-4. 백엔드 패키지 설치

```powershell
cd c:\baikal777\baikal-private-ai\backend
pip install -r requirements.txt
```

### 1-5. 프론트엔드 패키지 설치

```powershell
cd c:\baikal777\baikal-private-ai\frontend
npm install
```

---

## 2. 데모 당일 — 원클릭 실행

PowerShell을 열고 아래 명령 **한 줄**만 입력합니다.

```powershell
cd c:\baikal777\baikal-private-ai
.\scripts\start-local.ps1
```

### 실행 순서 (자동)

```
[1/4] 사전 체크
      - Ollama 모델 확인 (없으면 자동 pull)
      - PostgreSQL 서비스 자동 시작
      - 포트 충돌(8000, 3000) 자동 정리

[2/4] 백엔드 시작 (FastAPI :8000)
      - DB 연결 및 테이블 자동 생성
      - 헬스체크 통과 확인 후 다음 단계

[3/4] 프론트엔드 시작 (React :3000)
      - 포트 열림 확인 후 다음 단계

[4/4] 브라우저 자동 오픈 → http://localhost:3000
```

### 정상 완료 화면

```
  ============================================
  [READY] BAIKAL Private AI is running!

  URL   : http://localhost:3000
  API   : http://localhost:8000
  Login : admin / admin1234

  Stop  : .\scripts\start-local.ps1 -Stop
  ============================================
```

---

## 3. 데모 시나리오 (15분)

### 접속 정보

| 항목 | 값 |
|------|----|
| URL | http://localhost:3000 |
| 관리자 계정 | `admin` / `admin1234` |

---

### Step 1 — 로그인 (1분)

1. 브라우저에서 `http://localhost:3000` 접속
2. ID: `admin`, PW: `admin1234` 입력 후 로그인
3. **포인트**: 프리미엄 다크 테마 UI, Linear/Vercel 스타일 디자인 강조

---

### Step 2 — 문서 업로드 (2분)

1. 좌측 사이드바에서 **문서관리** 클릭
2. PDF 또는 DOCX 파일을 드래그&드롭 또는 클릭하여 업로드
3. 상태가 `processing` → `completed` 로 자동 변환되는 것 확인
4. **포인트**: 업로드 즉시 자동 텍스트 추출 + 벡터화 (외부 API 없음)

> 샘플 문서: `demo_docs/` 폴더의 파일 활용 가능

---

### Step 3 — AI 질문응답 (5분)

1. 좌측 사이드바에서 **채팅** 클릭
2. 새 대화 세션 생성
3. 업로드한 문서 내용 기반으로 질문 입력
   - 예: `"이 문서의 핵심 내용을 요약해줘"`
   - 예: `"~~ 에 대해 설명해줘"`
4. **포인트**:
   - 답변이 토큰 단위로 **실시간 스트리밍**되는 효과 강조
   - 답변 하단에 **참고문서 출처** 표시
   - Ollama 로컬 실행 → **외부 통신 없음** 강조

---

### Step 4 — 문서 검색 (2분)

1. 좌측 사이드바에서 **검색** 클릭
2. 키워드 입력 후 검색
3. **포인트**: 키워드 매칭이 아닌 **의미 기반(벡터) 유사도 검색**, 유사도 점수 표시

---

### Step 5 — 사용자 관리 (2분)

1. 좌측 사이드바에서 **사용자 관리** 클릭 (관리자 전용)
2. 새 사용자 생성, 역할(admin/user) 설정, 비활성화 토글 시연
3. **포인트**: 다중 사용자 / 역할 기반 접근 제어

---

### Step 6 — 모바일 반응형 (1분)

1. 브라우저 창 폭을 줄여서 모바일 뷰로 전환
2. **포인트**: 햄버거 메뉴, 슬라이드 사이드바, 적응형 테이블 자동 전환

---

### Step 7 — 마무리 (2분)

**핵심 메시지**:
- 외부 인터넷 **완전 차단 환경**에서도 동작
- Ollama 기반 **로컬 LLM** — 데이터가 외부로 나가지 않음
- 폐쇄망(에어갭) 환경에 USB 1개로 설치 가능

---

## 4. 데모 종료

```powershell
cd c:\baikal777\baikal-private-ai
.\scripts\start-local.ps1 -Stop
```

백엔드, 프론트엔드 프로세스를 모두 정리합니다.

---

## 5. 트러블슈팅

### 백엔드가 시작되지 않을 때

```powershell
# 직접 실행해서 오류 메시지 확인
cd c:\baikal777\baikal-private-ai\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**자주 발생하는 원인**:

| 증상 | 원인 | 해결 |
|------|------|------|
| `getaddrinfo failed` | DB 호스트 연결 실패 | `.env`의 `localhost` → `127.0.0.1` 변경 |
| `password authentication failed` | DB 비밀번호 오류 | DB 사용자/비밀번호 재확인 |
| `ModuleNotFoundError` | 패키지 미설치 | `pip install -r requirements.txt` 재실행 |
| 포트 8000 충돌 | 다른 프로세스 점유 | `start-local.ps1 -Stop` 후 재실행 |

### 프론트엔드가 뜨지 않을 때

```powershell
cd c:\baikal777\baikal-private-ai\frontend
npm install   # node_modules 재설치
npm start
```

### Ollama 모델 응답이 없을 때

```powershell
ollama list           # 모델 설치 확인
ollama ps             # 현재 실행 중인 모델 확인
Invoke-RestMethod http://127.0.0.1:11434/api/tags   # Ollama API 직접 확인
```

### 헬스체크 API 직접 확인

```powershell
Invoke-RestMethod http://localhost:8000/api/health
# 정상: status=ok, database=connected, ollama=connected
```

### psql PATH 문제

PowerShell에서 `psql`을 인식 못하면:

```powershell
$env:PATH += ";C:\Program Files\PostgreSQL\16\bin"
```

---

## 참고

| 파일 | 설명 |
|------|------|
| `.env` | DB URL, Ollama URL, JWT Secret 등 환경변수 |
| `scripts/start-local.ps1` | 원클릭 데모 실행/종료 스크립트 |
| `scripts/create_demo_docs.py` | 샘플 문서 자동 업로드 스크립트 |
| `backend/app/config.py` | 백엔드 설정 기본값 |
| `docs/USER_MANUAL.md` | 사용자 매뉴얼 |
| `docs/ADMIN_MANUAL.md` | 관리자 매뉴얼 |
