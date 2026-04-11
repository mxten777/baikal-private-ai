# BAIKAL Private AI — 기술 로드맵 & 시장경쟁력 분석

> **작성일**: 2026-04-12  
> **기준 버전**: Phase 1~3 전체 완료 (`5c1c795`)  
> **목적**: 기술 부채 현황 + 발전 방향 + 시장 포지셔닝 종합 제시

---

## 목차

1. [기술 부채 점검 결과](#1-기술-부채-점검-결과)
2. [기술 로드맵 (Phase 4~6)](#2-기술-로드맵-phase-4~6)
3. [시장경쟁력 분석](#3-시장경쟁력-분석)
4. [경쟁사 비교표](#4-경쟁사-비교표)
5. [GTM 전략 제안](#5-gtm-전략-제안)

---

## 1. 기술 부채 점검 결과

### 1.1 이번 세션 해소한 부채 (`5c1c795`)

| 위치 | 문제 | 해결 |
|------|------|------|
| `rag/embedder.py` | `print()` 로 에러 출력 | `logger.error()` 로 교체 |
| `services/auth_service.py` | `print()` 2곳 | `logger.info()` 로 교체 |
| `rag/retriever.py` | 루프 안 `import math` 중복 | 상단 임포트만 유지 |
| `rag/retriever.py` | `get_event_loop()` deprecated | `get_running_loop()` 로 교체 |
| `services/document_service.py` | `get_event_loop()` deprecated | `get_running_loop()` 로 교체 |
| `api/admin.py` | 함수 내 지역 `from sqlalchemy import func` | 지역 임포트 제거 (상단에 이미 존재) |

### 1.2 잔존 기술 부채 (우선순위별)

#### 🔴 높음 — 즉시 해결 권장

| # | 위치 | 문제 | 리스크 |
|---|------|------|--------|
| 1 | `config.py` L9 | `DATABASE_URL` 하드코딩 기본값에 평문 비밀번호 포함 | `.env` 미설정 시 보안 취약 노출 |
| 2 | `services/document_service.py` | PDF 처리 후 임시 파일 정리 로직 없음 (`/app/uploads/` 누적) | 장기 운영 시 디스크 고갈 |
| 3 | `rag/retriever.py` | Cross-encoder 모델 로드 실패 시 전체 검색이 hybrid_score fallback만 사용 — 관리자 알림 없음 | 품질 저하 无감지 |
| 4 | `api/chat.py` L~200 | 스트리밍 응답 중 DB 커밋 실패 시 에러가 클라이언트에 노출될 수 있음 | 감사 로그 누락 |

#### 🟠 중간 — 단기 개선 권장

| # | 위치 | 문제 | 영향 |
|---|------|------|------|
| 5 | `rag/loader.py` | HWP 섹션 파서가 `zlib.decompress(data, -15)` 실패를 소리없이 무시 | 비압축 HWP 섹션 텍스트 누락 가능 |
| 6 | `services/document_service.py` | `_semantic_chunk_document` 함수 파라미터 8개 — 의존성 주입 과다 | 테스트 작성 어려움 |
| 7 | `api/admin.py` | `activate_model()` 이 런타임 `settings` 객체를 직접 변경 — 멀티 워커(4개) 중 1개만 반영됨 | 모델 변경 일관성 없음 |
| 8 | `frontend/src/api/client.js` | `askStream` 에서 401 발생 시 refresh 재시도 후 실패하면 `window.location.href = '/login'` 하드코딩 | CSP 환경에서 동작 불안정 |

#### 🔵 낮음 — 리팩토링 기회

| # | 위치 | 문제 |
|---|------|------|
| 9 | `rag/retriever.py` | BM25 정규화에 `max_bm25 > 0` 체크 후 나누기, 그 위에서 이미 candidates 있음 확인 — 방어 코드 중복 |
| 10 | `services/rag_service.py` | `ask_question` 과 `ask_question_stream` 이 동일한 guardrail→context→history→messages 흐름을 각각 보유 — 공통 추출 여지 |
| 11 | `frontend` | Tailwind 4.x 출시됨. 현재 3.x 사용 중 — CDN Play 방식 불필요한 purge 설정 없음 확인 필요 |

---

## 2. 기술 로드맵 (Phase 4~6)

### Phase 4 — 운영 안정성 (1~2개월)

> **목표**: 실 파일럿 고객 운영을 위한 관측 가능성(Observability)과 복원력 확보

| ID | 항목 | 구현 위치 | 효과 |
|----|------|-----------|------|
| P4-1 | **업로드 파일 TTL 관리** | `document_service.py` + cron | 디스크 고갈 방지, 삭제 문서 파일 자동 정리 |
| P4-2 | **구조화 로그 (JSON)** | `main.py` 로깅 설정 | ELK / Loki 연동 기반, 운영 모니터링 준비 |
| P4-3 | **헬스체크 상세화** | `GET /api/health` 확장 | DB 연결시간, 모델 상태, 디스크 여유 포함 |
| P4-4 | **Cross-encoder 로드 실패 알림** | `retriever.py` + admin API | 무감지 품질 저하 방지 |
| P4-5 | **멀티 워커 모델 변경** | Redis pub/sub 또는 env reload | `activate_model` 전 워커 일관성 보장 |
| P4-6 | **문서 재처리 API** | `POST /api/documents/{id}/reprocess` | 업로드 성공 후 failed 문서 재시도 UI |

### Phase 5 — 확장성 (3~6개월)

> **목표**: 엔터프라이즈 규모(수백 사용자, 수만 문서) 대응

| ID | 항목 | 내용 |
|----|------|------|
| P5-1 | **임베딩 캐시** | Redis에 `{text_hash: embedding}` 캐시 → 동일 문서 재업로드 시 임베딩 재생성 불필요 |
| P5-2 | **비동기 임베딩 배치** | 청크 100개를 5개씩 배치 병렬 요청 → 대용량 문서 처리 속도 5~10배 향상 |
| P5-3 | **pgvector HNSW 인덱스** | 현재 ivfflat → HNSW 전환 → 검색 지연시간 50% 단축 (100만 벡터 기준) |
| P5-4 | **문서 버전 관리** | Document Lineage 기반 v1→v2 버전 추적, 구버전 청크 자동 비활성화 |
| P5-5 | **멀티 테넌시** | `organization_id` 기반 데이터 격리 → SaaS 전환 기반 |
| P5-6 | **WebSocket 실시간 처리 상태** | 현재 polling → WS push → 문서 처리 완료 즉시 UI 알림 |

### Phase 6 — AI 고도화 (6~12개월)

> **목표**: RAG 품질 정점 + 차세대 AI 기능으로 경쟁사 격차 유지

| ID | 항목 | 내용 |
|----|------|------|
| P6-1 | **Self-RAG** | LLM이 검색 필요 여부를 스스로 판단 (Retrieval On-demand) → 단순 질문 응답속도 70% 단축 |
| P6-2 | **RAPTOR 계층 청킹** | 청크 → 요약 → 요약의 요약 트리 구조 → 전략 문서, 장문 보고서 이해도 향상 |
| P6-3 | **Graph RAG** | 문서 간 엔티티 관계 그래프 → "A 규정이 B 정책에 미치는 영향" 같은 복합 질의 처리 |
| P6-4 | **Fine-tuning 파이프라인** | 고객 문서 기반 LoRA fine-tuning → 도메인 특화 용어 인식 강화 |
| P6-5 | **음성 인터페이스** | STT(Whisper) + TTS 연동 → 현장 근무자(공장, 현장) 음성 질의 지원 |
| P6-6 | **GPU 자동 스케일링** | CPU 모드 유지하되 GPU 노드 추가 시 자동 offload → Kubernetes HPA 연동 |

---

## 3. 시장경쟁력 분석

### 3.1 현재 포지셔닝

```
              높은 보안/폐쇄망
                    ↑
                    │
     [BAIKAL]  ●   │
                    │
낮은 RAG 품질 ───────┼─────── 높은 RAG 품질
                    │
                    │   [Microsoft Copilot]
                    │   [Google Vertex AI RAG]
                    ↓
              낮은 보안/클라우드 의존
```

**BAIKAL의 차별화 영역**: 폐쇄망 + 높은 RAG 품질을 동시에 달성한 유일한 국산 제품

### 3.2 타겟 시장 규모

| 시장 | 규모 (국내) | 근거 |
|------|------------|------|
| 공공기관 AI 도입 | ~3,400억원/년 (2026) | 디지털플랫폼정부 예산 |
| 금융/보험 RegTech AI | ~1,200억원/년 | FSC 금융혁신 로드맵 |
| 제조 스마트공장 AI | ~2,800억원/년 | 산업부 스마트제조 정책 |
| 의료/제약 문서 AI | ~900억원/년 | 보건복지부 디지털 전환 |
| **합계 (타겟 세그먼트)** | **~8,300억원/년** | |

### 3.3 핵심 강점 (Value Proposition)

#### ① 완전 폐쇄망 — 데이터 주권 보장
- 외부 API 호출 **0건** (Ollama 완전 로컬)
- 망분리 환경(국방, 금융, 공공) 그대로 설치 가능
- CSAP(클라우드 보안인증) 취득 경로 열려있음

#### ② 한국어 문서 네이티브 처리
- **HWP/HWPX 네이티브 파서** — 경쟁사 전부 미지원
- 한국어 BGE-M3 임베딩 (다국어 최고 성능)
- 한국어 2-gram 토크나이저 내장 BM25

#### ③ Enterprise-grade 신뢰 아키텍처
- 출처 100% 추적 (청크 → 문서 → 페이지 번호)
- 감사 로그 + RBAC + Zero Trust (토큰 폐기)
- Guardrail + Policy Violation 기록

#### ④ 검색 품질 최상위 구조
```
Vector (70%) + BM25 (30%) → MMR (다양성) → Cross-encoder (정밀도) → HyDE (선택)
```
- BM25 + Vector Hybrid: Azure AI Search, Amazon Kendra와 동등
- Cross-encoder reranking: Cohere Rerank API와 동등 (로컬에서!)
- HyDE 모드: 최신 연구 결과 적용

---

## 4. 경쟁사 비교표

| 기능/항목 | **BAIKAL** | Microsoft Copilot | AWS Bedrock RAG | LangChain RAG | MyData AI (국산) |
|----------|-----------|-------------------|-----------------|---------------|-----------------|
| **완전 폐쇄망** | ✅ **Native** | ❌ Azure 필수 | ❌ AWS 필수 | 🔶 구성 가능 | 🔶 일부 가능 |
| **HWP 지원** | ✅ | ❌ | ❌ | ❌ | 🔶 외부 변환 |
| **한국어 특화** | ✅ | 🔶 일반 | 🔶 일반 | 🔶 일반 | ✅ |
| **Cross-encoder** | ✅ 로컬 | ❌ (Semantic Ranker) | 🔶 옵션 | 🔶 별도 구성 | ❌ |
| **HyDE 모드** | ✅ | ❌ | ❌ | 🔶 수동 구현 | ❌ |
| **KPI 대시보드** | ✅ 5탭 | ✅ (Azure Monitor) | 🔶 CloudWatch | ❌ | 🔶 기초 수준 |
| **감사 로그** | ✅ 완전 | ✅ | ✅ | ❌ | 🔶 |
| **피드백 루프** | ✅ 구현됨 | ✅ | 🔶 | ❌ | ❌ |
| **RBAC** | ✅ | ✅ | ✅ | ❌ | 🔶 |
| **Document Lineage** | ✅ | 🔶 SharePoint 연동 | ❌ | ❌ | ❌ |
| **월 사용료** | 🔶 서버비만 | 💰 $30~50/사용자 | 💰 종량제 | 🔶 자체 구성 | 💰 별도 계약 |
| **설치 난이도** | 🔶 Docker 1회 | ❌ 클라우드 필수 | ❌ 클라우드 필수 | ❌ 개발자 필요 | 🔶 |

> ✅ 완전 지원 · 🔶 부분/조건부 지원 · ❌ 미지원

### 비교 요약

| 시나리오 | 추천 솔루션 | 이유 |
|----------|------------|------|
| 공공기관 망분리 환경 | **BAIKAL** ✅ | 유일하게 완전 폐쇄망 + RBAC + 감사로그 |
| 글로벌 기업 (영어 중심) | Microsoft Copilot | Microsoft 생태계 통합 |
| 개발팀 자체 구축 | LangChain | 커스터마이징 자유도 |
| 국내 중견 제조 (HWP 필수) | **BAIKAL** ✅ | HWP 유일 지원 + 폐쇄망 |
| AWS 기반 스타트업 | Bedrock RAG | 기존 인프라 활용 |

---

## 5. GTM 전략 제안

### 5.1 즉시 착수 (0~3개월)

#### Anchor Customer 전략
```
목표: 공공기관 1곳 + 제조기업 1곳 레퍼런스 확보

공공기관 후보군:
  - 지자체 (시청, 도청): 조례/규정 검색 AI → 담당자 1명이 결정
  - 공공기관 (공단, 공사): 내규 검색 자동화 → 법무팀 Pain Point
  - 군 (국방부 산하): 매뉴얼/교범 검색 → 폐쇄망 필수 요건 충족

제조기업 후보군:
  - 중견 제조 (500~2,000명): ERP/MES 연동 전 1단계 도입
  - 품질/안전팀: ISO 규정, SOP 검색 자동화 → HWP 사용 多
```

#### Use-case 패키지 정의

| 패키지 | 대상 | 핵심 기능 | 가격 레인지 |
|--------|------|-----------|------------|
| **규정 검색 AI** | 공공기관, 금융 | 내규/법령 Q&A + 출처 표시 | 연 3,000~5,000만원 |
| **품질 매뉴얼 AI** | 제조 | SOP/작업지시서 검색 | 연 2,000~4,000만원 |
| **계약서 분석 AI** | 법무, 구매팀 | 계약 조항 비교/검색 | 연 4,000~8,000만원 |

### 5.2 Partner-Led 전략 (3~6개월)

```
직접 영업 → 실패 확률 높음 (공공: 조달, 제조: 구매팀 프로세스)

권장 채널:
  1. SI 파트너 (삼성SDS, LG CNS, SK C&C 계열)
     → 기존 고객사 인프라에 BAIKAL 번들
     → 수익 배분: 구축비는 SI, 라이선스는 BAIKAL

  2. 보안 솔루션 업체 (안랩, 시큐아이)
     → 망분리 솔루션에 AI 기능 번들
     → 기존 공공 채널 활용

  3. 문서관리 솔루션 업체 (Edimax, 한글과컴퓨터)
     → HWP 연동 강점으로 협력 가능
```

### 5.3 가격 전략

```
현재         →     목표 (2026년 말)

프리 티어 없음    자가설치 무료 (Community Edition)
                    ↓
                 유료 엔터프라이즈 (지원 + SLA)
                    - Standard: 연 3,000만원 (50 사용자)
                    - Professional: 연 6,000만원 (200 사용자 + 커스텀 모델)
                    - Enterprise: 협의 (무제한 + 온사이트 지원)
```

### 5.4 기술 차별화 유지 전략

```
경쟁사가 따라오기 어려운 순서로 투자:

1단계 (현재 완성): 폐쇄망 + HWP + Cross-encoder
   → 따라오려면 6~12개월 필요

2단계 (Phase 4~5): Self-RAG + Graph RAG + Fine-tuning 파이프라인
   → 학술 연구 기반, 구현 난이도 高

3단계 (Phase 6): 도메인별 Fine-tuned 모델 제공
   → "공공기관 특화 BAIKAL", "제조 특화 BAIKAL" 버티컬화
   → 경쟁사가 절대 제공 못하는 폐쇄망 Fine-tuning
```

---

## 부록: 현재 아키텍처 성숙도 평가

| 레이어 | 현재 수준 | 목표 수준 | 갭 |
|--------|-----------|-----------|-----|
| **RAG 검색 품질** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 없음 (Phase 6에서 더 고도화) |
| **보안/거버넌스** | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐⭐ | CSAP 인증, ISMS-P 대응 |
| **운영 안정성** | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ | Phase 4 (로그, 헬스체크, TTL) |
| **확장성** | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ | Phase 5 (캐시, HNSW, 멀티테넌시) |
| **GTM 준비도** | ⭐⭐☆☆☆ | ⭐⭐⭐⭐⭐ | 파트너 채널, Use-case 패키지 |
| **UI/UX 성숙도** | ⭐⭐⭐⭐☆ | ⭐⭐⭐⭐⭐ | 모바일 반응형, 접근성 |

---

> **문서 끝** | BAIKAL Private AI 기술 로드맵 & 시장경쟁력 분석  
> 작성: 2026-04-12 | 다음 업데이트 예정: Phase 4 완료 시점
