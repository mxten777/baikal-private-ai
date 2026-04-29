# BAIKAL Private AI — 시연 런북 (Demo Runbook)

> **버전**: 1.4 (신뢰도 게이트·답변 거절, 면책 배너, 보안 감사, 법령 데모 패키지 반영)  
> **작성일**: 2026-04-29  
> **환경**: Windows 11 + Docker Desktop (CPU 모드)  
> **총 소요 시간**: 준비 8분 + 시연 20분

---

## ✅ 서비스 준비 완료 확인 (검증된 사항)

| 항목 | 상태 | 비고 |
|------|:----:|------|
| Docker 5개 컨테이너 정상 기동 | ✅ | postgres / ollama / backend / frontend / nginx |
| LLM 모델 (qwen2.5:7b, 4.7GB) | ✅ | ollama_data 볼륨에 영구 저장 |
| 비전/OCR 모델 (qwen2.5vl:7b) | ✅ | 이미지·PDF OCR 처리용, CPU ~2분 |
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
| 신뢰도 경고 배지 (< 40%) | ✅ | 주황색 배지로 낮은 신뢰도 시각 경고 |
| 검색 원문 미리보기 (펼치기 버튼) | ✅ | 청크 전문 토글 표시 |
| HyDE 모드 (💡 버튼) | ✅ | 가상 답변 임베딩으로 검색 정확도 향상 |
| 답변 피드백 (👍👎 버튼) | ✅ | 만족/불만족 피드백 저장 |
| 신뢰도 sigmoid 절대 관련도 | ✅ | sigmoid 변환 + 가중 평균 (최고점 60% + 상위절반 40%) |
| **신뢰도 게이트 / 답변 거절** | ✅ | top1<0.45 또는 confidence<0.40 시 거절 (할루시네이션 방어) |
| **면책 안내 배너** | ✅ | 상단 고정 — "답변은 참고용, 법적 효력 판단 근거 아님" |
| 감사 로그 (QueryLog) | ✅ | 질문·응답·신뢰도·지연시간·거절사유 DB 저장 |
| 시스템 설정 페이지 | ✅ | LLM 모델 런타임 전환 + 쿼리 통계 |
| 비밀번호 변경 기능 | ✅ | 현재 세션 유지 |
| 데이터 외부 유출 없음 | ✅ | 모든 처리 로컬 서버 내 완결 |
| **보안 감사 스크립트** | ✅ | `scripts/security_audit.py` — SECRET_KEY/포트/외부도메인 점검 |
| **오프라인 배포 패키지** | ✅ | `scripts/export-images.ps1`, `export-models.ps1` (폐쇄망 이전용) |
| **법령 데모 패키지** | ✅ | `demo_docs/law/` — 표준 5건·질문 20개·시연 시나리오·정답표 |

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
NAME                  ID              SIZE    MODIFIED
bge-m3:latest         xxxxxxxx        1.2 GB  x minutes ago
qwen2.5:7b            xxxxxxxx        4.7 GB  x minutes ago
qwen2.5vl:7b          xxxxxxxx        6.0 GB  x minutes ago
```

> `qwen2.5vl:7b`는 PDF 이미지 OCR 및 표 추출에 사용됩니다. CPU 환경에서 페이지당 약 20~30초 소요.

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

### 🔥 시연 직전 워밍업 (필수, 30초)

첫 질의는 LLM cold-start 때문에 30~60초 걸립니다. 시연 시작 **5분 전**에 반드시 워밍업하세요.

```powershell
# 한 번에 헬스체크 + 워밍업 + 거절 검증
.\scripts\demo_warmup.ps1
```

또는 수동:
1. `http://localhost` 로그인 후 아무 질문 1회 ("테스트") → 응답 받을 때까지 대기
2. 답변이 나오면 워밍업 완료 — 이후부터는 5~10초 내 응답

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
4. **상단 호박색(amber) 배너** 확인 — "BAIKAL은 업로드된 문서 검색 보조 도구이며 답변은 참고용입니다"

**강조 포인트**:
- 다크 테마 기반 모던 UI
- 폐쇄망 전용 시스템 (외부 CDN 없음)
- **면책 배너로 책임 범위 명확화** → 법적 리스크 사전 차단

---

### 🎬 Scene 2 — 문서 업로드 (2분)

**목적**: 내부 문서를 AI가 학습하는 과정 시연

1. 좌측 사이드바 **"문서 관리"** 클릭
2. 준비한 PDF/DOCX/XLSX 파일을 업로드 영역에 **드래그&드롭**
3. 상태 변화를 실시간으로 보여줌: `처리 중` → `완료`

**강조 포인트**:
- 업로드 즉시 텍스트 자동 추출 + AI 임베딩
- 외부 API 없이 서버 자체 처리
- PDF는 qwen2.5vl 비전 모델로 OCR 처리 (CPU 환경: 문서 길이에 따라 30초~2분)
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

1. 채팅 입력창 왼쪽 두 번째 **깔때기(🔽) 버튼** 클릭
2. 특정 문서 1~2개만 선택 후 질문
3. 선택한 문서에서만 답변이 나오는 것 확인

**강조 포인트**:
- "이 계약서 내용만 물어보기" 등 범위 제한 가능
- 문서가 많을수록 효과적

---

#### 💡 HyDE 모드 시연 (선택)

1. 채팅 입력창 왼쪽 맨 첫 번째 **💡 버튼** 클릭 (비활성: 회색 → 활성: 황색)
2. 동일한 질문을 HyDE 모드 OFF/ON으로 각각 입력
3. 답변 품질 비교

**HyDE란?** (Hypothetical Document Embeddings)
- AI가 먼저 "예상 답변 초안"을 생성한 뒤, 그 초안의 임베딩으로 문서를 검색
- 단순 키워드 매칭보다 의미적으로 더 깊은 검색 가능
- 검색이 어렵거나 추상적인 질문에 효과적

**강조 포인트**:
- "ChatGPT에게 물어보는 것과 달리, 먼저 관련 내용을 찾아주는 방식이 독특하다"
- HyDE 활성 시 입력창 테두리가 황색으로 변하고 "HyDE 모드"라는 안내 텍스트 표시

---

#### 👍👎 피드백 기능 시연 (선택)

1. AI 답변이 출력된 후 하단의 **👍 / 👎 버튼** 확인
2. 만족하는 답변에 👍, 아닌 답변에 👎 클릭

**강조 포인트**:
- 누적 피드백으로 RAG 품질 추이 모니터링 가능
- 감사 로그와 함께 "AI 활용 품질" 지표로 활용

---

#### 신뢰도 점수 + 청크 미리보기 시연

1. AI 답변 헤더에 표시된 **`신뢰도 XX%` 배지** 확인
2. 답변 하단 출처 배지(예: `바이칼_취업규칙.pdf 78%`) **클릭**
3. 해당 청크 원문 팝업 확인

**강조 포인트**:
- 답변 근거를 직접 확인 가능 → 신뢰도 향상
- "AI가 어디서 가져온 내용인지" 투명하게 공개

---

### 🎬 Scene 3.5 — 답변 거절 / 할루시네이션 방어 ★ (2분)

**목적**: "AI가 모르는 건 모른다고 한다" — 신뢰도 게이트 시연

경쟁 제품(ChatGPT 등) 대비 **가장 강력한 차별점**입니다. 반드시 보여주세요.

1. 동일 채팅 세션에서 **문서에 없는 질문** 입력:

```
다음 분기 매출 예상치는 얼마인가요?
```

또는

```
오늘 점심 메뉴 추천해줘
```

2. 응답 확인:
   - 빨간 배지 **"답변 거절 · low_top1_score"** (또는 `low_confidence`, `no_chunks`)
   - 본문: _"업로드된 문서에서 충분한 근거를 찾지 못해 답변을 거절합니다..."_

3. **시스템 설정 → 최근 질의 로그**에서 거절 사유가 함께 기록된 것 확인 (감사 추적)

**스크립트 멘트 예시**:
> "ChatGPT는 모르는 것도 그럴듯하게 지어내지만(할루시네이션), BAIKAL은 **근거가 없으면 거절합니다.** 법무·인사·계약처럼 틀리면 책임이 따르는 영역에서 이 차이는 결정적입니다."

**강조 포인트**:
- 임계값: top1 유사도 0.45 미만 OR 신뢰도 0.40 미만 → 자동 거절
- 거절도 감사 로그에 남음 → 컴플라이언스 증빙
- `.env`로 임계값 조정 가능 (`MIN_CONFIDENCE_THRESHOLD`, `MIN_TOP1_SCORE`)

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
| "어떤 AI 모델을 쓰나요?" | 기본 qwen2.5:7b이지만 관리자 페이지에서 Ollama에 설치된 모델로 즉시 전환 가능합니다. OCR/이미지 처리는 qwen2.5vl:7b 비전 모델을 별도 사용합니다. |
| "HyDE가 뭔가요?" | AI가 질문에 대한 가상 답변 초안을 먼저 생성한 후 그 내용으로 문서를 검색하는 기법입니다. 추상적인 질문이나 복잡한 개념 질문에서 검색 품질을 높입니다. |
| "AI 답변을 믿을 수 있나요?" | 답변마다 신뢰도 점수와 출처 청크 원문을 표시합니다. 근거 부족 시 **답변을 거절**(빨간 배지)하므로 할루시네이션이 차단됩니다. |
| "사용 이력을 볼 수 있나요?" | 시스템 설정 페이지에서 질문 이력·신뢰도·응답시간·거절사유 감사 로그를 확인할 수 있습니다. |
| "법적 효력이 있나요?" | **없습니다.** 상단 면책 배너에도 명시되어 있습니다. BAIKAL은 문서 검색 보조 도구이며, 최종 판단은 담당자가 원문을 확인해야 합니다. |
| "폐쇄망 이전은 어떻게 하나요?" | `scripts/export-images.ps1`로 Docker 이미지·모델·설정 일체를 tar로 묶고, 폐쇄망에서 `import-images.sh`로 복원합니다. |

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


---

# 遺濡?A. ?곸꽭 ?쒖뿰 媛?대뱶

> 2026-04-29 ?듯빀. ?먮낯: DEMO_GUIDE.md, DEMO_PACKAGE.md

## 遺濡?A-1. ?쒖뿰 媛?대뱶 (援?DEMO_GUIDE)
## BAIKAL Private AI — 데모 가이드

> **대상**: 고객사 방문 데모 / 내부 시연  
> **환경**: Windows 10/11 + Docker Desktop (CPU 모드)  
> **소요 시간**: 최초 설정 15분 / 이후 데모 당일 3분
> **최종 업데이트**: 2026-04-07

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
## Ollama 컨테이너 먼저 시작
docker compose -f docker-compose.cpu.yml up -d ollama

## LLM 모델 (4.7 GB)
docker exec baikal-ollama ollama pull qwen2.5:7b

## 임베딩 모델 (1.2 GB)
docker exec baikal-ollama ollama pull bge-m3

## 확인
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
## Ollama 재시작
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
## PID 확인 후 해당 프로세스 종료
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


---

## 遺濡?A-2. ?쒖뿰 ?⑦궎吏 援ъ꽦 (援?DEMO_PACKAGE)

## BAIKAL Private AI — 업종별 시연 패키지

> **목적**: 고객사 미팅/PoC 시 "이 문서를 BAIKAL에 넣으면 이런 질문에 이렇게 답한다"를 보여주는 가이드  
> **구성**: 4개 업종 × 문서셋 + 시연 질문 + 기대 답변 예시

---

## 📦 사전 준비 사항

### 시연에 필요한 파일

`demo_docs/` 폴더에 있는 파일 또는 아래 스크립트로 생성:

```powershell
cd C:\baikal777\baikal-private-ai
python scripts/create_demo_docs.py
```

| 파일명 | 형식 | 내용 |
|--------|------|------|
| 바이칼_취업규칙.pdf | PDF | 근무시간, 연차, 급여, 경조사 |
| 바이칼_매출현황.xlsx | XLSX | 월별 매출 데이터 |
| 바이칼_사업제안서.docx | DOCX | 사업 개요, 기술 설명 |
| 폐쇄형 RAG BAIKAL Private AI.hwpx | HWPX | 제품 소개 한글 문서 |

---

## 🏛️ 시연 패키지 1 — 공공기관 (행정 내규 검색)

> **타깃**: 지자체 담당자, 행정직 공무원  
> **핵심 메시지**: "내규집·조례를 HWP 그대로 넣으면 담당자 없이도 즉시 답변"

### 추천 문서 구성

| 문서 | 형식 | 효과 |
|------|------|------|
| 행정 업무 규정집 | HWP/HWPX | HWP 직접 처리 능력 시연 |
| 지자체 조례 모음 | PDF | 법령·조례 검색 정확도 |
| 출장비 지급 기준표 | XLSX | 숫자 데이터 정확도 |

### 시연 질문 세트

| 순서 | 질문 | 기대 답변 핵심 |
|------|------|----------------|
| 1 | "직원 출장비는 어떻게 지급되나요?" | 교통비·숙박비·일비 기준 금액 |
| 2 | "연차 휴가를 며칠이나 쓸 수 있나요?" | 근속연수별 일수 (15일~25일) |
| 3 | "그러면 3년차 직원은 몇 일인가요?" | *(후속 질문 — 맥락 유지 시연)* |
| 4 | "경조사 휴가는 어떤 경우에 며칠인가요?" | 결혼·출산·사망별 세부 일수 |
| 5 | "외부 AI 서비스(ChatGPT) 사용이 허용되나요?" | 사내 보안 규정 답변 |

### 강조 포인트

- **질문 3번**: 이전 대화 맥락을 이어서 답변 → "기억력" 시연
- **출처 배지 클릭**: 어느 조문에서 가져왔는지 원문 확인 가능
- 외부 AI는 불가하지만 BAIKAL은 내부에서만 동작한다는 차별점

---

## 🏭 시연 패키지 2 — 제조/유통 (매출·재고 데이터 검색)

> **타깃**: 영업팀 관리자, 경영기획팀  
> **핵심 메시지**: "엑셀 파일을 AI가 읽어서 말로 답한다"

### 추천 문서 구성

| 문서 | 형식 | 효과 |
|------|------|------|
| 월별 매출 현황 | XLSX | 표 데이터 수치 정확도 |
| 제품별 단가표 | XLSX | 복잡한 표 구조 처리 |
| 영업 보고서 | DOCX/PDF | 정성 분석 내용 |

### 시연 질문 세트

| 순서 | 질문 | 기대 답변 핵심 |
|------|------|----------------|
| 1 | "2025년 연간 총 매출은 얼마인가요?" | 합계 수치 |
| 2 | "월별로 정리해서 알려주세요" | 표 형식 12개월 정리 |
| 3 | "가장 매출이 높은 달은 언제고, 이유는?" | 분석 + 추론 답변 시연 |
| 4 | "솔루션 부문과 SI 부문 중 어느 쪽이 더 높나요?" | 비교 분석 |
| 5 | "4분기 매출 합계와 비중을 계산해줘" | 계산·비율 처리 |

### 강조 포인트

- **질문 2번**: 길고 복잡한 표를 말로 깔끔하게 정리 → "보고서 작성 시간 절감"
- **질문 3번**: 단순 검색이 아닌 분석·추론 능력 시연
- 엑셀을 열어서 직접 찾는 것 vs BAIKAL에 물어보는 것 직접 비교

---

## ⚖️ 시연 패키지 3 — 법무/컴플라이언스 (계약·규정 검색)

> **타깃**: 법무팀, 감사팀, 컴플라이언스 담당자  
> **핵심 메시지**: "계약서·내부 규정을 물어보면 조항 위치까지 알려준다"

### 추천 문서 구성

| 문서 | 형식 | 효과 |
|------|------|------|
| 표준 계약서 (NDA, 공급계약) | PDF/DOCX | 조항 참조 정확도 |
| 개인정보처리방침 | PDF | 법령 준수 문서 |
| 내부 감사 체크리스트 | DOCX | 체계적 문서 처리 |

### 시연 질문 세트

| 순서 | 질문 | 기대 답변 핵심 |
|------|------|----------------|
| 1 | "계약 해지 시 사전 통보 기간은 며칠인가요?" | 조항 번호 + 내용 |
| 2 | "손해배상 한도는 계약금액의 몇 %인가요?" | 수치 + 근거 조항 |
| 3 | "개인정보 보유 기간은 어떻게 되나요?" | 법정 보유 기간 |
| 4 | "비밀유지 의무 위반 시 어떤 조치가 취해지나요?" | 패널티 내용 |
| 5 | "이 계약서에서 을의 의무사항만 정리해줘" | 구조화된 요약 |

### 강조 포인트

- **출처 청크 팝업**: "정말 계약서 몇 조에 있는 내용인지" 원문 확인
- **신뢰도 배지**: 근거가 명확한 질문은 신뢰도 80% 이상 → 신뢰성 시연
- 여러 계약서 동시 업로드 → 문서 필터로 특정 계약서만 질의 가능

---

## 🏥 시연 패키지 4 — HR/총무 (인사 규정 검색)

> **타깃**: HR팀, 총무팀, 임직원 셀프서비스  
> **핵심 메시지**: "인사팀에 물어보는 대신 AI에게 직접 물어본다"

### 추천 문서 구성

| 문서 | 형식 | 효과 |
|------|------|------|
| 취업규칙 / 인사 규정 | PDF/HWP | 규정 기반 정확한 답변 |
| 복리후생 가이드 | DOCX | 직원 혜택 문의 대응 |
| 임직원 행동강령 | PDF | 윤리·보안 규정 |

### 시연 질문 세트

| 순서 | 질문 | 기대 답변 핵심 |
|------|------|----------------|
| 1 | "신입사원 수습 기간은 얼마나 되나요?" | 기간 + 평가 방식 |
| 2 | "자기개발비는 연간 얼마까지 지원되나요?" | 금액 + 사용 조건 |
| 3 | "재택근무 신청은 어떻게 하나요?" | 절차·조건 |
| 4 | "아이 학교 입학식 때 반차 쓸 수 있나요?" | 경조사/반차 규정 |
| 5 | "ChatGPT 같은 외부 AI 사용이 금지인가요?" | 보안 규정 답변 |

### 강조 포인트

- **HyDE 모드 시연**: 질문 4번처럼 직접 조문에 없는 질문 → HyDE ON/OFF 비교
- 인사팀이 받는 반복 문의의 70%를 AI가 대신 처리 가능
- 24/7 언제든지 임직원이 직접 조회 가능

---

## 🎯 공통 시연 포인트 (모든 패키지)

### 반드시 보여줄 기능 3가지

1. **스트리밍 응답** — 글자가 실시간으로 타이핑되는 것을 보여줌
2. **출처 배지 클릭** — 답변 근거 원문 팝업 → "AI가 지어낸 것이 아님" 증명
3. **네트워크 탭 확인** (F12) — 외부 요청 없음 → 폐쇄망 증명

### 분위기에 따른 추가 시연

| 관심 포인트 | 시연 방법 |
|------------|----------|
| 보안 걱정 | 개발자 도구 Network 탭 → localhost 외 요청 없음 |
| 여러 명이 써야 함 | 사용자 관리 → 역할별 계정 생성 시연 |
| 문서 접근 제어 필요 | 문서 관리 → 방패 버튼 → 역할별 권한 설정 |
| "ChatGPT랑 뭐가 달라요?" | 문서 없이 질문 → "문서를 찾을 수 없습니다" → 문서 업로드 후 재질문 |
| 도입 비용 문의 | `docs/roi_calculator.html` 을 브라우저로 열어서 현황 입력 후 ROI 계산 |

---

## 📝 미팅 후 남겨줄 자료 체크리스트

- [ ] `docs/roi_calculator.html` — ROI 계산기 (브라우저에서 바로 실행)
- [ ] `docs/INSTALL_GUIDE_EASY.md` — 비개발자 설치 가이드
- [ ] `docs/DEMO_RUNBOOK.md` — 상세 시연 스크립트
- [ ] 시연 중 실제 답변 스크린샷 (가능하면 고객 문서로 시연)

---

*이 패키지는 고객사 업종에 맞는 시나리오를 선택해서 사용하세요.  
실제 고객 문서로 시연할수록 구매 전환율이 높아집니다.*
