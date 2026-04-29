# BAIKAL Private AI — 문서 인덱스

> 12개 핵심 문서로 정리되어 있습니다. 2026-04-29 통합 완료.

## 📘 고객 대상 (Customer-facing)

| 문서 | 용도 | 대상 독자 |
|---|---|---|
| [INTRODUCTION.md](INTRODUCTION.md) | 제품 한 장 소개 | 모든 독자 (입구 문서) |
| [PROPOSAL.md](PROPOSAL.md) | 정식 도입 제안서 | 고객 의사결정자 |
| [PERFORMANCE_ROADMAP.md](PERFORMANCE_ROADMAP.md) | 단계별 성능 향상 계획 (CPU→GPU) | 고객 IT 담당자 |
| [INSTALL_GUIDE_EASY.md](INSTALL_GUIDE_EASY.md) | 비개발자용 설치 가이드 | 도입 담당자 |
| [USER_MANUAL.md](USER_MANUAL.md) | 사용자 매뉴얼 | 일반 사용자 |
| [ADMIN_MANUAL.md](ADMIN_MANUAL.md) | 관리자 매뉴얼 | 시스템 관리자 |

## 📊 사업·전략 (Internal)

| 문서 | 용도 |
|---|---|
| [BUSINESS_PLAN.md](BUSINESS_PLAN.md) | 사업계획서 (부록 A: ISP 자료 통합) |
| [MARKETING_STRATEGY.md](MARKETING_STRATEGY.md) | 마케팅·시장 통합 전략 (4개 문서 통합) |

## 🔧 시연·검증 (Demo & QA)

| 문서 | 용도 |
|---|---|
| [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) | 시연 마스터 매뉴얼 (부록 A: 상세 가이드 통합) |
| [TEST_RESULTS.md](TEST_RESULTS.md) | RAG 평가 자동 산출 결과 |
| [SECURITY_AUDIT.md](SECURITY_AUDIT.md) | 보안 자가점검 자동 산출 결과 |

## 🛠️ 개발 내부 (Engineering)

| 문서 | 용도 |
|---|---|
| [DEVELOPMENT_NOTES.md](DEVELOPMENT_NOTES.md) | 개선 로드맵 + RAG 개선 이력 + 시스템 분석 (3개 문서 통합) |

## 🧮 기타 자료

- [roi_calculator.html](roi_calculator.html) — ROI 시뮬레이터 (브라우저용)

---

## 통합 이력 (2026-04-29)

다음 9개 문서가 위 통합본으로 흡수되어 삭제되었습니다 (git 이력으로 복구 가능):

| 삭제된 원본 | 통합 위치 |
|---|---|
| `GO_TO_MARKET_STRATEGY.md` | MARKETING_STRATEGY.md Part 1 |
| `VERTICAL_MARKETING.md` | MARKETING_STRATEGY.md Part 2 |
| `VERTICAL_MARKETING_ANALYSIS.md` | MARKETING_STRATEGY.md Part 3 |
| `ROADMAP_AND_MARKET.md` | MARKETING_STRATEGY.md Part 4 |
| `IMPROVEMENT_ROADMAP.md` | DEVELOPMENT_NOTES.md Part 1 |
| `RAG_IMPROVEMENT.md` | DEVELOPMENT_NOTES.md Part 2 |
| `ANALYSIS.md` | DEVELOPMENT_NOTES.md Part 3 |
| `ISP_IMPROVEMENT_PLAN.md` | BUSINESS_PLAN.md 부록 A-1 |
| `ISP_RESULTS.md` | BUSINESS_PLAN.md 부록 A-2 |
| `DEMO_GUIDE.md` | DEMO_RUNBOOK.md 부록 A-1 |
| `DEMO_PACKAGE.md` | DEMO_RUNBOOK.md 부록 A-2 |

> **복구 방법**: `git log --diff-filter=D -- docs/<파일명>`으로 마지막 커밋 확인 후
> `git checkout <commit>~1 -- docs/<파일명>`로 복원 가능합니다.
