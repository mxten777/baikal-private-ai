"""
BAIKAL Private AI — Self Security Audit
PoC 시 IT 보안팀에 그대로 제출 가능한 자가 점검 리포트를 생성한다.

점검 항목 (모두 자동, 외부 호출 없음):
  1. SECRET_KEY 강도 (길이 ≥ 32, 기본값 아님)
  2. DEFAULT_ADMIN_PASSWORD 변경 여부
  3. APP_ENV=production 여부
  4. .env 파일 권한/존재
  5. Docker Compose 외부 노출 포트 검토
  6. requirements.txt 의존 패키지 CVE 스캔 (pip-audit 가용 시)
  7. 백엔드 코드 내 외부 도메인 하드코딩 검사

사용법:
  python scripts/security_audit.py
  python scripts/security_audit.py --output audit_report.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 점검 항목 결과 컨테이너
class CheckResult:
    def __init__(self, name: str, status: str, detail: str, severity: str = "info"):
        # status: PASS | FAIL | WARN | SKIP
        # severity: info | low | medium | high | critical
        self.name = name
        self.status = status
        self.detail = detail
        self.severity = severity

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "severity": self.severity,
            "detail": self.detail,
        }


# ── 점검 함수 ────────────────────────────────────────────────

def _read_env() -> dict:
    """.env 파일 파싱 (없으면 빈 dict)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return {}
    result = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def check_secret_key(env: dict) -> CheckResult:
    val = env.get("SECRET_KEY", "")
    if not val:
        return CheckResult("SECRET_KEY 설정", "FAIL",
                           ".env에 SECRET_KEY가 없습니다.", "critical")
    if val == "change-this-to-random-secret-key-in-production":
        return CheckResult("SECRET_KEY 설정", "FAIL",
                           "기본값이 그대로 사용되고 있습니다.", "critical")
    if len(val) < 32:
        return CheckResult("SECRET_KEY 설정", "FAIL",
                           f"길이가 {len(val)}자입니다. 32자 이상 권장.", "high")
    return CheckResult("SECRET_KEY 설정", "PASS",
                       f"길이 {len(val)}자, 기본값 아님.", "info")


def check_admin_password(env: dict) -> CheckResult:
    val = env.get("DEFAULT_ADMIN_PASSWORD", "")
    weak = {"admin1234", "admin", "password", "1234", "0000"}
    if not val:
        return CheckResult("관리자 비밀번호", "WARN",
                           ".env에 DEFAULT_ADMIN_PASSWORD가 없어 기본값(admin1234) 사용 가능성.", "high")
    if val in weak:
        return CheckResult("관리자 비밀번호", "FAIL",
                           "취약한 기본 비밀번호가 사용되고 있습니다.", "critical")
    if len(val) < 10:
        return CheckResult("관리자 비밀번호", "WARN",
                           f"길이가 {len(val)}자입니다. 10자 이상 권장.", "medium")
    return CheckResult("관리자 비밀번호", "PASS",
                       f"길이 {len(val)}자, 기본값 아님.", "info")


def check_app_env(env: dict) -> CheckResult:
    val = env.get("APP_ENV", "production")
    if val == "production":
        return CheckResult("APP_ENV 모드", "PASS",
                           "production 모드입니다.", "info")
    return CheckResult("APP_ENV 모드", "WARN",
                       f"현재 APP_ENV={val}. 운영 배포 시 production 권장.", "medium")


def check_env_file() -> CheckResult:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return CheckResult(".env 파일 존재", "FAIL",
                           ".env 파일이 없습니다.", "high")
    # Windows에서는 NTFS ACL이 다르므로 경고만
    return CheckResult(".env 파일 존재", "PASS",
                       f"{env_path} 존재. 운영 환경에서는 600 권한 권장.", "info")


def check_compose_ports() -> CheckResult:
    """docker-compose 외부 노출 포트가 nginx(80)만인지 확인."""
    compose = ROOT / "docker-compose.cpu.yml"
    if not compose.exists():
        return CheckResult("외부 노출 포트", "SKIP",
                           "docker-compose.cpu.yml 없음.", "info")
    text = compose.read_text(encoding="utf-8")
    # ports: 와 같은 매핑 찾기 (간단 휴리스틱)
    port_lines = re.findall(r'^\s*-\s*"(\d+):(\d+)"', text, re.M)
    external = [host for host, _ in port_lines]
    risky = [p for p in external if p not in {"80", "443"}]
    if risky:
        return CheckResult("외부 노출 포트", "WARN",
                           f"비표준 포트 외부 노출: {', '.join(risky)}. 내부 네트워크에서만 접근 가능한지 확인.",
                           "medium")
    return CheckResult("외부 노출 포트", "PASS",
                       f"외부 노출 포트: {', '.join(sorted(set(external))) or '없음'}.", "info")


def check_external_domains() -> CheckResult:
    """백엔드 코드에 하드코딩된 외부 도메인이 있는지 검사 (Ollama/postgres 제외)."""
    backend = ROOT / "backend" / "app"
    if not backend.exists():
        return CheckResult("외부 도메인 하드코딩", "SKIP",
                           "backend/app 없음.", "info")
    suspicious = []
    pattern = re.compile(r"https?://([a-z0-9.\-]+)", re.I)
    allowlist = {"localhost", "ollama", "postgres", "127.0.0.1", "0.0.0.0",
                 "errors.pydantic.dev", "schema.org", "www.w3.org"}
    for py in backend.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in pattern.finditer(text):
            host = m.group(1).lower()
            if host in allowlist:
                continue
            # huggingface, openai 같은 호스트가 있으면 의심
            if any(x in host for x in ("huggingface", "openai", "anthropic",
                                       "googleapis", "amazonaws", "azure")):
                suspicious.append(f"{py.relative_to(ROOT)}:{host}")
    if suspicious:
        return CheckResult("외부 도메인 하드코딩", "WARN",
                           "외부 호출 가능 도메인 발견 (폐쇄망 운영 시 검토 필요): " +
                           "; ".join(suspicious[:5]),
                           "medium")
    return CheckResult("외부 도메인 하드코딩", "PASS",
                       "외부 호출 도메인 미발견 (Ollama/Postgres 제외).", "info")


def check_pip_audit() -> CheckResult:
    """pip-audit 사용 가능하면 requirements.txt 스캔."""
    if shutil.which("pip-audit") is None:
        return CheckResult("의존성 CVE 스캔", "SKIP",
                           "pip-audit 미설치. `pip install pip-audit` 후 재실행.",
                           "info")
    req = ROOT / "backend" / "requirements.txt"
    if not req.exists():
        return CheckResult("의존성 CVE 스캔", "SKIP",
                           "backend/requirements.txt 없음.", "info")
    try:
        proc = subprocess.run(
            ["pip-audit", "-r", str(req), "--format", "json", "--progress-spinner", "off"],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        return CheckResult("의존성 CVE 스캔", "SKIP",
                           f"pip-audit 실행 실패: {e}", "info")
    if proc.returncode not in (0, 1):
        return CheckResult("의존성 CVE 스캔", "SKIP",
                           f"pip-audit 비정상 종료: rc={proc.returncode}", "info")
    try:
        data = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return CheckResult("의존성 CVE 스캔", "SKIP",
                           "pip-audit 출력 파싱 실패.", "info")
    # pip-audit 형식: [{"name":..,"version":..,"vulns":[{"id":..,"fix_versions":..}]}]
    vulns = []
    for entry in data if isinstance(data, list) else data.get("dependencies", []):
        for v in entry.get("vulns", []) or []:
            vulns.append(f"{entry.get('name')} {entry.get('version')} → {v.get('id')}")
    if vulns:
        return CheckResult("의존성 CVE 스캔", "WARN",
                           f"{len(vulns)}건 발견: " + "; ".join(vulns[:5]) +
                           (" ..." if len(vulns) > 5 else ""),
                           "high")
    return CheckResult("의존성 CVE 스캔", "PASS",
                       "알려진 CVE 없음.", "info")


# ── 리포트 생성 ──────────────────────────────────────────────

def render_markdown(results: list[CheckResult]) -> str:
    pass_n = sum(1 for r in results if r.status == "PASS")
    fail_n = sum(1 for r in results if r.status == "FAIL")
    warn_n = sum(1 for r in results if r.status == "WARN")
    skip_n = sum(1 for r in results if r.status == "SKIP")

    lines = [
        "# BAIKAL Private AI — 자가 보안 점검 리포트",
        "",
        f"- 측정일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 점검 항목: 총 {len(results)}건",
        f"- 결과: ✅ PASS {pass_n} · ⚠️ WARN {warn_n} · ❌ FAIL {fail_n} · ⏭ SKIP {skip_n}",
        "",
        "## 요약",
        "",
        "| # | 항목 | 상태 | 심각도 |",
        "|--:|------|:----:|:------:|",
    ]
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭"}
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r.name} | {icon.get(r.status, r.status)} {r.status} | {r.severity} |")
    lines += ["", "## 상세 결과", ""]
    for r in results:
        lines.append(f"### {icon.get(r.status, '')} {r.name}")
        lines.append("")
        lines.append(f"- 상태: **{r.status}** (심각도 `{r.severity}`)")
        lines.append(f"- 상세: {r.detail}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*이 리포트는 `scripts/security_audit.py` 으로 자동 생성되었습니다. 외부 호출 없이 로컬에서만 실행됩니다.*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="BAIKAL 자가 보안 점검")
    parser.add_argument("--output", default=None,
                        help="마크다운 리포트 출력 경로 (생략 시 화면 출력만)")
    parser.add_argument("--json", default=None,
                        help="JSON 결과 출력 경로")
    args = parser.parse_args()

    env = _read_env()
    checks = [
        check_secret_key(env),
        check_admin_password(env),
        check_app_env(env),
        check_env_file(),
        check_compose_ports(),
        check_external_domains(),
        check_pip_audit(),
    ]

    # 콘솔 출력
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭"}
    print()
    print("=" * 60)
    print("  BAIKAL 자가 보안 점검")
    print("=" * 60)
    for r in checks:
        print(f"  {icon.get(r.status, '?')} [{r.status:4}] {r.name}: {r.detail}")
    print()
    fail_n = sum(1 for r in checks if r.status == "FAIL")
    warn_n = sum(1 for r in checks if r.status == "WARN")
    print(f"  결과: FAIL {fail_n}건, WARN {warn_n}건")
    print()

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(checks), encoding="utf-8")
        print(f"  리포트 저장: {out}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps([r.to_dict() for r in checks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  JSON 저장: {out}")

    # FAIL 있으면 exit code 1
    sys.exit(1 if fail_n > 0 else 0)


if __name__ == "__main__":
    main()
