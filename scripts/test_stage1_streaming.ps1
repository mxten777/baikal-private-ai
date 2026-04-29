# Stage 1.1 회귀 테스트 — 스트리밍 단절 시 DB 보존
#
# 시나리오:
#   1) 로그인 → 세션 생성
#   2) /api/chat/ask/stream 호출 시작
#   3) 첫 토큰 수신 후 즉시 연결 끊기 (사용자가 페이지 이동한 상황)
#   4) /api/chat/sessions/{id}/messages 조회
#   5) user 질문이 DB에 남아있어야 통과 (FAIL이면 패치 회귀)
#
# 실행: .\scripts\test_stage1_streaming.ps1

$ErrorActionPreference = 'Stop'
$base = 'http://localhost'
$adminUser = 'admin'
$adminPass = 'Baikal@2026!'
$testQuestion = "[STAGE1 TEST $(Get-Date -Format 'HHmmss')] 행정처분 사전통지의 예외 사유는?"

function Write-Step($msg) { Write-Host "`n[STEP] $msg" -ForegroundColor Cyan }
function Write-Pass($msg) { Write-Host "  [PASS] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red; exit 1 }

# 1. 로그인
Write-Step "로그인"
$loginBody = @{username=$adminUser;password=$adminPass} | ConvertTo-Json
$null = Invoke-RestMethod -Uri "$base/api/auth/login" -Method Post -Body $loginBody -ContentType 'application/json' -SessionVariable s
Write-Pass "session cookie 확보"

# 2. 새 세션 생성
Write-Step "테스트용 세션 생성"
$sess = Invoke-RestMethod -Uri "$base/api/chat/sessions" -Method Post -Body (@{title="STAGE1 TEST"} | ConvertTo-Json) -ContentType 'application/json' -WebSession $s
$sessionId = $sess.id
Write-Pass "session_id=$sessionId"

# 3. 스트리밍 시작 → 첫 청크 수신 후 즉시 단절
Write-Step "스트리밍 시작 후 의도적 단절 (시연 중 페이지 이동 시뮬레이션)"
$cookieHeader = ($s.Cookies.GetCookies("$base/") | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join '; '
$askBody = @{ session_id=$sessionId; question=$testQuestion } | ConvertTo-Json
$req = [System.Net.HttpWebRequest]::Create("$base/api/chat/ask/stream")
$req.Method = 'POST'
$req.ContentType = 'application/json'
$req.Headers.Add('Cookie', $cookieHeader)
$req.Timeout = 60000
$req.ReadWriteTimeout = 60000

$bytes = [System.Text.Encoding]::UTF8.GetBytes($askBody)
$req.ContentLength = $bytes.Length
$reqStream = $req.GetRequestStream()
$reqStream.Write($bytes, 0, $bytes.Length)
$reqStream.Close()

try {
    $resp = $req.GetResponse()
    $rs = $resp.GetResponseStream()
    $buf = New-Object byte[] 4096
    $totalRead = 0
    $chunksRead = 0
    $sawSourcesEvent = $false
    $sawTokenEvent = $false
    $allText = ''
    $deadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $deadline) {
        $n = $rs.Read($buf, 0, $buf.Length)
        if ($n -le 0) { break }
        $totalRead += $n
        $chunksRead++
        $text = [System.Text.Encoding]::UTF8.GetString($buf, 0, $n)
        $allText += $text
        if ($text -match '"type"\s*:\s*"sources"') { $sawSourcesEvent = $true }
        if ($text -match '"type"\s*:\s*"token"')   { $sawTokenEvent   = $true }
        # 진짜 token 이벤트가 보이면 즉시 단절
        if ($sawTokenEvent) { break }
    }
    Write-Pass "수신 chunks=$chunksRead bytes=$totalRead sources=$sawSourcesEvent token=$sawTokenEvent"
    Write-Host "  [DEBUG] first 300 chars: $($allText.Substring(0, [Math]::Min(300, $allText.Length)))" -ForegroundColor DarkGray
    $rs.Close(); $resp.Close()
} catch {
    Write-Host "  [WARN] 스트리밍 단절 중 예외: $_" -ForegroundColor Yellow
}

if (-not $sawTokenEvent) {
    Write-Host "  [WARN] 토큰을 받기 전 종료 (Confidence Gate 거절일 수 있음)" -ForegroundColor Yellow
}

# 4. 짧게 대기 (백엔드 finally 핸들러가 commit 마치도록)
Start-Sleep -Seconds 2

# 5. DB 검증 — user 질문이 저장되었는가?
Write-Step "DB 검증: user 메시지 존재 확인"
$msgs = Invoke-RestMethod -Uri "$base/api/chat/sessions/$sessionId/messages" -WebSession $s
$userMsgs = @($msgs | Where-Object { $_.role -eq 'user' })
$assistantMsgs = @($msgs | Where-Object { $_.role -eq 'assistant' })

Write-Host "  user msgs: $($userMsgs.Count) / assistant msgs: $($assistantMsgs.Count)"
if ($userMsgs.Count -ge 1 -and $userMsgs[0].content -eq $testQuestion) {
    Write-Pass "user 질문이 DB에 저장됨"
} else {
    Write-Fail "user 질문이 DB에 없음 (스트리밍 단절 시 데이터 유실 — Stage 1.1 회귀)"
}

if ($assistantMsgs.Count -ge 1) {
    $partial = $assistantMsgs[0].content
    if ($partial -and $partial.Length -gt 0) {
        Write-Pass "assistant 부분 답변도 저장됨 (길이=$($partial.Length))"
    } else {
        Write-Host "  [INFO] assistant 행은 있으나 본문 비어있음 (단절 시점이 너무 빨랐음 — 허용)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [INFO] assistant 행 없음 — 단절 시점이 LLM 호출 전" -ForegroundColor Yellow
}

# 6. 정리 (best-effort, 서버에서 LLM이 끝날 때까지 기다리지 않음)
Write-Step "테스트 세션 정리 (best-effort)"
try {
    Invoke-RestMethod -Uri "$base/api/chat/sessions/$sessionId" -Method Delete -WebSession $s -TimeoutSec 5 | Out-Null
    Write-Pass "세션 삭제 완료"
} catch {
    Write-Host "  [INFO] 세션 삭제 타임아웃/실패 — 서버에서 LLM 스트리밍이 진행 중일 수 있음 (테스트 결과에는 영향 없음)" -ForegroundColor Yellow
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " Stage 1.1 PASS — 스트리밍 단절 시 데이터 보존" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
exit 0
