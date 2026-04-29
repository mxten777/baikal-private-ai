<#
.SYNOPSIS
  BAIKAL 시연 직전 워밍업 스크립트
.DESCRIPTION
  ① 컨테이너 상태 확인 ② 헬스체크 ③ LLM cold-start 워밍업 ④ 거절 동작 검증
  시연 5분 전에 1회 실행하면 첫 질의 지연 없음.
.EXAMPLE
  .\scripts\demo_warmup.ps1
  .\scripts\demo_warmup.ps1 -Username admin -Password 'Baikal@2026!'
#>
[CmdletBinding()]
param(
    [string]$ApiBase = "http://localhost/api",
    [string]$Username = "admin",
    [string]$Password = "Baikal@2026!",
    [switch]$SkipRefusalCheck
)

$ErrorActionPreference = "Stop"

function Write-Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Write-OK($msg)       { Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn2($msg)    { Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Fail($msg)     { Write-Host "  ❌ $msg" -ForegroundColor Red }

# ─────────────────────────────────────────────────────────────
Write-Step "1/5" "Docker 컨테이너 상태"
$containers = @("baikal-postgres","baikal-ollama","baikal-backend","baikal-frontend","baikal-nginx")
$running = docker ps --format "{{.Names}}" 2>$null
$missing = @()
foreach ($c in $containers) {
    if ($running -contains $c) { Write-OK $c } else { Write-Fail "$c 미기동"; $missing += $c }
}
if ($missing.Count -gt 0) {
    Write-Warn2 "기동 시도: docker compose -f docker-compose.cpu.yml up -d"
    docker compose -f docker-compose.cpu.yml up -d | Out-Null
    Start-Sleep -Seconds 15
}

# ─────────────────────────────────────────────────────────────
Write-Step "2/5" "API 헬스체크"
try {
    $health = Invoke-RestMethod "$ApiBase/health" -TimeoutSec 10
    if ($health.status -eq "ok") {
        Write-OK "status=ok, db=$($health.components.database), ollama=$($health.components.ollama)"
    } else {
        Write-Fail "status=$($health.status)"; exit 1
    }
} catch {
    Write-Fail "헬스체크 실패: $_"; exit 1
}

# ─────────────────────────────────────────────────────────────
Write-Step "3/5" "관리자 로그인"
try {
    $loginBody = @{ username = $Username; password = $Password } | ConvertTo-Json
    $null = Invoke-WebRequest "$ApiBase/auth/login" -Method Post `
        -ContentType "application/json" -Body $loginBody -TimeoutSec 10 -SessionVariable webSession
    $cookie = $webSession.Cookies.GetCookies($ApiBase) | Where-Object { $_.Name -eq "access_token" }
    if (-not $cookie -or -not $cookie.Value) { throw "access_token 쿠키 없음" }
    Write-OK "쿠키 세션 획득 (token len=$($cookie.Value.Length))"
} catch {
    Write-Fail "로그인 실패: $_"; exit 1
}

# ─────────────────────────────────────────────────────────────
Write-Step "4/5" "LLM cold-start 워밍업 (30~60초 소요)"
$chatSession = Invoke-RestMethod "$ApiBase/chat/sessions" -Method Post `
    -WebSession $webSession -ContentType "application/json" `
    -Body (@{ title = "_warmup" } | ConvertTo-Json) -TimeoutSec 10
$sessionId = $chatSession.id
Write-Host "  → 세션 생성: $sessionId" -ForegroundColor DarkGray

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$ask = @{ session_id = $sessionId; question = "안녕하세요, 테스트입니다." } | ConvertTo-Json
try {
    $resp = Invoke-RestMethod "$ApiBase/chat/ask" -Method Post `
        -WebSession $webSession -ContentType "application/json" -Body $ask -TimeoutSec 180
    $sw.Stop()
    Write-OK ("워밍업 완료 — {0:N1}초" -f $sw.Elapsed.TotalSeconds)
    if ($resp.refusal_reason) {
        Write-Host "  (테스트 질문이 거절됨: $($resp.refusal_reason) — 정상)" -ForegroundColor DarkGray
    }
} catch {
    Write-Fail "워밍업 실패: $_"; exit 1
}

# 세션 정리
try {
    Invoke-RestMethod "$ApiBase/chat/sessions/$sessionId" -Method Delete -WebSession $webSession -TimeoutSec 10 | Out-Null
} catch {}

# ─────────────────────────────────────────────────────────────
Write-Step "5/5" "거절 동작 사전 검증"
if ($SkipRefusalCheck) {
    Write-Warn2 "건너뜀 (--SkipRefusalCheck)"
} else {
    $session2 = Invoke-RestMethod "$ApiBase/chat/sessions" -Method Post `
        -WebSession $webSession -ContentType "application/json" `
        -Body (@{ title = "_refusal_test" } | ConvertTo-Json) -TimeoutSec 10
    $ask2 = @{ session_id = $session2.id; question = "다음 분기 매출 예상치를 알려주세요" } | ConvertTo-Json
    try {
        $r2 = Invoke-RestMethod "$ApiBase/chat/ask" -Method Post `
            -WebSession $webSession -ContentType "application/json" -Body $ask2 -TimeoutSec 60
        if ($r2.refusal_reason) {
            Write-OK "거절 동작 확인 — reason=$($r2.refusal_reason)"
        } else {
            Write-Warn2 "거절되지 않음 — 임계값 또는 색인된 문서 확인 필요"
        }
    } catch {
        Write-Warn2 "거절 검증 스킵: $_"
    }
    try {
        Invoke-RestMethod "$ApiBase/chat/sessions/$($session2.id)" -Method Delete -WebSession $webSession | Out-Null
    } catch {}
}

# ─────────────────────────────────────────────────────────────
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  🚀 시연 준비 완료. 브라우저에서 http://localhost 접속하세요." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Green
