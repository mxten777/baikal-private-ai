# BAIKAL Private AI — Copilot 코딩 지침

## 프로젝트 개요

- **구조**: FastAPI 백엔드 (`backend/app/`) + React 프론트엔드 (`frontend/src/`) + Docker Compose
- **배포**: `docker-compose.cpu.yml` (5개 컨테이너: backend:8000, frontend:3000, nginx:80, postgres, ollama)
- **관리자 계정**: username=`admin`, 비밀번호는 `.env`의 `DEFAULT_ADMIN_PASSWORD`
- **상세 문서**: `docs/` 디렉토리 참고

---

## 필수 규칙

### 1. 백엔드 파일 편집 후 반드시 문법 검사

Python 파일을 수정한 즉시 문법 검사를 실행한다. 이 단계를 생략하면 컨테이너 기동 실패로 이어진다.

```powershell
python -m py_compile backend/app/path/to/file.py && Write-Host "Syntax OK"
```

그 후 재빌드:
```powershell
docker compose -f docker-compose.cpu.yml build backend
docker compose -f docker-compose.cpu.yml up -d backend
```

### 2. React 모달은 반드시 `ReactDOM.createPortal(document.body)` 사용

`overflow: hidden` 또는 `transform`이 적용된 부모 안에 `fixed` 모달을 놓으면 잘린다.
모달 컴포넌트는 항상 `document.body`에 portal로 마운트한다.

```jsx
import ReactDOM from 'react-dom';

function Modal({ onClose }) {
  return ReactDOM.createPortal(
    <div style={{ zIndex: 9999 }} className="fixed inset-0 ..." onClick={onClose}>
      {/* 내용 */}
    </div>,
    document.body
  );
}
```

z-index는 Tailwind 클래스 대신 인라인 `style={{ zIndex: 9999 }}`을 사용한다.

### 3. 점수/확률 함수는 출력 범위를 주석으로 명시하고 min-max 정규화 금지

min-max 정규화는 입력 값의 절대 크기를 무시하고 상대적 순위만 반영하므로,
관련도가 낮은 결과도 1위가 되면 1.0이 되는 왜곡이 발생한다.
절대 관련도를 반영해야 하는 경우 sigmoid 변환을 사용한다.

```python
# 출력 범위: 0.0 ~ 1.0 (절대 관련도 반영)
# min-max 정규화 금지 — 청크 수에 따라 결과가 달라짐
import math
score = round(1 / (1 + math.exp(-ce_score)), 4)
```

신뢰도 집계 시 단순 평균 대신 가중 평균을 사용한다:
```python
# 최고점 60% + 상위 절반 평균 40%
scores = sorted([c['score'] for c in chunks], reverse=True)
upper_avg = sum(scores[:max(1, len(scores) // 2)]) / max(1, len(scores) // 2)
confidence = round(0.6 * scores[0] + 0.4 * upper_avg, 3)
```

### 4. 다중 파일 동시 편집 시 인코딩 주의

`multi_replace_string_in_file`로 한글 주석이 포함된 파일을 편집할 때
인코딩 불일치로 교체가 실패하거나 파일이 잘릴 수 있다.
실패 시 Python 스크립트로 직접 수정한다:

```python
with open('path/to/file.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
# 수정 후
with open('path/to/file.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
```

### 5. UI 조건부 렌더링은 가장 단순한 조건 사용

버튼/요소의 표시 조건에 불필요한 비교를 추가하지 않는다.
"데이터가 있으면 보여준다"가 기본 원칙이다.

```jsx
// 금지: 여러 조건 중첩
{result.content && result.content.length > result.content_snippet.length && (...)}

// 권장: 데이터 존재 여부만 확인
{result.content && (...)}
```

---

## API 엔드포인트 (확정)

```
POST /api/auth/login                  body: {username, password}
POST /api/auth/refresh                body: {refresh_token}
GET  /api/auth/me
GET  /api/users
POST /api/users
GET  /api/documents
POST /api/documents/upload
GET  /api/documents/{id}/status
DELETE /api/documents/{id}
GET  /api/chat/sessions
POST /api/chat/sessions
POST /api/chat/ask
POST /api/chat/ask/stream
GET  /api/search                      params: q=, mode=hybrid|vector|keyword
GET  /api/admin/query-logs
GET  /api/health
```

- 비인증 요청은 nginx 레벨에서 403 반환 (401이 아님)
- 검색 파라미터는 `q=` (query= 아님)
- trailing slash 없음

---

## 지원 파일 형식

업로드: `PDF`, `DOCX`, `XLSX`, `HWP`, `HWPX` (`.txt` 미지원)

---

## 프론트엔드 빌드 흐름

```powershell
# 1. React 빌드
cd frontend; npm run build

# 2. Docker 이미지 재빌드
cd ..; docker compose -f docker-compose.cpu.yml build frontend

# 3. 컨테이너 재시작
docker compose -f docker-compose.cpu.yml up -d frontend
```

백엔드는 `frontend` 대신 `backend`로 동일하게 적용.
