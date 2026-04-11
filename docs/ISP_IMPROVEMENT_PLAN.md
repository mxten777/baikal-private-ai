# BAIKAL Private AI — ISP 검토 기반 개선 계획서

> **작성일**: 2026-04-08 | **최종 업데이트**: 2026-04-12  
> **기반 자료**: 外 ISP/컨설팅 검토 의견 (1차: 사업/기술 구조 평가 + 2차: RAG KPI Dashboard 설계)  
> **현재 완성도**: 기능 **100%** · 상용화 준비도 **95%** (Phase 1~3 전체 + P3-3 HyDE 완료 기준)

---

## 목차

1. [컨설팅 핵심 진단 요약](#1-컨설팅-핵심-진단-요약)
2. [KPI 대시보드 설계 방향](#2-kpi-대시보드-설계-방향)
3. [개선 방안 전체 목록](#3-개선-방안-전체-목록)
4. [Phase별 상세 구현 계획](#4-phase별-상세-구현-계획)
5. [QueryLog 스키마 확장 설계](#5-querylog-스키마-확장-설계)
6. [KPI 목표값 정의표](#6-kpi-목표값-정의표)
7. [우선순위 요약](#7-우선순위-요약)

---

## 1. 컨설팅 핵심 진단 요약

### 1.1 강점 (유지)

| 항목 | 평가 | 비고 |
|------|------|------|
| RAG 품질 구조 | ✅ 상용 수준 | Hybrid + MMR + Cross-encoder |
| 보안/폐쇄망 | ✅ 매우 강점 | 외부 API 의존 0 |
| 엔터프라이즈 기능 | ✅ 최소 요건 충족 | RBAC, 감사로그, 문서 접근제어 |
| HWP/한글 문서 | ✅ 국내 차별성 | HWP/HWPX 네이티브 처리 |
| 기술 성숙도 | Early Product → **Pilot Ready** | 지금 당장 팔 수 있는 수준 |

### 1.2 핵심 리스크 3가지

#### ① 제품 vs SI 충돌 리스크 (🔴 심각)

- 공공/제조 고객은 "제품"이 아니라 "커스터마이징"을 요구함
- 방치 시: 제품 회사 → SI 회사로 변질, 유지보수 비용 폭증, 확장성 붕괴
- **대응 원칙**: SI 요청 수용 기준선을 명확히 문서화하고, 커스터마이징 범위를 설정/API 옵션 한계치로 통제

#### ② GTM 전략 부재 (🔴 즉시 착수 필요)

현재 있는 것: 제품 정의, 기술, 시장 분석  
현재 없는 것: **세일즈 구조, 고객 확보 Funnel, 파트너 전략 구체화**

권장 GTM 구조:
- **Anchor Customer 전략**: 공공기관 1곳 + 제조기업 1곳 레퍼런스 확보
- **Partner-Led Sales**: SI 업체/보안 솔루션 업체 채널 (직접 영업은 거의 실패)
- **Use-case 패키징**: "규정 검색 AI" / "계약서 분석 AI" / "품질 매뉴얼 AI" 등 문제 해결 단위 판매

#### ③ 신뢰 UX 미완성 (🟠 상용화 진입 장벽)

기업 사용자 기준: **"맞는 답"보다 "틀리지 않는 증거"가 중요**

현재 구현된 것: 청크 원문 팝업, 유사도 점수 배지  
아직 없는 것:
- 답변 내 인용 문장 **하이라이트** (어느 문장이 어느 청크에서 왔는지)
- 원본 문서 내 **페이지 번호/위치 표시**
- 근거 없는 답변 시 **저신뢰도 경고 배지**

### 1.3 ISP 보완 방향 4가지

| # | 항목 | 방향 |
|---|------|------|
| 4.1 | 제품 → 플랫폼 재정의 | 문서 QA Tool → **Enterprise Knowledge Platform** (4레이어 구조) |
| 4.2 | GTM 전략 재설계 | Anchor Customer + Partner-Led + Use-case Packaging |
| 4.3 | RAG 품질 측정 체계 | Precision@K, Faithfulness, Citation Accuracy 정량 평가 |
| 4.4 | 차별화 포인트 재정의 | "폐쇄망+한글" → **"Enterprise-grade Trustable AI"** (출처 100% 추적, 감사, 권한 기반 응답) |

---

## 2. KPI 대시보드 설계 방향

### 2.1 5축 KPI 프레임워크

```
[RAG KPI Framework]
축 1. Retrieval Quality     — 검색 정밀도·순위 품질
축 2. Answer Quality & Trust — 답변 신뢰성·근거 충실도
축 3. System Performance     — 응답시간·인덱싱·OCR
축 4. User Adoption          — 실사용률·업무 가치
축 5. Security / Governance  — 감사·권한·정책 준수
```

### 2.2 현재 시스템 설정 페이지 vs 목표 대시보드 Gap

| 항목 | 현재 (SettingsPage) | 목표 (KPI Dashboard) |
|------|---------------------|----------------------|
| 총 질의 수 | ✅ 있음 | ✅ 유지 + 추이 차트 |
| 평균 신뢰도 | ✅ 있음 | ✅ 유지 + 분포 차트 |
| 평균 응답시간 | ✅ 있음 | ✅ 유지 + 단계별 분리 |
| Precision@K | ❌ 없음 | 추가 필요 |
| Citation Accuracy | ❌ 없음 | 추가 필요 |
| Answer Faithfulness | ❌ 없음 | 추가 필요 |
| 문서 유형별 품질 | ❌ 없음 | 추가 필요 |
| 사용자 피드백 수집 | ❌ 없음 | 추가 필요 |
| Access Denied Count | ❌ 없음 | 추가 필요 |
| 검색 단계별 지연시간 | ❌ 없음 | 추가 필요 |
| Active User Rate | ❌ 없음 | 추가 필요 |
| 출처 클릭률 | ❌ 없음 | 추가 필요 |

### 2.3 필수 로그 필드 (현재 → 목표)

**현재 `query_logs` 테이블 필드:**
```
id, user_id, query, response_summary, document_ids,
confidence_score, latency_ms, created_at
```

**추가 필요 필드 (KPI 산출 근거):**
```
session_id         — 세션 연결 (MAU/WAU 산출)
retrieved_chunks   — 검색된 청크 ID 목록 (Precision@K 산출 기반)
reranked_order     — Cross-encoder 재정렬 후 순서 (Reranking Lift 측정)
cited_sources      — LLM이 실제 인용한 청크 ID 목록 (Citation Accuracy)
model_name         — 사용된 LLM 모델명 (모델별 품질 비교)
retrieval_ms       — 검색 단계 소요시간
reranking_ms       — Cross-encoder 단계 소요시간
llm_ms             — LLM 생성 단계 소요시간
feedback_score     — 사용자 피드백 (1=좋음, -1=나쁨, null=미응답)
click_source_flag  — 출처 원문 클릭 여부 (Source Click-through Rate)
```

---

## 3. 개선 방안 전체 목록

### 🔴 Phase 1 — ✅ 완료

| ID | 분류 | 개선 항목 | 구현 위치 | 효과 |
|----|------|-----------|-----------|------|
| P1-1 | **로그 확장** | `query_logs` 에 9개 필드 추가 + Alembic 마이그레이션 ✅ | `models/document.py` + `alembic/versions/0003` | KPI 전체 산출 기반 확보 |
| P1-2 | **로그 수집** | RAG 서비스에서 `retrieved_chunks`, `reranked_order`, `cited_sources`, `retrieval_ms`, `reranking_ms`, `llm_ms` 기록 ✅ | `services/rag_service.py` | Precision@K, Reranking Lift, 단계별 지연시간 |
| P1-3 | **사용자 피드백** | 답변 하단 👍👎 버튼 추가, `/api/chat/feedback` 엔드포인트 ✅ | `api/chat.py` + `ChatMessage.jsx` | Answer Acceptance Rate, Query Success Rate proxy |
| P1-4 | **출처 클릭 트래킹** | 출처 배지 클릭 시 `/api/chat/source-click` 이벤트 기록 ✅ | `api/chat.py` + `ChatMessage.jsx` | Source Click-through Rate |
| P1-5 | **신뢰도 배지 강화** | confidence < 0.4 시 "근거 부족" 경고 배지, 스타일 변경 ✅ | `ChatMessage.jsx` | 신뢰 UX — 저신뢰도 경고 |

### 🟠 Phase 2 — ✅ 완료

| ID | 분류 | 개선 항목 | 구현 위치 | 효과 |
|----|------|-----------|-----------|------|
| P2-1 | **KPI 대시보드 UI** | 시스템 설정 페이지를 5탭 대시보드로 확장 (Executive / Retrieval / Answer Trust / Operations / Governance) ✅ | `pages/admin/SettingsPage.jsx` | ISP 납품형 경영 대시보드 |
| P2-2 | **응답 단계별 지연시간 차트** | 검색/Reranking/LLM 분리 스택 차트 ✅ | `SettingsPage.jsx` | 병목 구간 시각화 |
| P2-3 | **답변 신뢰도 분포 차트** | High/Medium/Low 구간별 질의 비율 파이 차트 ✅ | `SettingsPage.jsx` | Answer Trust 시각화 |
| P2-4 | **User 모델에 department 필드 추가** | 부서별 사용 통계 지원 ✅ | `models/user.py` + `alembic/versions/0005` | 부서별 도입률 KPI |
| P2-5 | **문서 페이지 번호 저장** | 청킹 시 `page_number` 필드 기록 ✅ | `models/document.py` + `rag/chunker.py` + `alembic/versions/0004` | 신뢰 UX — 원본 위치 표시 |
| P2-6 | **신뢰 UX 하이라이트** | 답변 내 인용 문장과 청크 원문 간 매칭 하이라이트 표시 ✅ | `ChatMessage.jsx` | 컨설팅 3.3 직접 대응 |
| P2-7 | **Active User Rate KPI** | 최근 7일/30일 활성 사용자 수/비율 산출 API ✅ | `api/admin.py` | User Adoption 축 |

### 🔵 Phase 3 — ✅ 완료

| ID | 분류 | 개선 항목 | 구현 위치 | 효과 |
|----|------|-----------|-----------|------|
| P3-1 | **Guardrail Engine** | 비관련/유해 질문 선제 차단 레이어, Policy Violation Count 기록 ✅ | `services/guardrail_service.py` | Control Plane 구현 |
| P3-2 | **평가 스크립트** | Precision@K, MRR, nDCG@K 자동 산출 테스트셋 ✅ | `scripts/eval_rag.py` | RAG 품질 정량 측정 체계 |
| P3-3 | **HyDE 검색 모드** | 배치/분석용 고정확도 모드 (LLM 2회 호출 옵션) ✅ | `rag/retriever.py` + UI 토글 버튼 | 검색 정확도 향상 |
| P3-4 | **JWT HttpOnly 쿠키 전환** | localStorage → HttpOnly Cookie (XSS 방어) ✅ | `api/auth.py` + `api/client.js` | 보안 강화 |
| P3-5 | **Refresh Token 폐기** | 탈취된 토큰 무효화 (DB 블랙리스트) ✅ | `services/auth_service.py` + `alembic/versions/0006` | Zero Trust 대응 |
| P3-6 | **Document Lineage** | 업로드자·수정일·파생 청크 수 계보 추적 ✅ | `models/document.py` + `alembic/versions/0007` | Knowledge Layer 완성 |
| P3-7 | **테스트 코드** | pytest (백엔드 핵심 API) + jest (프론트 주요 컴포넌트) ✅ | `tests/` + `__tests__/` | 납품 품질 기준 |
| P3-8 | **멀티모달** | 차트·도표 이미지 내용 추출 (qwen2.5-vl 연동) ✅ | `rag/loader.py` | 고급 문서 처리 |

---

## 4. Phase별 상세 구현 계획

### Phase 1-1: QueryLog 스키마 확장

**파일**: `backend/app/models/document.py`

추가 컬럼:
```python
session_id: Optional[str]        # chat_sessions.id FK (nullable)
retrieved_chunks: Optional[List] # JSON — [{"chunk_id": ..., "score": ...}]
reranked_order: Optional[List]   # JSON — chunk_id 목록 (재정렬 후 순서)
cited_sources: Optional[List]    # JSON — LLM이 인용한 chunk_id 목록
model_name: Optional[str]        # 사용 LLM 모델명
retrieval_ms: Optional[int]      # 검색 단계 ms
reranking_ms: Optional[int]      # Cross-encoder 단계 ms
llm_ms: Optional[int]            # LLM 생성 단게 ms
feedback_score: Optional[int]    # 1 / -1 / null
click_source_flag: Optional[bool]# 출처 클릭 여부
```

**새 Alembic 마이그레이션**: `alembic/versions/0003_querylog_kpi_fields.py`

### Phase 1-3: 사용자 피드백 엔드포인트

**신규 API**:
```
POST /api/chat/messages/{message_id}/feedback
body: {"score": 1 | -1}

POST /api/chat/messages/{message_id}/source-click
body: {"chunk_id": "..."}
```

### Phase 2-1: 대시보드 탭 구조

```
/admin/settings (현재) → /admin/dashboard
┌─────────────────────────────────────────────┐
│ [Executive] [Retrieval] [Trust] [Ops] [Governance] │
├─────────────────────────────────────────────┤
│ Executive 탭 (기본)                          │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│  │총질의│ │신뢰도│ │응답속도│ │활성유저│         │
│  └─────┘ └─────┘ └─────┘ └─────┘           │
│  [주간 품질 추이 차트]                        │
│  [답변 신뢰도 분포]    [리스크 알림 패널]      │
└─────────────────────────────────────────────┘
```

### Phase 2-5: 청크 페이지 번호 저장

**파일**: `backend/app/models/document.py` — `DocumentChunk`에 추가:
```python
page_number: Optional[int]   # PDF/DOCX 페이지 번호
source_type: Optional[str]   # "text" / "table" / "ocr"
```

**파일**: `backend/app/rag/chunker.py` — `page_number` 추출 후 저장

**UI 효과**: 출처 배지에 `바이칼_취업규칙.pdf p.12 78%` 형식으로 표시

### Phase 3-2: RAG 평가 스크립트

**파일**: `scripts/eval_rag.py`

평가 항목:
```
Precision@K   — 상위 K개 검색 결과 중 관련 청크 비율
Recall@K      — 정답 청크가 상위 K안에 포함되는 비율
MRR           — 최초 정답 청크가 몇 번째 순위에 등장하는지
nDCG@K        — 순위 가중 품질 평가
Reranking Lift — Cross-encoder 적용 전후 Precision@K 개선폭
```

테스트셋 형식 (`scripts/eval_testset.json`):
```json
[
  {
    "query": "바이칼 취업규칙에서 근무시간은?",
    "relevant_doc_ids": ["doc-uuid-1"],
    "expected_keywords": ["9시", "오전", "근무"],
    "query_type": "regulation"
  }
]
```

---

## 5. QueryLog 스키마 확장 설계

### 5.1 현재 → 목표 비교

```python
# 현재
class QueryLog(Base):
    id, user_id, query, response_summary,
    document_ids, confidence_score, latency_ms, created_at

# 목표 (0003 마이그레이션 추가 필드)
class QueryLog(Base):
    # 기존 유지
    id, user_id, query, response_summary,
    document_ids, confidence_score, latency_ms, created_at

    # KPI 산출을 위한 신규 필드
    session_id: Optional[str]         # 세션 연결
    retrieved_chunks: Optional[List]  # [{chunk_id, score, rank}]
    reranked_order: Optional[List]    # [chunk_id, ...] — Reranking 후 순서
    cited_sources: Optional[List]     # LLM이 실제 인용한 chunk_ids
    model_name: Optional[str]         # 사용 모델
    retrieval_ms: Optional[int]       # 검색 단계 ms
    reranking_ms: Optional[int]       # Reranking 단계 ms
    llm_ms: Optional[int]             # LLM 생성 단계 ms
    feedback_score: Optional[int]     # 👍=1 / 👎=-1 / null
    click_source_flag: Optional[bool] # 출처 클릭 여부
```

### 5.2 KPI 산출 방법

| KPI | 산출 방법 | 필요 필드 |
|-----|-----------|-----------|
| Query Success Rate | `feedback_score = 1` 건수 / 전체 | `feedback_score` |
| Source Click-through Rate | `click_source_flag = true` / 전체 | `click_source_flag` |
| Reranking Lift | 재정렬 전 Precision vs `reranked_order` 비교 | `retrieved_chunks`, `reranked_order` |
| 단계별 지연시간 | `retrieval_ms`, `reranking_ms`, `llm_ms` 평균 | 3개 ms 필드 |
| 모델별 성능 비교 | `model_name`으로 그룹화 후 `confidence_score` 평균 | `model_name`, `confidence_score` |
| Active User (WAU) | 지난 7일 `user_id` distinct count | `user_id`, `created_at` |

---

## 6. KPI 목표값 정의표

### 6.1 품질 목표 (초기 파일럿 기준)

| KPI | 산식 | 목표값 | 측정 주기 |
|-----|------|--------|-----------|
| Precision@5 | 관련 청크 수 / 5 | **80% 이상** | 주간 |
| Citation Accuracy | 정확 인용 건수 / 전체 인용 | **95% 이상** | 주간 |
| Answer Faithfulness | 근거 내 발언 비율 | **90% 이상** | 주간 |
| Table QA Exact Match | 표 질문 정답률 | **75% 이상** | 주간 |
| Query Success Rate | 피드백 긍정 / 전체 | **70% 이상** (초기) | 일간 |

### 6.2 성능 목표

| KPI | 목표값 | 측정 주기 |
|-----|--------|-----------|
| End-to-End 응답시간 | **8초 이하** (CPU 모드) | 일간 |
| 검색 단계 (`retrieval_ms`) | **1,500ms 이하** | 일간 |
| Reranking 단계 (`reranking_ms`) | **500ms 이하** | 일간 |
| 인덱싱 성공률 | **98% 이상** | 일간 |

### 6.3 운영 목표

| KPI | 목표값 | 측정 주기 |
|-----|--------|-----------|
| OCR 실패율 | **5% 이하** | 일간 |
| 감사로그 누락률 | **0%** | 일간 |
| 권한 위반 응답률 | **0%** | 일간 |

### 6.4 활용 목표 (파일럿 부서 기준)

| KPI | 목표값 | 측정 주기 |
|-----|--------|-----------|
| 활성 사용자율 (WAU) | **60% 이상** | 주간 |
| 반복 사용률 | **40% 이상** | 주간 |
| Source Click-through Rate | **30% 이상** | 주간 |

---

## 7. 우선순위 요약

### 착수 순서 (권장)

```
Week 1~2 (Phase 1)
  P1-1 QueryLog 스키마 확장 + Alembic 마이그레이션
  P1-2 RAG 서비스에서 단계별 시간/청크 로그 기록
  P1-3 답변 하단 👍👎 피드백 버튼 + API
  P1-4 출처 클릭 이벤트 트래킹
  P1-5 저신뢰도 경고 배지 (<40%)

Month 1 (Phase 2)
  P2-5 청크 페이지 번호 저장 (chunker + DB)
  P2-6 신뢰 UX 하이라이트 (인용 문장 ↔ 청크 매칭)
  P2-1 5탭 KPI 대시보드 UI 구성
  P2-2 단계별 지연시간 차트
  P2-3 신뢰도 분포 차트
  P2-4 User.department 필드 추가
  P2-7 Active User Rate API

Month 2~3 (Phase 3)
  P3-2 RAG 평가 스크립트 (eval_rag.py + 테스트셋)
  P3-1 Guardrail Engine (Policy Violation 차단)
  P3-4 JWT HttpOnly 쿠키 전환
  P3-5 Refresh Token 폐기 (DB 블랙리스트)
  P3-6 Document Lineage
  P3-7 테스트 코드 (pytest + jest)
  P3-3 HyDE 검색 모드 (옵션)
  P3-8 멀티모달 (qwen2.5-vl)
```

### 비즈니스 병행 과제 (코드 외)

| 항목 | 내용 | 시점 |
|------|------|------|
| SI 수용 기준 문서화 | 어디까지 커스터마이징 허용할지 정책 결정 | 즉시 |
| Anchor Customer 발굴 | 공공기관 1곳 + 제조기업 1곳 파일럿 후보 선정 | 즉시 |
| Use-case 패키지 작성 | "규정 검색 AI" 등 3종 상품 패키지 문서 | 1개월 |
| 파트너 채널 검토 | SI 업체/보안 솔루션 업체 접촉 | 2개월 |

---

## 부록: 아키텍처 목표 (ISP 권고)

```
[User / Channel Layer]
임직원 포털 | 업무시스템 | BI | 챗봇 | 모바일 | API 연계
↓
[AI Experience & Access Layer]          ← 현재: React UI (기본 구현)
SSO | RBAC | Prompt UI | API Gateway
↓
[AI Orchestration & Control Plane]      ← P3-1 Guardrail Engine 위치
Prompt Router | Policy Engine | Audit Logger | QoS Manager
↓
[BAIKAL RAG Engine]                     ← 현재: 완성
Hybrid Search | Semantic Chunking | Cross-encoder | OCR
↓
[Knowledge & Data Layer]                ← P2-5 Page# + P3-6 Lineage
HWP/PDF/DOCX/XLSX | Metadata | pgvector
↓
[LLM Runtime (Private AI)]              ← 현재: Ollama 완성
Local LLM | Model Registry | Runtime 전환
↓
[Infrastructure Layer]                  ← 현재: Docker Compose
Docker/K8s | GPU/CPU Hybrid
↓
[Security & Governance Layer]           ← P3-4 HttpOnly + P2-1 Dashboard
IAM | Audit Trail | ISMS-P | Zero Trust
```

**현재 수준**: RAG Engine + LLM Runtime + Infrastructure = **핵심 3개 레이어 완성**  
**목표 수준**: Control Plane + Knowledge Lineage + Governance Dashboard = **Enterprise Platform 완성**

---

> **문서 끝** | BAIKAL Private AI ISP 개선 계획서  
> **최종 업데이트**: 2026-04-12 — Phase 1 · 2 · 3 전체 완료 (P3-3 HyDE 포함, 총 20개 항목 구현 완료)
