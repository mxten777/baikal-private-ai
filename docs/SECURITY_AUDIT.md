# BAIKAL Private AI — 자가 보안 점검 리포트

- 측정일: 2026-04-29 11:03:42
- 점검 항목: 총 7건
- 결과: ✅ PASS 5 · ⚠️ WARN 1 · ❌ FAIL 0 · ⏭ SKIP 1

## 요약

| # | 항목 | 상태 | 심각도 |
|--:|------|:----:|:------:|
| 1 | SECRET_KEY 설정 | ✅ PASS | info |
| 2 | 관리자 비밀번호 | ✅ PASS | info |
| 3 | APP_ENV 모드 | ✅ PASS | info |
| 4 | .env 파일 존재 | ✅ PASS | info |
| 5 | 외부 노출 포트 | ⚠️ WARN | medium |
| 6 | 외부 도메인 하드코딩 | ✅ PASS | info |
| 7 | 의존성 CVE 스캔 | ⏭ SKIP | info |

## 상세 결과

### ✅ SECRET_KEY 설정

- 상태: **PASS** (심각도 `info`)
- 상세: 길이 48자, 기본값 아님.

### ✅ 관리자 비밀번호

- 상태: **PASS** (심각도 `info`)
- 상세: 길이 12자, 기본값 아님.

### ✅ APP_ENV 모드

- 상태: **PASS** (심각도 `info`)
- 상세: production 모드입니다.

### ✅ .env 파일 존재

- 상태: **PASS** (심각도 `info`)
- 상세: C:\baikal777\baikal-private-ai\.env 존재. 운영 환경에서는 600 권한 권장.

### ⚠️ 외부 노출 포트

- 상태: **WARN** (심각도 `medium`)
- 상세: 비표준 포트 외부 노출: 8000, 3000. 내부 네트워크에서만 접근 가능한지 확인.

### ✅ 외부 도메인 하드코딩

- 상태: **PASS** (심각도 `info`)
- 상세: 외부 호출 도메인 미발견 (Ollama/Postgres 제외).

### ⏭ 의존성 CVE 스캔

- 상태: **SKIP** (심각도 `info`)
- 상세: pip-audit 미설치. `pip install pip-audit` 후 재실행.

---

*이 리포트는 `scripts/security_audit.py` 으로 자동 생성되었습니다. 외부 호출 없이 로컬에서만 실행됩니다.*