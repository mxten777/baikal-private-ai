# BAIKAL 媛쒕컻 ?명듃 (?대???

> **理쒖쥌 ?듯빀蹂?* 쨌 2026-04-29
> 蹂?臾몄꽌???ㅼ쓬 3媛?媛쒕컻 ?대? 臾몄꽌瑜??듯빀???먮즺?낅땲??
> - IMPROVEMENT_ROADMAP.md ??媛쒖꽑 濡쒕뱶留?
> - RAG_IMPROVEMENT.md ??RAG ?뚯씠?꾨씪??媛쒖꽑 ?대젰
> - ANALYSIS.md ???쒖뒪??遺꾩꽍

---

## 紐⑹감

- [Part 1. 媛쒖꽑 濡쒕뱶留?(#part-1-媛쒖꽑-濡쒕뱶留?
- [Part 2. RAG ?뚯씠?꾨씪??媛쒖꽑 ?대젰](#part-2-rag-?뚯씠?꾨씪??媛쒖꽑-?대젰)
- [Part 3. ?쒖뒪??遺꾩꽍](#part-3-?쒖뒪??遺꾩꽍)

---

# Part 1. 媛쒖꽑 濡쒕뱶留?
## BAIKAL 프로젝트 실질 개선 방향

> **작성일**: 2026-04-29
> **근거 문서**: [VERTICAL_MARKETING_ANALYSIS.md](VERTICAL_MARKETING_ANALYSIS.md)
> **목적**: 냉정 분석에서 도출된 약점 3가지(할루시네이션 리스크 / 영업 전제 오류 / 첫 고객 부재)를 **제품·코드·문서 레벨에서 어떻게 메울 것인가** 를 행동 단위로 정리

이 문서는 마케팅 전략 문서가 아니다. **개발자 한 명이 즉시 착수할 수 있는 코드/콘텐츠 작업 목록**이다.

---

## 진행 현황 (2026-04-29 갱신)

| 항목 | 상태 | 산출물 |
|------|:----:|--------|
| Confidence Gate (P0) | ✅ 완료 | `backend/app/services/rag_service.py`, `backend/app/config.py` |
| 거절 응답 UI (P0) | ✅ 완료 | `frontend/src/components/ChatMessage.jsx` 빨간 배지 |
| 채팅 disclaimer 배너 (P0) | ✅ 완료 | `frontend/src/pages/ChatPage.jsx` 상단 고정 |
| eval_rag.py `--output md` (P0) | ✅ 완료 | `scripts/eval_rag.py`, `docs/TEST_RESULTS.md` 자동 생성 |
| 자가 보안 점검 (P1) | ✅ 완료 | `scripts/security_audit.py`, `docs/SECURITY_AUDIT.md` |
| PowerShell 오프라인 패키지 (P1) | ✅ 완료 | `scripts/export-images.ps1`, `scripts/export-models.ps1` |
| 법령 데모 패키지 (P1) | ✅ 완료 | `demo_docs/law/` (README, 질문지, 시나리오, 정답표) |
| 백엔드 테스트 | ✅ 38/38 | `backend/tests/` |

남은 작업: 실제 시연 대상 지자체 조례 다운로드 → 색인 → `eval_rag.py` 실측 → `docs/TEST_RESULTS.md` 갱신.

---

## 0. 우선순위 한 줄 요약

| 순위 | 영역 | 목적 | 주력 파일 |
|------|------|------|-----------|
| 🔴 P0 | **법령 버티컬 정합성** | "검색"과 "검토"의 혼동 차단, 출처 강제 표시 | `backend/app/services/rag_service.py`, `frontend/src/components` |
| 🔴 P0 | **eval_rag.py 결과 공개 가능화** | 숫자 기반 신뢰 자료 — 제안서 1페이지에 들어갈 표 | `scripts/eval_rag.py`, `scripts/eval_testset.json`, `docs/TEST_RESULTS.md` |
| 🟠 P1 | **법령 데모 패키지** | 공공 PoC 진입용 시연 문서셋·질문지 | `demo_docs/`, `docs/DEMO_PACKAGE.md` |
| 🟠 P1 | **할루시네이션 가드** | 신뢰도 임계 미달 시 "답변 거절" 명시 | `backend/app/services/guardrail_service.py`, `rag_service.py` |
| 🟡 P2 | **비교 콘텐츠 / ROI 자료** | 인바운드 채널 구축 | `docs/`, `docs/roi_calculator.html` |

---

## 1. 분석 문서가 지적한 3대 약점 — 제품으로 어떻게 답할 것인가

### 1-1. "할루시네이션 리스크" — 제품 안전장치로 해소

분석 문서 §3-1은 *"법무팀이 검색을 검토로 사용할 가능성"* 을 지적한다. 이 리스크를 **마케팅 카피가 아니라 코드로** 막아야 한다.

#### 즉시 작업 항목

1. **신뢰도 임계 게이트 (Confidence Gate)**
   - 위치: `backend/app/services/rag_service.py`
   - 정책: 최상위 청크 score < `MIN_CONFIDENCE_THRESHOLD` (예: 0.45) 이면 LLM 호출 전에 다음 응답 강제 반환
     > *"관련도가 낮아 답변하지 않습니다. 질문을 구체화하거나 관련 문서가 색인되어 있는지 확인하세요."*
   - 환경 변수로 외부화: `MIN_CONFIDENCE_THRESHOLD`, `MIN_TOP1_SCORE` (`backend/app/config.py`)

2. **출처 미부착 응답 차단**
   - 모든 답변은 인용 청크 1개 이상을 포함해야 한다. LLM이 청크 없이 생성한 경우 응답 폐기.
   - `llm_service.py` 후처리에서 `[citation]` 토큰 또는 `chunk_id` 매핑이 0개면 거절.

3. **"검색 결과" vs "AI 답변" UI 분리**
   - 프론트엔드 채팅 화면 상단에 고정 배지: **"BAIKAL은 문서 검색 보조 도구입니다. 법적·계약상 효력 판단의 근거가 아닙니다."**
   - 모든 답변 카드 하단에 출처 칩 강제 노출 (이미 있으면 disclaimer 강화).

4. **로그 남기기 — 책임 추적**
   - `query_logs`에 다음 필드 보강 (이미 있으면 활용):
     - `top1_score`, `confidence`, `refusal_reason`, `cited_chunk_ids`
   - 마이그레이션 0003에 KPI 필드가 이미 있다. 누락 필드만 추가하면 됨.

> 효과: 분석 문서 §3-1의 "법적 오류 발생 시 책임 구조 불명확" 을 *"제품이 자체적으로 판단을 회피한다"* 는 영업 메시지로 역전.

---

### 1-2. "영업 사이클 낙관" — 진입 장벽을 코드로 낮춘다

분석 문서 §3-2는 *대기업 IT 보안 검토 6~9개월* 을 경고한다. 이 시간을 **단축할 수 없다면 평가 비용이라도 0에 가깝게** 만들어야 한다.

#### 즉시 작업 항목

1. **오프라인 설치 패키지 검증 자동화**
   - `scripts/export-images.sh`, `scripts/import-images.sh`, `scripts/export-models.sh` 가 이미 있다.
   - 추가 작업: PowerShell 버전(`scripts/export-images.ps1`)과 SHA256 체크섬 산출 스크립트.
   - 산출물: USB 단일 폴더 — `images.tar`, `models.tar`, `docker-compose.cpu.yml`, `INSTALL_GUIDE_EASY.md`, `verify.ps1`.

2. **보안 자가 점검 리포트 (Self-Audit)**
   - 새 스크립트: `scripts/security_audit.py`
   - 점검 항목 (모두 자동):
     - 외부 도메인 호출 0건 (네트워크 인터셉트 결과)
     - 기본 비밀번호 변경 여부
     - `.env`의 `SECRET_KEY` 길이
     - HTTPS/CORS 설정
     - 의존 패키지 CVE 스캔 (`pip-audit`)
   - 출력: `audit_report_YYYYMMDD.json` + 마크다운. **PoC 시 IT 보안팀에 그대로 제출**.

3. **개인정보 마스킹 사전 점검 모드**
   - `backend/app/rag/loader.py` 인덱싱 시 옵션으로 PII 검출 (주민번호, 계좌, 이메일 패턴) 후 통계만 산출.
   - 결과를 관리자 화면에서 *"색인된 문서 X건 중 PII 의심 N건"* 으로 노출.
   - 보안팀 검토 시간 단축 — 직접 보고서 작성하지 않아도 됨.

---

### 1-3. "첫 고객 확보 경로 부재" — 콘텐츠 자산을 코드와 같은 속도로 만든다

분석 문서 §3-3은 *레퍼런스 부재의 데드락* 을 지적한다. 콘텐츠는 마케팅이 아니라 **개발자가 직접 산출 가능한 형태**로 정의한다.

#### 즉시 작업 항목 (모두 산출물 = 마크다운/HTML/스크립트)

1. **법령 데모 패키지 (`demo_docs/law/`)**
   - 공개 법령 HWP 5건 (자치법규시스템 ELIS에서 다운로드 가능 — 저작권 제약 없음)
   - 동봉 파일:
     - `질문지_20개.md` — 검증 가능한 정답 매핑 (조항/페이지)
     - `예상답변_정답표.md` — 평가용
     - `시연_시나리오.md` — 5분 시연 스크립트
   - 동시에 `scripts/eval_testset.json` 에 법령 도메인 케이스 추가

2. **벤치마크 결과표 자동 생성**
   - `scripts/eval_rag.py` 실행 결과를 마크다운 표로 출력하는 옵션 추가 (`--output md`)
   - 산출물: `docs/TEST_RESULTS.md` 자동 갱신
   - 제안서 1페이지에 그대로 복사 가능한 형태

3. **비교 시연 페이지 (정적 HTML)**
   - `docs/comparison_demo.html` (이미 있는 `roi_calculator.html` 형식 모방)
   - 좌: ChatGPT 스크린샷 (HWP 업로드 실패) / 우: BAIKAL 응답
   - 분석 문서 §7-2의 4줄 비교표를 그대로 시각화

---

## 2. 코드 레벨 변경 체크리스트

### 2-1. 백엔드

| 파일 | 변경 내용 | 우선순위 |
|------|-----------|----------|
| `backend/app/config.py` | `MIN_CONFIDENCE_THRESHOLD`, `MIN_TOP1_SCORE`, `REQUIRE_CITATION` 환경 변수 추가 | P0 |
| `backend/app/services/rag_service.py` | confidence gate, 출처 강제, 거절 응답 분기 | P0 |
| `backend/app/services/guardrail_service.py` | 거절 사유 분류 (`low_confidence`, `no_citation`, `pii_detected`) | P0 |
| `backend/app/services/llm_service.py` | 인용 토큰 후처리, 미부착 시 폐기 | P0 |
| `backend/app/api/admin.py` | query_log 신규 필드 노출 (top1_score, refusal_reason) | P1 |
| `backend/app/rag/loader.py` | 인덱싱 시 PII 통계 옵션 | P1 |

### 2-2. 프론트엔드

| 파일 | 변경 내용 | 우선순위 |
|------|-----------|----------|
| `frontend/src/components` (채팅) | 상단 고정 disclaimer, 거절 응답 전용 카드 UI | P0 |
| `frontend/src/components` (검색) | top1_score 시각화 (낮을 때 경고색) | P1 |
| `frontend/src/pages` (관리자) | refusal_reason 통계 대시보드 | P1 |

### 2-3. 스크립트 / 평가

| 파일 | 변경 내용 | 우선순위 |
|------|-----------|----------|
| `scripts/eval_rag.py` | `--output md` 옵션, 모드별(hybrid/vector/keyword) 비교 표 출력 | P0 |
| `scripts/eval_testset.json` | 법령 도메인 케이스 10건 추가 | P0 |
| `scripts/security_audit.py` | (신규) 자가 점검 리포트 생성 | P1 |
| `scripts/export-images.ps1` | (신규) Windows 환경 오프라인 패키징 | P1 |

### 2-4. 문서

| 파일 | 변경 내용 | 우선순위 |
|------|-----------|----------|
| `docs/TEST_RESULTS.md` | eval_rag.py 결과 자동 갱신 — 숫자 표 1페이지 | P0 |
| `docs/DEMO_PACKAGE.md` | 법령 버티컬 시나리오 추가 | P1 |
| `docs/comparison_demo.html` | (신규) 비교 시연 정적 페이지 | P1 |
| `docs/INSTALL_GUIDE_EASY.md` | 자가 점검 리포트 사용법 추가 | P1 |

---

## 3. 의도적으로 *하지 않는* 일

분석 문서 §5는 "기술이 아니라 영업이 병목"이라고 결론짓는다. 따라서 다음은 **지금 시점에서 하지 않는다**.

- 새 LLM 모델 교체/파인튜닝 — qwen2.5:7b 로컬 모델로 충분, 검증 가능성이 더 중요
- 새 청크 전략 실험 — 현재 청크 파이프라인 동작 중, 깊은 튜닝은 PoC 후 데이터로 결정
- 새 UI 페이지 추가 — disclaimer/거절 응답 외 신규 화면 추가 금지
- 멀티 테넌트 / SaaS 청구 — 폐쇄망 단일 설치 모델에 집중

> 분석 문서 §3의 약점 3가지에 직접 대응하지 않는 작업은 모두 후순위.

---

## 4. 한 줄 결론

> **법령 버티컬 1순위 + 할루시네이션 가드 + 숫자 기반 자료 — 이 셋을 코드로 구현한 뒤에야 영업이 의미를 갖는다.**

P0 항목(confidence gate, citation 강제, eval_rag 결과 표, 법령 데모셋)을 먼저 끝내는 것이 다른 어떤 마케팅 활동보다 선행한다.

---

*이 문서는 docs/VERTICAL_MARKETING_ANALYSIS.md 의 분석 결론을 제품 작업 항목으로 매핑한 실행 문서입니다.*


---

# Part 2. RAG ?뚯씠?꾨씪??媛쒖꽑 ?대젰

## BAIKAL Private AI — RAG 품질 개선 로드맵

> 마지막 업데이트: 2026-04-07 (최신 커밋: logo-update, 기능 완료: Cross-encoder·OCR·시맨틱청킹·3단계권한·신뢰도·감사로그)

---

## 1. 상용 RAG 제품 비교

| 기능 영역 | Dify | LlamaIndex | Cohere RAG | **BAIKAL (현재)** |
|---|---|---|---|---|
| 배포 형태 | 자체호스팅 가능 | 라이브러리 | 클라우드 전용 | ✅ 완전 폐쇄망 |
| 청킹 | 고급(시맨틱/구조인식) | 고급(노드파서) | N/A | ✅ 시맨틱청킹 + 표헤더반복 + OCR폴백 |
| 검색 방식 | 벡터+전문검색 | 벡터+BM25+다양 | 벡터+rerank | ✅ 벡터+BM25+MMR |
| Reranking | Cross-encoder | Cross-encoder | Cohere Rerank | ✅ Cross-encoder + MMR |
| 이미지 PDF(OCR) | ✅ | 플러그인 | 제한적 | ✅ Tesseract 5 (kor+eng) |
| 지원 파일 형식 | 10종+ | 플러그인 무제한 | 제한적 | ✅ PDF/DOCX/XLSX/HWP/HWPX |
| 멀티유저 | ✅ | ❌(라이브러리) | ✅ | ✅ |
| 권한 관리 | 팀/워크스페이스 | ❌ | 팀 | ✅ admin/manager/user 3단계 + 문서별 접근제어 |
| UI | ✅ 풀 노코드 | ❌ 코드만 | API만 | ✅ React 대화형 |
| LLM 교체 | ✅ 다수 지원 | ✅ 다수 지원 | Cohere 전용 | ✅ Ollama 모델 런타임 전환 |
| 스트리밍 | ✅ | ✅ | ✅ | ✅ |
| 신뢰도/감사로그 | ✅ | 부분 | 제한적 | ✅ sigmoid 신뢰도 + QueryLog DB |
| 한글 문서(HWP) | 부분 | 부분 | 제한적 | ✅ HWP/HWPX 네이티브 |
| 인터넷 불필요 | 자체호스팅 시 가능 | ✅ | ❌ | ✅ 완전 격리 |

### 현재 수준 평가 (2026-04-06 기준)
- **Dify v0.6 수준** (Cross-encoder, OCR, 시맨틱청킹, 3단계 권한 모두 구현 완료)
- **강점:** 완전 폐쇄망 + HWP 네이티브 + 원클릭 설치 + 신뢰도 투명성 → 국내 기업 환경 특화
- **잔여 격차:** 멀티모달 이미지 이해(차트·도표 내용 추출), HyDE 검색 정확도 향상

---

## 2. 개선 체크리스트

### 🟢 완료

#### 안정성 / 버그 수정
- [x] **업로드 후 백그라운드 태스크 소멸 문제** `af71a09` (2026-04-06)
  - 서버 재시작 시 `processing` 상태 문서 → `failed` 자동 복구
  - DB 예외 발생 시 rollback 후 재조회하여 상태 업데이트
  - null 바이트(`\x00`, `\uf000`) 제거 → PostgreSQL UTF-8 거부 방지
- [x] **stuck 문서 UI 표시 및 삭제 기능** `af71a09` (2026-04-06)
  - 5분 이상 처리 중이면 "응답없음" 배지 표시
  - failed / stuck 문서에 삭제 버튼 추가

#### 검색 품질
- [x] **유사도 임계값 상향** `c0c5b0a` (2026-04-06)
  - `SIMILARITY_THRESHOLD` 0.3 → 0.50
  - MMR 후 hybrid score 0.45 미만 청크 최종 제거
- [x] **비관련 청크 무시 시스템 프롬프트** `c0c5b0a` (2026-04-06)
  - 질문과 직접 관련 없는 참고 문서 내용 무시 지시 추가

#### 파일 처리
- [x] **PyPDF2 → pdfplumber 교체** `18e6775` (2026-04-06)
  - 표 구조 인식, 셀 단위 추출
  - 표/일반텍스트 영역 분리 추출

#### 컨텍스트 품질
- [x] **num_ctx 4096 → 8192** `4960c49` (2026-04-06)
  - 청크 5개 + 히스토리 + 시스템 프롬프트 합산 시 토큰 잘림 방지
- [x] **표 헤더 반복 청킹** `4960c49` (2026-04-06)
  - 탭 구분 행 자동 감지, 각 청크마다 컬럼 헤더 포함
  - 청크 경계에서 이름 없는 숫자만 남는 문제 해결
- [x] **히스토리 turns 5 → 3** `4960c49` (2026-04-06)
  - 다른 주제 이전 대화의 컨텍스트 오염 범위 축소

---

### 🟡 단기 개선 (코드 수정 수준)

- [x] **Cross-encoder Reranking 추가** `045a8bd` (2026-04-06)
  - 모델: `cross-encoder/ms-marco-MiniLM-L-6-v2` (Docker 이미지에 포함, 폐쇄망 지원)
  - 파이프라인: 벡터+BM25 → MMR → **Cross-encoder 정밀 재정렬** → top-K
  - Cross-encoder 실패 시 hybrid_score 순으로 자동 fallback
  - `@lru_cache` 싱글턴으로 모델 1회만 로드

- [x] **문서별 채팅 필터** `e9f9055` (2026-04-06)
  - 특정 문서만 대상으로 질문하는 기능
  - 검색 쿼리에 `document_id` 필터 파라미터 추가
  - UI: 채팅 입력창 왼쪽 퍼널 버튼 → 문서 멀티셀렉트 패널

- [x] **청크 원문 미리보기** `e9f9055` (2026-04-06)
  - 답변 출처 배지 클릭 시 해당 청크 내용 팝업 표시
  - 관련도 점수 함께 표시, 사용자 신뢰도 향상

- [x] **신뢰도 점수 표시** `e9f9055` (2026-04-06)
  - 검색된 청크 점수 평균 → 답변 헤더에 `신뢰도 XX%` 배지

- [x] **감사 로그 (QueryLog)** `e9f9055` (2026-04-06)
  - 질문마다 DB에 저장: 사용자, 쿼리, 응답요약, 신뢰도, 지연시간

- [x] **임베딩 비대칭 완화 (표 NL 변환)** `e9f9055` (2026-04-06)
  - 청크 저장 시 표 데이터를 자연어로 변환(`table_chunk_to_nl`) 후 임베딩
  - 예: `"이름\t금액\n홍길동\t5000"` → `"이 행은 이름이 홍길동이고 금액이 5000입니다."`

---

### 🔵 중기 개선 (설계 변경 필요)

- [x] **이미지 PDF 지원 (OCR)** (2026-04-06)
  - 엔진: Tesseract 5.5 + pytesseract + pdf2image (Docker 이미지에 포함)
  - 언어: 한국어(kor) + 영어(eng) 동시 인식
  - 동작: pdfplumber 추출 텍스트가 페이지당 30자 미만이면 OCR 자동 폴백
  - 스캔 문서, 이미지 삽입 PDF 모두 처리 가능, 기존 텍스트 PDF는 영향 없음

- [x] **시맨틱 청킹** (2026-04-06)
  - 단락 임베딩 유사도(bge-m3) 기반 의미 경계 탐지, `similarity_threshold=0.75`
  - 표 영역은 기존 헤더반복 방식 유지, 일반 텍스트만 시맨틱 청킹 적용
  - 시맨틱 청킹 실패 시 문자 기반 슬라이딩 윈도우로 자동 폴백
  - `split_into_paragraphs()` + `semantic_chunk_with_embeddings()` → `chunker.py`

- [x] **권한 단계 확장**
  - admin / manager / user 3단계, 문서별 is_public + allowed_roles 접근 제어 UI (d643653)

- [x] **LLM 모델 UI 전환**
  - /admin/settings 페이지: Ollama 모델 목록 조회 + 런타임 활성화, 쿼리 감사 로그 (d643653)

- [ ] **멀티모달 (이미지 이해)**
  - 이미지 포함 문서에서 차트/도표 내용 추출
  - LLaVA 또는 qwen2.5-vl 모델 연동

---

### 🔴 장기 / 보류

- [ ] **HyDE (가상 문서 임베딩)**
  - 질문 → LLM으로 가상 답변 생성 → 그 답변으로 임베딩 검색
  - 검색 정확도 대폭 향상 가능
  - 단점: LLM 2회 호출로 응답 시간 2배 증가 → 데모/실시간 환경 부적합
  - 조건: 응답속도보다 정확도가 중요한 배치 분석용으로 별도 모드 구현 시 검토

---

## 3. 성능 기준선 (2026-04-06 측정)

| 항목 | 값 |
|---|---|
| PDF 처리 속도 (213KB, 16청크) | ~13초 |
| 임베딩 모델 | bge-m3 (1.2GB) |
| LLM 모델 | qwen2.5:7b (4.7GB) |
| 청크 크기 | 500자 / overlap 50자 (폴백 기준) |
| 유사도 임계값 | 0.50 (검색), 0.75 (시맨틱 청킹 경계) |
| Top-K | 5 |
| num_ctx | 8192 |
| 청크 수 변화 | 181개 (고정분할) → 423개 (시맨틱청킹, 11개 문서 기준) |


---

# Part 3. ?쒖뒪??遺꾩꽍

## BAIKAL Private AI — 완성도 분석 및 상용화 개선 과제

> 분석 기준일: 2026-04-03  
> 최종 수정일: 2026-04-07 (2차 개선 완료 — RAG 품질 강화·로고)

---

## 전체 평가

| 항목 | 초기 | 1차 개선 후 | **2차 개선 후** |
|------|------|-------------|----------------|
| 기능 완성도 | 70% | 80% | **92%** |
| 상용화 준비도 | 30% | 65% | **82%** |

핵심 RAG 파이프라인(업로드→청킹→임베딩→검색→LLM 스트리밍)은 실제로 작동하는 완성된 구현체입니다.  
1차 개선에서 보안 치명 항목 전체 + 운영 안정성 항목 전체 + 주요 품질 이슈를 해결했습니다.  
2차 개선에서 Cross-encoder Reranking·시맨틱 청킹·OCR·3단계 RBAC·신뢰도·감사 로그 등 RAG 품질 전반을 강화했습니다.

---

## 🔴 즉시 수정 필수 (보안 치명적)

| # | 문제 | 위치 | 상태 |
|---|------|------|------|
| 1 | **CORS 와일드카드 + credentials=True 동시 설정** — 브라우저 스펙상 무효, 크로스 오리진 인증 파괴 | `backend/app/main.py` | ✅ 완료 |
| 2 | **하드코딩된 JWT 시크릿 키** — `.env` 없이 배포 시 알려진 키로 토큰 위조 가능 | `backend/app/config.py` | ✅ 완료 |
| 3 | **기본 관리자 비밀번호 `admin1234`** — `.env` 미설정 시 그대로 노출 | `backend/app/config.py` | ✅ 완료 |
| 4 | **PostgreSQL 포트 5432, Ollama 포트 11434 외부 노출** — 호스트/로컬 네트워크에서 인증 없이 직접 접근 가능 | `docker-compose.yml` | ✅ 완료 |
| 5 | **문서 다운로드 소유권 검사 없음** — 모든 인증된 사용자가 타인의 문서 ID로 다운로드 가능 | `backend/app/api/documents.py` | ✅ 완료 |
| 6 | **로그인 엔드포인트 Rate Limit 없음** — Brute-force 공격 무방비 | `backend/app/api/auth.py` | ✅ 완료 |

### 적용 내용 요약
- **#1** `allow_credentials=False`로 변경 — JWT는 Authorization 헤더 사용, 쿠키 불필요
- **#2 #3** `APP_ENV=production` 시 기본 `SECRET_KEY` / 취약 비밀번호 사용하면 **서버 기동 자체 차단** (`@model_validator`)
- **#4** `postgres:5432`, `ollama:11434` 외부 포트 매핑 제거 — Docker 내부 네트워크로만 접근
- **#5** 다운로드 API에 소유자 검사 추가 — 타인 문서 접근 시 403 반환
- **#6** `slowapi` 기반 로그인 **분당 5회** 제한 추가

---

## 🔴 첫 사용자 투입 전 수정 필수 (기능 버그)

| # | 문제 | 위치 | 상태 |
|---|------|------|------|
| 7 | **`DELETE /api/chat/sessions/{id}` 엔드포인트 없음** — 항상 404 | `backend/app/api/chat.py` | ✅ 확인 (기존 구현됨) |
| 8 | **설치 스크립트가 `llama3`를 받지만 서버는 `qwen2.5:7b` 기대** — 신규 설치 시 LLM 완전 불작동 | `scripts/setup.sh`, `scripts/setup.ps1` | ✅ 완료 |

### 적용 내용 요약
- **#7** 분석 오탐 — `chat.py` 하단에 이미 구현되어 있었음
- **#8** `llama3` → `qwen2.5:7b` 수정. `sleep 30` 고정 대기 → **Ollama 실제 응답 확인 폴링 루프**로 교체 (최대 150초, 실패 시 명확한 오류)

---

## 🟠 프로덕션 배포 전 수정 (운영 안정성)

| # | 문제 | 상태 |
|---|------|------|
| 9 | **단일 uvicorn 워커** — LLM 요청 하나가 모든 API 블로킹 | ✅ 완료 |
| 10 | **Alembic 마이그레이션 디렉토리 없음** — DB 스키마 변경 시 데이터 손실 위험 | ✅ 완료 |
| 11 | **백그라운드 문서처리 중 서버 재시작 시 복구 불가** — `processing` 상태로 영구 고착 | ✅ 완료 |
| 12 | **HTTPS 없음** — nginx가 80포트 HTTP만 처리 | ✅ 완료 (준비) |
| 13 | **비밀번호 최소 길이 4자** — 상용 기준에 턱없이 부족 | ✅ 완료 |

### 적용 내용 요약
- **#9** `Dockerfile` — `--workers 4` 추가 (LLM 응답 중에도 다른 API 정상 처리)
- **#10** `alembic/` 디렉토리, `alembic.ini`, `env.py`, `0001_initial.py` 생성. 서버 시작 시 `alembic upgrade head` 자동 실행
- **#11** lifespan에 watchdog 추가 — 재시작 시 `processing`/`uploading` 고착 문서 자동 `failed` 처리 후 로그 기록
- **#12** Nginx 보안 헤더 5종 즉시 적용 (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `CSP`). SSL 전환 가이드 주석 포함. SSE `proxy_buffering off`, `proxy_read_timeout` 600s
- **#13** Pydantic `@field_validator`로 8자 이상 정책 통일 — 사용자 생성/수정/비밀번호 변경 전체 적용

---

## 🟡 단기 개선 필요 (품질/보완)

| # | 문제 | 상태 |
|---|------|------|
| 14 | **JWT 토큰 `localStorage` 저장** — XSS 공격 시 토큰 탈취 가능 | ⬜ 미완 (장기 검토) |
| 15 | **SSE 스트리밍이 Axios 인터셉터 우회** — 토큰 만료 시 스트리밍 중 갱신 불가 | ✅ 완료 |
| 16 | **BM25 IDF가 상수** — `math.log(2)` 고정값으로 단어 희귀도 미반영 | ✅ 완료 |
| 17 | **목록 API 페이지네이션 없음** — 대규모 데이터 시 전 건 반환 | ✅ 완료 |
| 18 | **`.gitignore` 불완전** — 빌드 산출물·업로드 파일 누락 패턴 | ✅ 완료 |
| 19 | **실제 사용자 파일이 git에 커밋됨** — `backend/backend/uploads/` 내 파일 5건 | ✅ 완료 |
| 20 | **CHUNK_SIZE 설정 불일치** — `config.py` 기본값 800자, `.env.example`은 500자 | ✅ 완료 |
| 21 | **Nginx 보안 헤더 없음** | ✅ 완료 (#12에서 처리) |

### 적용 내용 요약
- **#15** SSE `fetch` 호출에 401 발생 시 토큰 갱신 → 재시도 로직 추가. 갱신 실패 시 로그인 페이지 이동
- **#16** BM25 IDF를 Robertson IDF 공식으로 교체 (`_compute_idf` 함수 신규 추가) — 단어 희귀도가 하이브리드 검색 점수에 실제 반영
- **#17** 문서/사용자/세션 목록 API에 `?skip=0&limit=N` 페이지네이션 추가
- **#18 #19** `.gitignore`에 `backend/backend/`, `uploads/`, `*.log` 등 추가. 잘못 커밋된 업로드 파일 5건 git 추적 제거

> **#14 (localStorage)**: `HttpOnly` 쿠키로 이전 시 프론트엔드 전반 수정이 필요하므로 별도 스프린트로 분리.

---

## 🟢 장기 로드맵 (경쟁력 강화)

| # | 항목 | 상태 |
|---|------|------|
| 22 | 테스트 코드 전무 (pytest, jest 등) | ⬜ 미완 |
| 23 | 토큰 폐기 메커니즘 없음 (탈취된 Refresh Token 무효화 불가) | ⬜ 미완 |
| 24 | 파일 중복 업로드 감지 없음 | ⬜ 미완 |
| 25 | 감사 로그(Audit Log) 없음 | ✅ 완료 (2026-04-06) |
| 26 | 검색 UI에서 검색 모드(키워드/벡터/하이브리드) 선택 미노출 | ✅ 완료 (2026-04-03) |

---

## 🔵 2차 개선 (RAG 품질 강화, 2026-04-06~07)

| # | 항목 | 상태 |
|---|------|------|
| A1 | **Cross-encoder Reranking** — `ms-marco-MiniLM-L-6-v2`, 벡터+BM25→MMR→정밀 재정렬→top-K | ✅ 완료 |
| A2 | **시맨틱 청킹** — bge-m3 임베딩 유사도 기반 의미 경계 탐지 (`similarity_threshold=0.75`), 폴백 지원 | ✅ 완료 |
| A3 | **이미지 PDF OCR** — Tesseract 5 kor+eng, 페이지당 30자 미만 시 자동 폴백 | ✅ 완료 |
| A4 | **3단계 RBAC + 문서 접근 제어** — admin/manager/user, 문서별 is_public + allowed_roles 멀티셀렉트 | ✅ 완료 |
| A5 | **신뢰도 점수** — sigmoid 절대 관련도 변환, 가중 평균 (최고점 60% + 상위절반 40%), 답변 헤더 배지 | ✅ 완료 |
| A6 | **감사 로그 (QueryLog)** — 질문·응답·신뢰도·지연시간 DB 저장, 시스템 설정 페이지 통계 | ✅ 완료 |
| A7 | **청크 원문 미리보기** — 출처 배지 클릭 시 청크 전문 팝업, 검색 결과 원문 토글 | ✅ 완료 |
| A8 | **문서별 채팅 필터** — 입력창 퍼널 버튼 → 문서 멀티셀렉트, 선택 문서만 RAG 검색 | ✅ 완료 |
| A9 | **LLM 모델 런타임 전환 UI** — 시스템 설정 페이지에서 Ollama 모델 목록 조회·즉시 전환 | ✅ 완료 |
| A10 | **서버 재시작 시 stuck 문서 자동 복구** — processing 고착 → failed 자동 변경, UI 삭제 버튼 | ✅ 완료 |
| A11 | **유사도 임계값 상향** — 0.30 → 0.50, MMR 후 hybrid score 0.45 미만 최종 제거 | ✅ 완료 |
| A12 | **브랜드 로고 이미지 적용** — 사이드바·로그인·모바일 헤더 전체 | ✅ 완료 |

---

## 우선순위 요약

| 단계 | 항목 번호 | 기준 | 진행 상태 |
|------|-----------|------|-----------|
| **즉시 수정** | #1 ~ #6 | 배포 시 보안 사고 직결 | ✅ 전체 완료 |
| **배포 전 필수** | #7 ~ #8 | 핵심 기능 불작동 | ✅ 전체 완료 |
| **프로덕션 기준** | #9 ~ #13 | 운영 안정성 미달 | ✅ 전체 완료 |
| **단기 개선** | #14 ~ #21 | 품질·보완 | ✅ 7/8 완료 (#14 제외) |
| **장기 과제** | #22 ~ #26 | 경쟁력 강화 | ✅ 2/5 완료 (#25, #26) |
| **2차 RAG 품질 강화** | A1 ~ A12 | 검색 정확도·UX·거버넌스 | ✅ 전체 완료 |

> **현재 결론**: 2차 개선 완료로 기능 완성도 92%, 상용화 준비도 82% 도달.  
> 남은 장기 과제 (#22 테스트코드, #23 토큰 폐기, #24 중복 업로드 감지, #14 HttpOnly 쿠키)는 운영 중 단계적으로 적용 권장.  
> 멀티모달(차트·도표 이해) 은 다음 개선 단계 후보.

