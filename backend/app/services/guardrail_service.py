"""
P3-1: Guardrail Engine — 비관련/유해 질문 선제 차단 레이어
rag_service.py의 _build_rag_context 앞단에서 호출됨.

차단 기준:
  1. 개인정보 추출 시도 (주민번호, 비밀번호, 카드번호 등)
  2. 유해/불법 콘텐츠 요청 (폭발물, 해킹, 음란물 등)
  3. 프롬프트 인젝션 시도 (시스템 프롬프트 무시/변경 요청)
  4. 시스템 자체 공격 질의 (DB 쿼리, 파일 경로 노출 등)

완전 차단 대신 경고 우선 방침:
  - BLOCK  : 즉시 차단, 응답 거부
  - WARN   : 사용자에게 경고 후 처리 가능 (현재는 차단과 동일하게 처리)
  - ALLOW  : 정상 처리
"""
import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger("baikal.guardrail")


class PolicyAction(str, Enum):
    BLOCK = "BLOCK"
    WARN  = "WARN"
    ALLOW = "ALLOW"


@dataclass
class GuardrailResult:
    action: PolicyAction
    category: Optional[str] = None
    reason: Optional[str] = None
    safe_message: Optional[str] = None  # 사용자에게 반환할 메시지


# ── 차단 패턴 정의 ─────────────────────────────────────────────

_BLOCK_PATTERNS = [
    # 개인정보 추출 시도
    (r"주민\s*등록\s*번호|주민.{0,5}번호|ssn|social.security",
     "pii_extraction", "개인정보(주민등록번호) 추출 시도"),
    (r"비밀번호.{0,10}(알려|가르쳐|뽑아|추출|조회)|password.{0,10}(extract|dump|show)",
     "pii_extraction", "비밀번호 추출 시도"),
    (r"카드.{0,5}번호|card.number|신용카드.{0,10}번호",
     "pii_extraction", "금융정보 추출 시도"),

    # 프롬프트 인젝션
    (r"ignore.{0,20}(previous|above|system)|시스템.{0,10}(무시|프롬프트).{0,10}(변경|벗어|탈출)",
     "prompt_injection", "시스템 프롬프트 조작 시도"),
    (r"(act as|pretend|역할극|롤플레이).{0,20}(no restriction|제한 없|unrestricted)",
     "prompt_injection", "Role-play 제한 우회 시도"),
    (r"(DAN|jailbreak|탈옥).{0,30}(mode|모드|활성)",
     "prompt_injection", "Jailbreak 시도"),
    (r"you are now|이제 너는|앞으로 너는.{0,20}(restriction|제한|규칙).{0,10}(없|free|무시)",
     "prompt_injection", "프롬프트 인젝션"),

    # 유해 콘텐츠
    (r"폭발물|폭탄.{0,10}(만들|만드|제조|설치)|bomb.{0,10}(make|build|how to)",
     "harmful_content", "폭발물 제조 요청"),
    (r"해킹.{0,10}(방법|코드|스크립트|취약)|hacking.{0,10}(tutorial|exploit|script)",
     "harmful_content", "해킹 방법 요청"),
    (r"(랜섬웨어|악성코드|malware|ransomware).{0,10}(코드|소스|작성|만들)",
     "harmful_content", "악성코드 작성 요청"),
    (r"마약.{0,10}(제조|구매|합성)|drug.{0,10}(synthesis|manufacture|buy)",
     "harmful_content", "마약 관련 요청"),

    # 시스템 공격
    (r"(SELECT|INSERT|UPDATE|DELETE|DROP|TRUNCATE).{0,30}(FROM|INTO|TABLE|WHERE)",
     "system_attack", "SQL 인젝션 패턴"),
    (r"(\.\./){2,}|path.traversal|디렉토리.{0,5}탈출",
     "system_attack", "경로 순회 공격 시도"),
    (r"<script.{0,50}>|javascript:|onerror\s*=|onload\s*=",
     "system_attack", "XSS 패턴"),
]

_WARN_PATTERNS = [
    # 경쟁사 비교 또는 민감한 내부 정보 유출 시도
    (r"(내부|기밀|비공개|confidential).{0,10}(문서|정보|데이터).{0,10}(전부|모두|리스트|목록)",
     "sensitive_info", "내부 기밀 전체 열람 시도"),
    (r"다른 사용자|other user|타 사용자.{0,10}(문서|접근|정보)",
     "access_violation", "타 사용자 정보 접근 시도"),
]

# 컴파일된 정규식 캐시
_COMPILED_BLOCK = [(re.compile(pat, re.I | re.S), cat, reason)
                   for pat, cat, reason in _BLOCK_PATTERNS]
_COMPILED_WARN  = [(re.compile(pat, re.I | re.S), cat, reason)
                   for pat, cat, reason in _WARN_PATTERNS]

_SAFE_MESSAGES = {
    "pii_extraction": "개인정보 추출 요청은 처리할 수 없습니다. 업로드된 문서 기반 질문을 이용해주세요.",
    "prompt_injection": "시스템 규칙 변경 요청은 처리할 수 없습니다.",
    "harmful_content": "유해하거나 불법적인 내용에 대한 요청은 처리할 수 없습니다.",
    "system_attack": "비정상적인 요청이 감지되었습니다.",
    "sensitive_info": "내부 기밀 정보 전체 열람 요청은 허용되지 않습니다.",
    "access_violation": "다른 사용자의 정보에 접근하는 것은 허용되지 않습니다.",
}

# ── 핵심 함수 ──────────────────────────────────────────────────

def check_guardrail(question: str, user_id: str = "") -> GuardrailResult:
    """질문을 정책 엔진으로 검사.
    반환: GuardrailResult (action=BLOCK이면 rag_service에서 즉시 차단)
    """
    # 연속 공백 정규화 (패턴 우회 방지)
    normalized = " ".join(question.split())

    for pattern, category, reason in _COMPILED_BLOCK:
        if pattern.search(normalized):
            logger.warning(
                f"Guardrail BLOCK | user={user_id} | category={category} | "
                f"reason={reason} | query={question[:80]}"
            )
            return GuardrailResult(
                action=PolicyAction.BLOCK,
                category=category,
                reason=reason,
                safe_message=_SAFE_MESSAGES.get(category, "이 질문은 처리할 수 없습니다."),
            )

    for pattern, category, reason in _COMPILED_WARN:
        if pattern.search(normalized):
            logger.warning(
                f"Guardrail WARN | user={user_id} | category={category} | "
                f"reason={reason} | query={question[:80]}"
            )
            return GuardrailResult(
                action=PolicyAction.WARN,
                category=category,
                reason=reason,
                safe_message=_SAFE_MESSAGES.get(category, "주의가 필요한 요청입니다."),
            )

    return GuardrailResult(action=PolicyAction.ALLOW)
