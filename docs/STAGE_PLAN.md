# BAIKAL 안정화 계획 — 5 Stage 로드맵

> **시작일**: 2026-04-29
> **목적**: 시연 가능한 안정성 + 회귀 방지 체계 확보
> **원칙**:
> 1. 한 번에 한 Stage만, 병렬 패치 금지
> 2. 변경마다 자동 검증(스크립트/테스트) → PASS 기록 후 다음 단계
> 3. 인덱싱 진행 중 백엔드 재시작 금지
> 4. Stage 단위로 git commit · tag (`stage-1-stable` …)
> 5. 검증 안 된 항목은 명시적으로 "🟡 검증 안 됨"로 표기

---

## Stage 1 — Data Integrity (데이터 무결성)

| #   | 항목                                              | 상태             | 검증              |
| --- | ------------------------------------------------- | ---------------- | ----------------- |
| 1.1 | 스트리밍 단절 시 user/assistant 메시지 DB 보존    | ✅ 완료 (3/3 PASS) | `scripts/test_stage1_streaming.ps1` |
| 1.2 | 인덱싱 batch commit (50청크 단위) + 진행률 컬럼   | ✅ 완료           | DB columns + alembic 0008 적용 |
| 1.2b | 임베딩 진짜 batch (Ollama input=list) + 진행률 cb | ✅ 완료 (745s→36s, 95.2%↓) | `scripts/test_stage1_indexing_perf.ps1` |
| 1.3 | 백엔드 재시작 안전 인덱싱 (resume / 명시적 retry) | ✅ 완료 (7/7 PASS) | `scripts/test_stage1_restart_retry.ps1` |
| 1.4 | Stage 1 회귀 일괄 + git tag                       | ⏳ 진행 예정      | 모든 1.x 테스트 PASS |

### 1.1 — 발견 사항 (영구 기록)
- **백엔드는 image COPY 방식이라 `restart`만으로는 코드 변경 반영 안 됨** → 반드시 `build` 후 `up -d`
- StreamingResponse `yield` 후 `await` 단계는 client disconnect 시 GeneratorExit 로 스킵 → DB 저장 필요한 것은 `yield` 이전에 commit
- **PowerShell `Invoke-RestMethod` multipart 업로드는 binary 파일을 ISO-8859-1↔UTF-8 변환으로 부풀려 ZIP 시그니처 깨뜨림** (215258B → 274205B). 자동화 업로드는 Python `requests` 사용 (`scripts/reupload_haengjeong.py`).

---

## Stage 2 — Answer Quality (답변 품질)

| #   | 항목                                          | 상태 | 검증 |
| --- | --------------------------------------------- | ---- | ---- |
| 2.1 | SYSTEM_PROMPT ⛔ 절대 규칙 5종 (외국·미래·개인·외부·무관) | ✅ 완료 | D그룹 5/5 PASS |
| 2.2 | 행정절차법 hwpx 재색인 (PDF 손상 → hwpx 202청크) | ✅ 완료 | Q3, Q11 PASS |
| 2.3 | 20문항 자동 채점 baseline                       | ✅ 완료 | **15/20 (게이트 14/20) ✅** |
| 2.4 | git tag stage-2-stable                          | ✅ 완료 | A 4/8, B 4/4, C 2/3, D 5/5 |

### 2.x — 발견 사항 (영구 기록)
- **A 그룹 미달 4건은 데이터 부재 / 응답 시간 초과**: Q05(표준 정보공개 조례안 미색인), Q07(표준 복무 조례안 미색인), Q08(인사 예규 미색인), Q02(LLM 180s 타임아웃, 답변 길어짐). 시스템 결함 아님.
- 평가 스크립트 `scripts/eval_demo_q20.py`, baseline `scripts/q20_full_baseline.json`
- Q4 (청문 시기) PASS 확인됨 — Stage 2.1 프롬프트 강화 효과 확인

---

## Stage 3 — UX 안정성

| #   | 항목                                            |
| --- | ----------------------------------------------- |
| 3.1 | "응답없음" → "처리 중 (n/m chunks, %)" 라이브 표시 |
| 3.2 | 업로드 실패 시 명확한 사유 + 재시도 버튼        |
| 3.3 | 답변 도중 페이지 이동 → 돌아오면 부분답변 보임  |
| 3.4 | 모달 portal 일관 적용 점검                      |

---

## Stage 4 — Observability (관찰 가능성)

| #   | 항목                                          |
| --- | --------------------------------------------- |
| 4.1 | structured logging (request_id, session_id)   |
| 4.2 | /api/admin/query-logs 신뢰도 분포 차트        |
| 4.3 | Ollama 응답 시간 histogram                     |
| 4.4 | 시연 전 점검 체크리스트 자동 실행 스크립트    |

---

## Stage 5 — 시연 리허설

| #   | 항목                                                                |
| --- | ------------------------------------------------------------------- |
| 5.1 | 표준 5건 색인 상태 일치 (정보공개·행정절차·표준조례×2·인사예규)     |
| 5.2 | 20개 질문 전체 라이브 답변 → 14/20 이상 합격                        |
| 5.3 | 의도적 단절·재연결 시연                                             |
| 5.4 | 컨소시엄 대표 시연 리허설 (대본 + Q&A 대응)                         |

---

## 진행 로그

### 2026-04-29
- ✅ Stage 1.1 완료 — `rag_service.py` user_msg를 sources yield 이전에 commit, 이미지 빌드, 3회 연속 PASS
- 📌 배포 절차 문서화: `restart` 단독 사용 금지, 항상 `build → up -d → 컨테이너 안 코드 확인`
- 🟡 SYSTEM_PROMPT 강화 (Stage 2.1)는 코드 적용·빌드는 됐으나 **답변 회귀 테스트 미실행**
- ✅ Stage 1.2 완료 — `documents.total_chunks/processed_chunks` 컬럼 + alembic 0008 적용, batch commit (50청크 단위)
- ✅ Stage 1.2b 완료 — `call_ollama_embedding`이 batch 내부에서 1개씩 직렬 호출하던 버그 수정 (Ollama `/api/embed` input=list 사용). 청킹/저장 양 단계 모두에 progress_cb 적용. 22청크 PDF 처리 시간 745s → 36s (**95.2% 단축**), 진행률 단조 증가 검증
  - 음수 total/processed = 청킹 단계 단락 임베딩 진행률, 양수 = 저장 단계 청크 임베딩 진행률
  - **잔여 위험**: 손상된 PDF는 OCR fallback으로 빠지면 분 단위 지연 (Stage 3.2에서 사용자 피드백 처리)
- ✅ Stage 1.3 완료 — `POST /api/documents/{id}/retry` 엔드포인트 추가. 재처리 시작 시 기존 청크 자동 정리(멱등성). 강제 kill→재기동 회귀 테스트 7/7 PASS (`scripts/test_stage1_restart_retry.ps1`)
  - completed 문서에 retry → 400 거부, failed 문서만 재처리 허용
  - main.py 기존 lifespan 복구 로직(고착 문서 → failed)이 그대로 작동함을 확인

### 변경된 파일 인덱스
- [backend/app/services/rag_service.py](backend/app/services/rag_service.py) — Stage 1.1 + 2.1
- [scripts/test_stage1_streaming.ps1](scripts/test_stage1_streaming.ps1) — Stage 1.1 회귀 테스트
- [docs/DEVELOPMENT_NOTES.md](DEVELOPMENT_NOTES.md) — 일별 작업 로그
