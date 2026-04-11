# BAIKAL Private AI — 시연 런북 (Demo Runbook)

> **버전**: 1.2 (검색 원문 미리보기, 신뢰도 개선 반영)  
> **작성일**: 2026-04-07  
> **환경**: Windows 11 + Docker Desktop (CPU 모드)  
> **총 소요 시간**: 준비 8분 + 시연 20분

---

## ✅ 서비스 준비 완료 확인 (검증된 사항)

| 항목 | 상태 | 비고 |
|------|:----:|------|
| Docker 5개 컨테이너 정상 기동 | ✅ | postgres / ollama / backend / frontend / nginx |
| LLM 모델 (qwen2.5:7b, 4.7GB) | ✅ | ollama_data 볼륨에 영구 저장 |
| 임베딩 모델 (bge-m3, 1.2GB) | ✅ | ollama_data 볼륨에 영구 저장 |
| API 헬스체크 | ✅ | `{"status":"ok","database":"connected","ollama":"connected"}` |
| PDF 문서 처리 (24 chunks) | ✅ | 텍스트 추출 + 벡터화 완료 |
| XLSX 스프레드시트 처리 | ✅ | 표 데이터 정확 추출 확인 |
| DOCX Word 문서 처리 | ✅ | 단락 분할 + 임베딩 완료 |
| HWPX 한글 문서 처리 (29 chunks) | ✅ | 예상 외 정상 처리 확인 |
| 하이브리드 검색 (벡터 70% + BM25 30%) | ✅ | MMR reranking 후 최종 5개 선택 |
| AI 스트리밍 응답 | ✅ | SSE 실시간 토큰 출력 |
| 참고문서 유사도 점수 표시 | ✅ | 예: 바이칼_취업규칙.pdf 78% |
| 관리자/매니저/사용자 3단계 역할 분리 | ✅ | admin / manager / user RBAC |
| 문서별 접근 권한 제어 | ✅ | is_public 토글 + allowed_roles 설정 |
| Cross-encoder Reranking | ✅ | ms-marco-MiniLM-L-6-v2, 폐쇄망 포함 |
| 신뢰도 점수 + 청크 미리보기 | ✅ | 답변 헤더 배지 + 출처 팝업 |
| 검색 원문 미리보기 (펼치기 버튼) | ✅ | 청크 전문 토글 표시 |
| 신뢰도 sigmoid 절대 관련도 | ✅ | sigmoid 변환 + 가중 평균 (최고점 60% + 상위절반 40%) |
| 감사 로그 (QueryLog) | ✅ | 질문·응답·신뢰도·지연시간 DB 저장 |
| 시스템 설정 페이지 | ✅ | LLM 모델 런타임 전환 + 쿼리 통계 |
| 비밀번호 변경 기능 | ✅ | 현재 세션 유지 |
| 데이터 외부 유출 없음 | ✅ | 모든 처리 로컬 서버 내 완결 |

---

## 📋 목차

1. [시연 전날 준비 (1회)](#1-시연-전날-준비-1회)
2. [당일 — 노트북 켜고 Docker 기동](#2-당일--노트북-켜고-docker-기동)
3. [헬스체크 — 모든 것이 살아있는지 확인](#3-헬스체크--모든-것이-살아있는지-확인)
4. [시연 시나리오 (20분)](#4-시연-시나리오-20분)
5. [예상 Q&A 답변 메모](#5-예상-qa-답변-메모)
6. [시연 종료](#6-시연-종료)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 시연 전날 준비 (1회)

> 이미 완료된 경우 건너뜁니다. 처음 시연하는 노트북이라면 이 섹션을 따라 진행하세요.

### 1-1. Docker Desktop 설치 확인

```powershell
docker --version
docker compose --version
```

기대 출력:
```
Docker version 27.x.x
Docker Compose version v2.x.x
```

설치되어 있지 않으면 [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/) 에서 설치합니다.

---

### 1-2. 최초 이미지 빌드 (처음 한 번만, ~5분)

```powershell
cd c:\baikal777\baikal-private-ai
docker compose -f docker-compose.cpu.yml build
```

완료 시 출력:
```
Successfully built xxxxxxxx
Successfully tagged baikal-private-ai-backend:latest
Successfully tagged baikal-private-ai-frontend:latest
```

---

### 1-3. AI 모델 다운로드 (처음 한 번만, ~20분)

```powershell
# 컨테이너 먼저 시작
docker compose -f docker-compose.cpu.yml up -d ollama

# LLM 모델 (4.7 GB)
docker exec baikal-ollama ollama pull qwen2.5:7b

# 임베딩 모델 (1.2 GB)
docker exec baikal-ollama ollama pull bge-m3

# 모델 확인
docker exec baikal-ollama ollama list
```

기대 출력:
```
NAME             ID              SIZE    MODIFIED
bge-m3:latest    xxxxxxxx        1.2 GB  x minutes ago
qwen2.5:7b       xxxxxxxx        4.7 GB  x minutes ago
```

> **수행이 되어있다면**: `ollama_data` 볼륨에 영구 저장되므로 재다운로드 불필요합니다.

---

### 1-4. 시연용 문서 준비

시연에 사용할 문서를 미리 준비합니다. 권장 파일 유형별 1~2개:

| 문서 유형 | 설명 | 효과 |
|----------|------|------|
| 취업규칙/인사규정 (PDF) | 근무시간·연차 등 규정 내용 | 정확한 규정 답변 시연 |
| 매출·실적 현황 (XLSX) | 월별 수치 데이터 | 표 데이터 추출 능력 시연 |
| 제안서·보고서 (DOCX) | 자유 형식 문서 | 요약·분석 능력 시연 |

`demo_docs/` 폴더 또는 본인이 준비한 실제 업무 문서를 사용할 수 있습니다.

---

## 2. 당일 — 노트북 켜고 Docker 기동

> **소요 시간: 약 3~5분**

### Step 1 — Docker Desktop 실행

1. 작업 표시줄의 **Docker Desktop** 아이콘을 더블클릭합니다 (또는 시작 메뉴에서 검색)
2. 시스템 트레이(오른쪽 하단)에 고래 아이콘이 **초록색** 상태가 될 때까지 대기합니다
   - 회색/주황색 = 아직 시작 중
   - 초록색 = 준비 완료 ✅

---

### Step 2 — PowerShell 열기

```
Win + X  →  "Windows PowerShell" 또는 "터미널" 클릭
```

---

### Step 3 — 서비스 기동 (명령어 1줄)

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

---

### Step 4 — 컨테이너 상태 확인

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "baikal"
```

기대 출력:
```
baikal-nginx      Up X seconds    0.0.0.0:80->80/tcp
baikal-frontend   Up X seconds    0.0.0.0:3000->80/tcp
baikal-backend    Up X seconds    0.0.0.0:8000->8000/tcp
baikal-ollama     Up X seconds
baikal-postgres   Up X seconds (healthy)
```

모든 컨테이너 상태가 `Up` 이면 정상입니다.

---

## 3. 헬스체크 — 모든 것이 살아있는지 확인

> **기동 후 30초 대기 권장** (백엔드 DB 연결 완료 때까지)

### 헬스체크 명령어

```powershell
# 방법 1: curl (PowerShell 7+)
curl -s http://localhost/api/health | ConvertFrom-Json

# 방법 2: Invoke-RestMethod
Invoke-RestMethod http://localhost/api/health
```

### ✅ 정상 응답

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

`database`와 `ollama` 모두 `"connected"`이면 **시연 준비 완료**입니다.

### ❌ 이상 응답 시

```powershell
# 백엔드 최근 로그 확인
docker logs baikal-backend --tail 30
```

---

### 브라우저 접속 확인

1. Chrome 또는 Edge를 엽니다
2. 주소창에 `http://localhost` 입력 (포트 번호 없음)
3. BAIKAL Private AI 로그인 화면이 나타나면 ✅

---

## 4. 시연 시나리오 (20분)

### 접속 정보

| 항목 | 값 |
|------|----|
| **URL** | `http://localhost` |
| **관리자 ID** | `admin` |
| **관리자 PW** | `Baikal@2026!` |

---

### 🎬 Scene 1 — 로그인 (1분)

**목적**: 깔끔한 UI 첫인상 전달

1. 브라우저에서 `http://localhost` 접속
2. ID `admin` / PW `Baikal@2026!` 입력 후 **로그인** 클릭
3. AI 질문응답 화면으로 이동

**강조 포인트**:
- 다크 테마 기반 모던 UI
- 폐쇄망 전용 시스템 (외부 CDN 없음)

---

### 🎬 Scene 2 — 문서 업로드 (2분)

**목적**: 내부 문서를 AI가 학습하는 과정 시연

1. 좌측 사이드바 **"문서 관리"** 클릭
2. 준비한 PDF/DOCX/XLSX 파일을 업로드 영역에 **드래그&드롭**
3. 상태 변화를 실시간으로 보여줌: `처리 중` → `완료`

**강조 포인트**:
- 업로드 즉시 텍스트 자동 추출 + AI 임베딩
- 외부 API 없이 서버 자체 처리
- 완료 후 즉시 질문 가능

> **팁**: 이미 업로드된 문서가 있다면 문서 목록에서 "완료" 상태 6개를 보여주고 바로 Scene 3으로 진행합니다.

---

### 🎬 Scene 3 — AI 질문응답 (6분)

**목적**: 핵심 기능 — 문서 기반 AI 답변 시연

1. 좌측 사이드바 **"AI 질문응답"** 클릭
2. **"+ 새 대화"** 버튼 클릭
3. 아래 질문을 순서대로 입력

---

#### 테스트 질문 1 — 규정 문서 (취업규칙/인사규정 PDF)

```
바이칼 취업규칙에서 근무시간은 어떻게 되나요?
```

✅ **기대 답변 예시**:
> 근무시간은 오전 9시부터 오후 6시까지이며, 점심시간은 12시~1시입니다. (바이칼_취업규칙.pdf 78% 일치)

**강조 포인트**:
- 답변이 **글자 단위로 실시간 스트리밍** 됩니다
- 답변 하단에 **참고문서명 + 유사도 점수** 표시
- 내부 문서 기반 정확한 답변 (할루시네이션 최소화)

---

#### 테스트 질문 2 — 표 데이터 (매출현황 XLSX)

```
2025년 매출 현황을 월별로 요약해줘
```

✅ **기대 답변 예시**:
> 2025년 매출 현황 (단위: 만원)은 1월 솔루션 XXX, SI XXX, 유지보수 XXX... (12월까지 전체 표 재현)

**강조 포인트**:
- 엑셀 숫자 데이터를 AI가 정확하게 읽어서 답변
- "AI가 스프레드시트도 이해한다"

---

#### 테스트 질문 3 — 후속 질문 (맥락 유지)

```
그 중에서 가장 매출이 높은 달은 언제고, 이유는 뭐라고 생각해?
```

✅ **기대 답변 예시**:
> 이전 대화의 매출 데이터를 바탕으로 가장 높은 달과 가능한 원인을 분석하여 답변

**강조 포인트**:
- 같은 세션 내 **대화 맥락 유지** (최근 3턴 기억)
- 단순 검색이 아닌 **분석·추론** 능력

---

#### 문서 필터 기능 시연 (선택)

1. 채팅 입력창 왼쪽 **깔때기(퍼널) 버튼** 클릭
2. 특정 문서 1~2개만 선택 후 질문
3. 선택한 문서에서만 답변이 나오는 것 확인

**강조 포인트**:
- "이 계약서 내용만 물어보기" 등 범위 제한 가능
- 문서가 많을수록 효과적

---

#### 신뢰도 점수 + 청크 미리보기 시연

1. AI 답변 헤더에 표시된 **`신뢰도 XX%` 배지** 확인
2. 답변 하단 출처 배지(예: `바이칼_취업규칙.pdf 78%`) **클릭**
3. 해당 청크 원문 팝업 확인

**강조 포인트**:
- 답변 근거를 직접 확인 가능 → 신뢰도 향상
- "AI가 어디서 가져온 내용인지" 투명하게 공개

---

### 🎬 Scene 4 — 문서 검색 (2분)

**목적**: Search 기능 시연

1. 좌측 사이드바 **"문서 검색"** 클릭
2. 검색창에 키워드 입력 후 검색

**검색 테스트 예시**:
```
연차 휴가
```
또는
```
RAG 시스템 평가
```

**검색 모드 전환 시연**:
- **하이브리드** (기본) → **키워드** → **벡터** 순서로 전환하며 결과 비교

**강조 포인트**:
- 유사도 점수(%)로 관련도 정량화
- 벡터 검색 = 단어가 달라도 의미가 같으면 검색됨
- "연차"로 검색해도 "유급휴가" 내용이 검색되는 사례
- 결과 카드 하단 **"원문 미리보기"** 버튼 클릭 → 청크 전문 펼쳐보기

---

### 🎬 Scene 5 — 사용자 관리 (2분)

**목적**: 기업 환경 다중 사용자 지원 + 3단계 역할 시연

1. 좌측 사이드바 **"사용자 관리"** 클릭 (관리자 전용 메뉴)
2. **"+ 사용자 추가"** 버튼으로 새 계정 생성
   - 사용자명: `manager1`
   - 비밀번호: `Test@1234`
   - 역할: `매니저`
3. 기존 사용자 역할 배지 클릭 → **admin → 매니저 → 사용자** 순환 전환 확인
4. 통계 카드 4개 확인: 전체 / 관리자 / 매니저 / 사용자 수

**강조 포인트**:
- **3단계 역할 RBAC**: admin(전체) / manager(문서 관리) / user(조회만)
- 부서별·직급별 계정 분리 운영 가능
- 계정 비활성화로 즉시 접근 차단

---

---

### 🎬 Scene 6 — 문서 접근 권한 제어 (2분)

**목적**: 문서별 세밀한 접근 제어 시연

1. 좌측 사이드바 **"문서 관리"** 클릭 (관리자 뷰)
2. 문서 목록에서 특정 문서 행 오른쪽 **🛡 방패 버튼** 클릭
3. 권한 편집 모달 확인:
   - **전체공개** 토글 ON/OFF (전체공개 vs 역할 제한)
   - **허용 역할** 멀티셀렉트: admin / manager / user 중 선택
4. 예시: `전체공개 OFF` + `허용 역할: admin, manager`로 저장
5. 사용자 계정으로 재로그인 후 해당 문서 검색 시 결과에 포함되지 않음을 확인

**강조 포인트**:
- 문서별로 "어느 직급까지 열람 가능"을 세밀하게 설정
- 인사·재무·기밀 문서 차등 관리 → 실제 기업 업무 요건 충족
- 설정 즉시 반영 (서버 재시작 불필요)

---

### 🎬 Scene 7 — 시스템 설정 (2분)

**목적**: LLM 모델 런타임 전환 + 사용 통계 시연

1. 좌측 사이드바 **"시스템 설정"** 클릭 (⚙️ 아이콘)
2. **LLM 모델 섹션** 확인:
   - 현재 활성 모델(예: `qwen2.5:7b`) 초록 배지 표시
   - Ollama에 설치된 모델 목록 카드
   - 다른 모델 카드 클릭 → 런타임 즉시 전환
3. **임베딩 모델 섹션**: `bge-m3` 표시 (변경 불가 안내)
4. **쿼리 통계 카드** 3개 확인:
   - 총 질의 횟수 / 평균 신뢰도 / 평균 응답시간
5. **최근 질의 로그 테이블**: 질문 내용·신뢰도·응답시간·시각

**강조 포인트**:
- 모델 교체 시 `.env` 수정·재시작 없이 즉시 적용
- 감사 로그로 "누가 무엇을 물었는지" 추적 가능 → 보안·컴플라이언스 대응
- 신뢰도 추이로 RAG 품질 모니터링

---

### 🎬 Scene 8 — (선택) 폐쇄망 증명 (1분)

**목적**: "데이터가 외부로 나가지 않는다"는 것을 눈으로 증명

1. 브라우저 개발자 도구 (F12) → **Network 탭**
2. AI 질문 전송
3. `localhost` 또는 `127.0.0.1` 외의 외부 도메인 요청이 **전혀 없음** 확인

**강조 포인트**:
- ChatGPT, Claude, Google 등 **외부 API 호출 없음**
- 고객사 데이터가 서버 밖으로 나가지 않음
- 금융·공공·의료 등 보안 규제 환경에 적합

---

## 5. 예상 Q&A 답변 메모

| 질문 | 답변 |
|------|------|
| "외부 인터넷이 없어도 되나요?" | 네. 모델과 코드 모두 로컬에 있어 완전 폐쇄망 운영 가능합니다. |
| "답변 속도를 높일 수 있나요?" | GPU 서버 추가 시 약 2분 → 8초로 단축됩니다. |
| "얼마나 많은 문서를 처리할 수 있나요?" | pgvector HNSW 인덱스 기반으로 수백만 청크 처리 가능. 로컬 PC 기준 실용 한계는 1,000~3,000개 문서입니다. |
| "어떤 파일 형식을 지원하나요?" | PDF, DOCX, XLSX, HWP, HWPX 지원. 추가 형식은 커스터마이징 가능합니다. |
| "데이터는 어디에 저장되나요?" | 서버 내 PostgreSQL DB에만 저장. 벡터 데이터도 pgvector로 로컬 저장합니다. |
| "여러 명이 동시에 쓸 수 있나요?" | 백엔드 4-worker로 동시 처리. GPU 환경에서 더 많은 동시 사용자 지원 가능합니다. |
| "설치가 어렵나요?" | Docker Desktop 설치 후 명령어 1줄로 기동. 폐쇄망은 이미지 파일로 이전합니다. |
| "권한을 세분화할 수 있나요?" | admin/manager/user 3단계에 더해 문서별 접근 역할까지 설정 가능합니다. |
| "어떤 AI 모델을 쓰나요?" | 기본 qwen2.5:7b이지만 관리자 페이지에서 Ollama에 설치된 모델로 즉시 전환 가능합니다. |
| "AI 답변을 믿을 수 있나요?" | 답변마다 신뢰도 점수와 출처 청크 원문을 표시합니다. 근거 없는 답변은 신뢰도가 낮게 표시됩니다. |
| "사용 이력을 볼 수 있나요?" | 시스템 설정 페이지에서 질문 이력·신뢰도·응답시간 감사 로그를 확인할 수 있습니다. |

---

## 6. 시연 종료

### 서비스 중단 (일시 중지)

컨테이너를 **중지만** 합니다 (데이터 보존):

```powershell
cd c:\baikal777\baikal-private-ai
docker compose -f docker-compose.cpu.yml stop
```

### 다음 번 재시작

```powershell
docker compose -f docker-compose.cpu.yml up -d
```

> 볼륨(postgres_data, ollama_data, upload_data)에 모든 데이터가 유지됩니다.  
> 재시작 후 약 30초 내 완전 기동됩니다.

### 완전 제거 (필요시만)

```powershell
# 컨테이너+네트워크 삭제 (볼륨은 유지)
docker compose -f docker-compose.cpu.yml down

# 볼륨까지 삭제 (데이터 완전 초기화 — 주의!)
docker compose -f docker-compose.cpu.yml down -v
```

---

## 7. 트러블슈팅

### ❌ 컨테이너가 시작되지 않을 때

```powershell
# 문제 컨테이너 로그 확인
docker logs baikal-backend --tail 50
docker logs baikal-postgres --tail 30
docker logs baikal-ollama --tail 20
```

---

### ❌ `http://localhost` 접속이 안 될 때

```powershell
# nginx 상태 확인
docker ps | Select-String "nginx"

# nginx 재시작
docker restart baikal-nginx
```

---

### ❌ 헬스체크에서 `ollama: disconnected`

```powershell
# Ollama 컨테이너 재시작
docker restart baikal-ollama

# 30초 대기 후 재확인
Start-Sleep 30
Invoke-RestMethod http://localhost/api/health
```

---

### ❌ AI 답변이 전혀 안 나올 때

```powershell
# 모델 목록 확인
docker exec baikal-ollama ollama list

# 없으면 재다운로드
docker exec baikal-ollama ollama pull qwen2.5:7b
docker exec baikal-ollama ollama pull bge-m3
```

---

### ❌ Docker Desktop이 켜지지 않을 때 (Windows)

1. 작업 관리자(Ctrl+Shift+Esc) → `Docker Desktop` 프로세스 종료
2. Docker Desktop 재시작
3. WSL2 관련 오류 시: PowerShell 관리자 권한으로 `wsl --update` 실행

---

### ❌ 포트 80 충돌 (IIS 또는 다른 서비스)

```powershell
# 80 포트 점유 프로세스 확인
netstat -ano | Select-String ":80 "

# 해당 PID 종료 후 nginx 재시작
docker restart baikal-nginx
```

---

## 📌 빠른 참조 카드 (출력 가능)

```
┌─────────────────────────────────────────────────┐
│         BAIKAL Private AI — 시연 체크리스트       │
├─────────────────────────────────────────────────┤
│                                                 │
│  □ Docker Desktop 초록불 확인                    │
│  □ PowerShell 열기                              │
│  □ cd c:\baikal777\baikal-private-ai            │
│  □ docker compose -f docker-compose.cpu.yml     │
│      up -d                                      │
│  □ 30초 대기                                    │
│  □ Invoke-RestMethod http://localhost/api/health │
│    → "status":"ok" 확인                         │
│  □ 브라우저 http://localhost 접속               │
│                                                 │
├─────────────────────────────────────────────────┤
│  ID: admin  /  PW: Baikal@2026!                 │
├─────────────────────────────────────────────────┤
│  시연 순서: 로그인 → 문서업로드 → AI질문(3개)     │
│            → 문서검색 → 사용자관리 → 폐쇄망증명  │
└─────────────────────────────────────────────────┘
```

---

> **문서 끝** | BAIKAL Private AI 시연 런북 v1.0  
> 문의: 시스템 관리자에게 연락하세요
