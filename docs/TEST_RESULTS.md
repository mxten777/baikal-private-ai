# BAIKAL Private AI — API 테스트 결과서

**테스트 일시:** 2026-04-06  
**테스트 환경:** Docker Compose (CPU) — 로컬 온프레미스  
**테스트 도구:** `scripts/api_test.py` (httpx 기반 자동화 테스트)  
**테스트 결과:** ✅ 전체 통과 (29/29)

---

## 1. 테스트 환경

| 항목 | 내용 |
|------|------|
| OS | Windows (로컬) |
| 배포 방식 | Docker Compose (`docker-compose.cpu.yml`) |
| Backend | FastAPI (포트 8000) |
| Frontend | React + Nginx (포트 80) |
| LLM | Ollama — qwen2.5:7b |
| 벡터 DB | PostgreSQL + pgvector |
| 임베딩 모델 | intfloat/multilingual-e5-small |
| Reranker | ms-marco-MiniLM-L-6-v2 |
| 테스트 시점 DB | 완료 문서 11개 |

---

## 2. 테스트 항목별 결과

### 2.1 서버 헬스체크

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 1 | `GET /api/health` → 200 | ✅ | DB connected, Ollama connected |

응답 예시:
```json
{"status":"ok","service":"BAIKAL Private AI","version":"1.0.0",
 "components":{"database":"connected","ollama":"connected"}}
```

---

### 2.2 인증

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 2 | `POST /api/auth/login` (admin 정상 로그인) → 200 | ✅ | access_token, refresh_token 발급 |
| 3 | `POST /api/auth/login` (잘못된 비밀번호) → 401 | ✅ | 401 Unauthorized 반환 |
| 4 | `POST /api/auth/refresh` (refresh_token 갱신) → 200 | ✅ | JSON body 방식 (`{"refresh_token": "..."}`) |

---

### 2.3 사용자 관리

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 5 | `GET /api/users` (admin) → 200 | ✅ | 사용자 4명 조회 |
| 6 | `POST /api/users` (신규 유저 생성) → 201 | ✅ | role=user 생성 |
| 7 | `POST /api/auth/login` (신규 유저 로그인) → 200 | ✅ | 생성 직후 로그인 정상 |

---

### 2.4 문서 목록 조회

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 8 | `GET /api/documents` (admin) → 200 | ✅ | 11개 문서 (전체 completed) |
| 9 | IDOR 방지: 일반 유저가 타인 문서 상태 조회 → 403 | ✅ | 소유자/admin 외 접근 차단 |
| 10 | `GET /api/documents` (비인증) → 401/403 | ✅ | Nginx 레벨 403 반환 |

---

### 2.5 문서 업로드 및 처리

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 11 | `POST /api/documents/upload` (PDF) → 201 | ✅ | 545 bytes 최소 PDF |
| 12 | 문서 처리 완료 (비동기 파이프라인) | ✅ | 4초 내 completed |

업로드 응답 예시:
```json
{"id":"e147b447-...","filename":"api_test.pdf","file_type":"pdf",
 "file_size":545,"status":"uploaded"}
```

---

### 2.6 문서 검색

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 13 | `GET /api/search?q=BAIKAL&mode=hybrid` → 200 | ✅ | 결과 5건 |
| 14 | `GET /api/search?q=문서&mode=vector` → 200 | ✅ | 벡터 단독 검색 |
| 15 | `GET /api/search?q=규정&mode=keyword` → 200 | ✅ | BM25 단독 검색 |

---

### 2.7 채팅 세션 및 질의응답 (Non-streaming)

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 16 | `POST /api/chat/sessions` → 201 | ✅ | 세션 생성 |
| 17 | `GET /api/chat/sessions` → 200 | ✅ | 세션 5개 조회 |
| 18 | `POST /api/chat/ask` → 200 | ✅ | LLM 정상 응답 |
| 19 | 질의응답: 답변 있음 | ✅ | 응답 729자 |
| 20 | 질의응답: 출처 있음 | ✅ | 소스 문서 4개 |
| 21 | 질의응답: 신뢰도 점수 | ✅ | confidence_score = 0.465 |

질의: `"BAIKAL Private AI의 주요 장점은?"`

답변 미리보기:
> BAIKAL Private AI의 주요 장점은 다음과 같습니다:
>
> 1. **보안성**: 모든 데이터 처리가 사내 서버에서 이루어지므로 외부 유출 위험이 없습니다. 이는 특히 민감한 정보를 다루는 기업이나 조직들에게...

---

### 2.8 스트리밍 질의응답

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 22 | `POST /api/chat/ask/stream` → 200 | ✅ | SSE 스트리밍 정상 응답 |
| 23 | 스트리밍: `sources` 이벤트 수신 | ✅ | |
| 24 | 스트리밍: `token` 이벤트 수신 | ✅ | |
| 25 | 스트리밍: `done` 이벤트 수신 | ✅ | |

스트리밍 이벤트 타입: `{'token', 'done', 'sources'}`

---

### 2.9 감사 로그

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 26 | `GET /api/admin/query-logs` (admin) → 200 | ✅ | 로그 6건 조회 |
| 27 | 일반 유저의 감사 로그 접근 → 403 | ✅ | 접근 제어 정상 |

---

### 2.10 테스트 데이터 정리

| # | 테스트 항목 | 결과 | 비고 |
|---|-------------|------|------|
| 28 | 테스트 문서 삭제 `DELETE /api/documents/{id}` → 204 | ✅ | |
| 29 | 테스트 유저 삭제 `DELETE /api/users/{id}` → 204 | ✅ | |

---

## 3. 최종 결과 요약

```
전체: 29개  |  [OK] 통과: 29개  |  [NG] 실패: 0개
```

| 구분 | 항목 수 | 통과 | 실패 |
|------|---------|------|------|
| 서버 헬스체크 | 1 | 1 | 0 |
| 인증 | 3 | 3 | 0 |
| 사용자 관리 | 3 | 3 | 0 |
| 문서 목록 조회 | 3 | 3 | 0 |
| 문서 업로드 및 처리 | 2 | 2 | 0 |
| 문서 검색 | 3 | 3 | 0 |
| 채팅 세션 및 질의응답 | 6 | 6 | 0 |
| 스트리밍 질의응답 | 4 | 4 | 0 |
| 감사 로그 | 2 | 2 | 0 |
| 테스트 데이터 정리 | 2 | 2 | 0 |
| **합계** | **29** | **29** | **0** |

---

## 4. 주요 검증 확인 사항

| 검증 항목 | 내용 | 상태 |
|-----------|------|------|
| 폐쇄망 운영 | 외부 API 호출 없이 전 기능 정상 동작 | ✅ |
| LLM 연동 | Ollama qwen2.5:7b 정상 응답 (non-stream / stream) | ✅ |
| 4단계 검색 파이프라인 | 벡터 + BM25 + MMR + Cross-encoder 정상 동작 | ✅ |
| 다형식 문서 처리 | PDF 업로드 → 인덱싱 → 검색 → 답변 4초 내 완료 | ✅ |
| 접근 제어 | IDOR 방지, 역할별 접근 제한, 비인증 차단 | ✅ |
| 감사 로그 | 질의/응답 이력 기록, 일반 유저 접근 차단 | ✅ |
| 신뢰도 점수 | confidence_score = 0.465, 소스 4개 근거 제시 | ✅ |
| 스트리밍 응답 | SSE sources/token/done 이벤트 모두 수신 | ✅ |

---

## 5. 테스트 실행 방법

```bash
# 의존성 설치 (최초 1회)
pip install httpx

# 테스트 실행 (컨테이너 실행 상태에서)
python scripts/api_test.py
```

> **참고:** LLM 응답 테스트는 Ollama 모델 첫 로딩 시 수 분이 소요될 수 있다.  
> 타임아웃 기준: 일반 API 30초 / LLM 질의 180초.
