# BAIKAL Private AI — 데모 가이드

> **대상**: 고객사 방문 데모 / 내부 시연  
> **환경**: Windows 10/11 + Docker Desktop (CPU 모드)  
> **소요 시간**: 최초 설정 15분 / 이후 데모 당일 3분
> **최종 업데이트**: 2026-04-06

---

## 목차

1. [사전 준비 (최초 1회)](#1-사전-준비-최초-1회)
2. [데모 당일 — 원클릭 실행](#2-데모-당일--원클릭-실행)
3. [데모 시나리오 (20분)](#3-데모-시나리오-20분)
4. [데모 종료](#4-데모-종료)
5. [트러블슈팅](#5-트러블슈팅)

---

## 1. 사전 준비 (최초 1회)

### 1-1. 필수 소프트웨어

| 소프트웨어 | 버전 | 확인 명령 |
|------------|------|-----------|
| Docker Desktop | 27 이상 | `docker --version` |
| (선택) Git | 최신 | `git --version` |

> Python, Node.js, PostgreSQL, Ollama는 **모두 Docker 컨테이너 내부에서 실행**됩니다. 별도 설치 불필요.

### 1-2. Docker 이미지 빌드 (처음 한 번만, 약 5분)

```powershell
cd c:\baikal777\baikal-private-ai
docker compose -f docker-compose.cpu.yml build
```

### 1-3. AI 모델 다운로드 (처음 한 번만, 약 20분)

```powershell
# Ollama 컨테이너 먼저 시작
docker compose -f docker-compose.cpu.yml up -d ollama

# LLM 모델 (4.7 GB)
docker exec baikal-ollama ollama pull qwen2.5:7b

# 임베딩 모델 (1.2 GB)
docker exec baikal-ollama ollama pull bge-m3

# 확인
docker exec baikal-ollama ollama list
```

> 모델은 `ollama_data` Docker 볼륨에 영구 저장됩니다. 재기동 시 재다운로드 불필요.

---

## 2. 데모 당일 — 기동 (3분)

### Step 1 — Docker Desktop 실행

작업 표시줄 또는 시작 메뉴에서 Docker Desktop을 실행합니다.  
시스템 트레이 고래 아이콘이 **초록색**이 될 때까지 대기합니다.

### Step 2 — 서비스 기동

```powershell
cd c:\baikal777\baikal-private-ai
docker compose -f docker-compose.cpu.yml up -d
```

기대 출력:
```
[+] Running 5/5
 ✔ Container baikal-postgres   Started
 ✔ Container baikal-ollama     Started
 ✔ Container baikal-backend    Started
 ✔ Container baikal-frontend   Started
 ✔ Container baikal-nginx      Started
```

### Step 3 — 헬스체크 (30초 후)

```powershell
Invoke-RestMethod http://localhost/api/health
```

정상 응답:
```json
{"status":"ok","components":{"database":"connected","ollama":"connected"}}
```

### 접속 정보

| 항목 | 값 |
|------|----|
| URL | `http://localhost` |
| 관리자 ID | `admin` |
| 관리자 PW | `Baikal@2026!` |

---

## 3. 데모 시나리오 (20분)

### 접속 정보

| 항목 | 값 |
|------|-----|
| URL | `http://localhost` |
| 관리자 ID | `admin` |
| 관리자 PW | `Baikal@2026!` |

---

### Step 1 — 로그인 (1분)

1. 브라우저에서 `http://localhost` 접속
2. ID: `admin`, PW: `Baikal@2026!` 입력 후 로그인
3. **포인트**: 프리미엄 다크 테마 UI, Linear/Vercel 스타일 디자인 강조

---

### Step 2 — 문서 업로드 (3분)

1. 좌측 사이드바에서 **문서관리** 클릭
2. PDF, DOCX, XLSX, HWP, HWPX 파일을 드래그&드롭 또는 클릭하여 업로드
3. 상태가 `processing` → `completed` 로 자동 변환되는 것 확인
4. **포인트**: 업로드 즉시 자동 텍스트 추출 + 벡터화 (외부 API 없음)

> 샘플 문서: `demo_docs/` 폴더의 파일 활용 가능

---

### Step 3 — AI 질문응답 (6분)

1. 좌측 사이드바에서 **채팅** 클릭
2. 새 대화 세션 생성
3. 업로드한 문서 내용 기반으로 질문 입력
   - 예: `"이 문서의 핵심 내용을 요약해줘"`
   - 예: `"BAIKAL Private AI의 주요 기능은 무엇인가요?"`
4. **포인트**:
   - 답변이 토큰 단위로 **실시간 스트리밍**되는 효과 강조
   - 답변 하단에 **참고문서 출처** 표시 + 클릭 시 미리보기
   - 신뢰도 점수 표시 (sigmoid 변환 기반 절대 관련도)
   - Ollama 로컬 실행 → **외부 통신 없음** 강조

---

### Step 4 — 문서 검색 (3분)

1. 좌측 사이드바에서 **검색** 클릭
2. 키워드 입력 후 검색 모드 선택 (하이브리드 / 벡터 / 키워드)
3. 결과 카드 하단 **"원문 미리보기"** 버튼 클릭 → 청크 전문 펼쳐보기
4. **포인트**: 키워드 매칭이 아닌 **의미 기반(벡터) 유사도 검색**, 유사도 점수 표시

---

### Step 5 — 사용자 관리 (2분)

1. 좌측 사이드바에서 **사용자 관리** 클릭 (관리자 전용)
2. 새 사용자 생성, 역할(admin/manager/user) 설정, 비활성화 토글 시연
3. **포인트**: 다중 사용자 / 역할 기반 접근 제어 (3단계)

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
docker compose -f docker-compose.cpu.yml stop
```

데이터는 볼륨에 보존됩니다. 다음 번 재기동:
```powershell
docker compose -f docker-compose.cpu.yml up -d
```

---

## 5. 트러블슈팅

### 백엔드가 시작되지 않을 때

```powershell
docker logs baikal-backend --tail 30
```

| 증상 | 원인 | 해결 |
|------|------|------|
| `SyntaxError` | Python 코드 오류 | 로그 확인 후 파일 수정 → 재빌드 |
| `Connection refused` | postgres 미시작 | `docker compose ... up -d` 재실행 |
| `502 Bad Gateway` | 백엔드 기동 중 | 30초 대기 후 새로고침 |

### Ollama 연결 오류

```powershell
# Ollama 재시작
docker restart baikal-ollama
Start-Sleep 20
Invoke-RestMethod http://localhost/api/health
```

### 모델이 없을 때

```powershell
docker exec baikal-ollama ollama list
docker exec baikal-ollama ollama pull qwen2.5:7b
docker exec baikal-ollama ollama pull bge-m3
```

### 포트 80 충돌

```powershell
netstat -ano | Select-String ":80 "
# PID 확인 후 해당 프로세스 종료
docker restart baikal-nginx
```

---

## 참고

| 파일 | 설명 |
|------|------|
| `.env` | DB URL, Ollama URL, JWT Secret 등 환경변수 |
| `docker-compose.cpu.yml` | CPU 환경 5개 컨테이너 구성 |
| `scripts/api_test.py` | API 자동화 테스트 (29개 항목) |
| `docs/TEST_RESULTS.md` | API 테스트 결과서 |
| `scripts/create_demo_docs.py` | 샘플 문서 자동 업로드 스크립트 |
| `backend/app/config.py` | 백엔드 설정 기본값 |
| `docs/USER_MANUAL.md` | 사용자 매뉴얼 |
| `docs/ADMIN_MANUAL.md` | 관리자 매뉴얼 |
