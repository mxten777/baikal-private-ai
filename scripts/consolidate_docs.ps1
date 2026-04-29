# BAIKAL 문서 통합 스크립트 (B안)
# 마케팅 4개, 개발 3개를 통합본으로, ISP 2개·DEMO 2개는 부록으로 합침
# 원본은 별도 단계에서 git rm으로 제거

param([string]$DocsDir = "$PSScriptRoot\..\docs")
$ErrorActionPreference = 'Stop'
$utf8bom = New-Object System.Text.UTF8Encoding $true

function Get-FileText([string]$path) {
    Get-Content -Raw -Encoding UTF8 -Path $path
}
function Demote-H1([string]$text) {
    return ($text -replace '(?m)^# ', '## ')
}
function Write-Utf8Bom([string]$path, [string]$content) {
    [System.IO.File]::WriteAllText($path, $content, $utf8bom)
}

Push-Location $DocsDir
try {
    # ---- 1) MARKETING_STRATEGY.md (4개 통합) ----
    $marketingHeader = @'
# BAIKAL 마케팅·시장 통합 전략

> **최종 통합본** · 2026-04-29
> 본 문서는 다음 4개 문서를 통합한 단일 마케팅 전략 자료입니다.
> - GO_TO_MARKET_STRATEGY.md — Go-to-Market 전략
> - VERTICAL_MARKETING.md — 버티컬 시장 전략
> - VERTICAL_MARKETING_ANALYSIS.md — 버티컬 전략 냉정 분석
> - ROADMAP_AND_MARKET.md — 로드맵 및 시장 분석

---

## 목차

- [Part 1. Go-to-Market 전략](#part-1-go-to-market-전략)
- [Part 2. 버티컬 시장 전략](#part-2-버티컬-시장-전략)
- [Part 3. 버티컬 전략 냉정 분석](#part-3-버티컬-전략-냉정-분석)
- [Part 4. 로드맵 및 시장 분석](#part-4-로드맵-및-시장-분석)

---

# Part 1. Go-to-Market 전략

'@

    $body = $marketingHeader
    $body += Demote-H1 (Get-FileText 'GO_TO_MARKET_STRATEGY.md')
    $body += "`n`n---`n`n# Part 2. 버티컬 시장 전략`n`n"
    $body += Demote-H1 (Get-FileText 'VERTICAL_MARKETING.md')
    $body += "`n`n---`n`n# Part 3. 버티컬 전략 냉정 분석`n`n"
    $body += Demote-H1 (Get-FileText 'VERTICAL_MARKETING_ANALYSIS.md')
    $body += "`n`n---`n`n# Part 4. 로드맵 및 시장 분석`n`n"
    $body += Demote-H1 (Get-FileText 'ROADMAP_AND_MARKET.md')
    Write-Utf8Bom (Join-Path $PWD 'MARKETING_STRATEGY.md') $body
    Write-Host "[1/4] MARKETING_STRATEGY.md 생성"

    # ---- 2) DEVELOPMENT_NOTES.md (3개 통합) ----
    $devHeader = @'
# BAIKAL 개발 노트 (내부용)

> **최종 통합본** · 2026-04-29
> 본 문서는 다음 3개 개발 내부 문서를 통합한 자료입니다.
> - IMPROVEMENT_ROADMAP.md — 개선 로드맵
> - RAG_IMPROVEMENT.md — RAG 파이프라인 개선 이력
> - ANALYSIS.md — 시스템 분석

---

## 목차

- [Part 1. 개선 로드맵](#part-1-개선-로드맵)
- [Part 2. RAG 파이프라인 개선 이력](#part-2-rag-파이프라인-개선-이력)
- [Part 3. 시스템 분석](#part-3-시스템-분석)

---

# Part 1. 개선 로드맵

'@
    $body = $devHeader
    $body += Demote-H1 (Get-FileText 'IMPROVEMENT_ROADMAP.md')
    $body += "`n`n---`n`n# Part 2. RAG 파이프라인 개선 이력`n`n"
    $body += Demote-H1 (Get-FileText 'RAG_IMPROVEMENT.md')
    $body += "`n`n---`n`n# Part 3. 시스템 분석`n`n"
    $body += Demote-H1 (Get-FileText 'ANALYSIS.md')
    Write-Utf8Bom (Join-Path $PWD 'DEVELOPMENT_NOTES.md') $body
    Write-Host "[2/4] DEVELOPMENT_NOTES.md 생성"

    # ---- 3) BUSINESS_PLAN.md 부록: ISP 2개 ----
    $existingBP = Get-FileText 'BUSINESS_PLAN.md'
    $ispAppendix = @'


---

# 부록 A. ISP (정보화전략계획) 자료

> 2026-04-29 통합. 원본: ISP_IMPROVEMENT_PLAN.md, ISP_RESULTS.md

## 부록 A-1. ISP 개선 계획

'@
    $ispAppendix += Demote-H1 (Get-FileText 'ISP_IMPROVEMENT_PLAN.md')
    $ispAppendix += "`n`n---`n`n## 부록 A-2. ISP 수행 결과`n`n"
    $ispAppendix += Demote-H1 (Get-FileText 'ISP_RESULTS.md')
    Write-Utf8Bom (Join-Path $PWD 'BUSINESS_PLAN.md') ($existingBP + $ispAppendix)
    Write-Host "[3/4] BUSINESS_PLAN.md 부록 A 추가"

    # ---- 4) DEMO_RUNBOOK.md 부록: DEMO_GUIDE, DEMO_PACKAGE ----
    $existingDR = Get-FileText 'DEMO_RUNBOOK.md'
    $demoAppendix = @'


---

# 부록 A. 상세 시연 가이드

> 2026-04-29 통합. 원본: DEMO_GUIDE.md, DEMO_PACKAGE.md

## 부록 A-1. 시연 가이드 (구 DEMO_GUIDE)

'@
    $demoAppendix += Demote-H1 (Get-FileText 'DEMO_GUIDE.md')
    $demoAppendix += "`n`n---`n`n## 부록 A-2. 시연 패키지 구성 (구 DEMO_PACKAGE)`n`n"
    $demoAppendix += Demote-H1 (Get-FileText 'DEMO_PACKAGE.md')
    Write-Utf8Bom (Join-Path $PWD 'DEMO_RUNBOOK.md') ($existingDR + $demoAppendix)
    Write-Host "[4/4] DEMO_RUNBOOK.md 부록 A 추가"

    Write-Host ""
    Write-Host "✅ 통합 완료. 다음 단계: 원본 9개 파일 삭제."
}
finally {
    Pop-Location
}
