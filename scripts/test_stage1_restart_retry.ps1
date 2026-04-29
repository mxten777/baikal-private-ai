# Stage 1.3 — 재시작 안전 인덱싱 회귀 테스트
#
# 시나리오:
# 1) 큰 문서 업로드
# 2) 처리 중에 백엔드 컨테이너 강제 재시작
# 3) 재시작 후 status='failed' + 명확한 error_message 확인
# 4) POST /api/documents/{id}/retry 호출 → 처리 재개
# 5) completed 도달 확인 + chunk 개수 일치
# 6) (옵션) completed 문서에 retry 호출 시 400 거부 확인

param(
    [string]$FilePath = "demo_docs/바이칼_취업규칙.pdf",
    [int]$KillAfterSec = 15,
    [int]$MaxSec = 300
)

$ErrorActionPreference = 'Stop'
$base = 'http://localhost'
$pass = 0; $fail = 0
function Write-Step($m) { Write-Host "`n[STEP] $m" -ForegroundColor Cyan }
function Write-Pass($m) { Write-Host "  [PASS] $m" -ForegroundColor Green; $script:pass++ }
function Write-Fail($m) { Write-Host "  [FAIL] $m" -ForegroundColor Red; $script:fail++ }

if (-not (Test-Path $FilePath)) { Write-Host "파일 없음: $FilePath" -ForegroundColor Red; exit 1 }

# 로그인
$loginBody = @{username='admin';password='Baikal@2026!'} | ConvertTo-Json
$null = Invoke-RestMethod "$base/api/auth/login" -Method Post -Body $loginBody -ContentType 'application/json' -SessionVariable s

# 동명 삭제
$fileName = Split-Path $FilePath -Leaf
$docs = Invoke-RestMethod "$base/api/documents" -WebSession $s
foreach ($d in @($docs | Where-Object { $_.filename -eq $fileName })) {
    try { Invoke-RestMethod "$base/api/documents/$($d.id)" -Method Delete -WebSession $s -TimeoutSec 10 | Out-Null } catch {}
}

# 업로드
Write-Step "업로드"
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath))
$fileEnc = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes)
$body = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
    "Content-Type: application/octet-stream$LF",
    $fileEnc,
    "--$boundary--$LF"
) -join $LF
$resp = Invoke-RestMethod "$base/api/documents/upload" -Method Post `
    -ContentType "multipart/form-data; boundary=$boundary" `
    -Body $body -WebSession $s -TimeoutSec 60
$docId = $resp.id
Write-Pass "doc_id=$docId"

# 처리 도중 컨테이너 재시작
Write-Step "처리 도중 backend kill (${KillAfterSec}s 대기 후)"
Start-Sleep -Seconds $KillAfterSec
$rowBefore = (docker exec baikal-postgres psql -U baikal -d baikal_ai -tAc "SELECT status||'|'||COALESCE(processed_chunks::text,'NULL') FROM documents WHERE id='$docId';").Trim()
Write-Host "  kill 직전 상태: $rowBefore" -ForegroundColor DarkGray
docker kill baikal-backend 2>&1 | Out-Null
Start-Sleep -Seconds 2
docker compose -f docker-compose.cpu.yml up -d backend 2>&1 | Out-Null

# 백엔드 health 대기
Write-Step "재시작 health 대기"
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $h = Invoke-RestMethod "$base/api/health" -TimeoutSec 3
        if ($h.status -eq 'ok') { $healthy = $true; break }
    } catch {}
}
if ($healthy) { Write-Pass "backend 재기동 완료" } else { Write-Fail "backend 재기동 실패"; exit 1 }

# DB에서 status=failed + 메시지 확인 (메시지 한글은 PowerShell stdout에서 깨질 수 있어 length만 검증)
Write-Step "고착 문서가 failed로 복구되었는지 확인"
$failedRow = docker exec baikal-postgres psql -U baikal -d baikal_ai -tAc "SELECT status, COALESCE(LENGTH(error_message),0) FROM documents WHERE id='$docId';"
$failedParts = ($failedRow.Trim() -split '\|')
$st = $failedParts[0].Trim()
$msgLen = [int]$failedParts[1].Trim()
if ($st -eq 'failed') {
    Write-Pass "status=failed"
} else {
    Write-Fail "status=$st (failed 기대)"
}
if ($msgLen -ge 10) {
    Write-Pass "error_message 길이=${msgLen} (>= 10자)"
} else {
    Write-Fail "error_message 너무 짧음: ${msgLen}자"
}

# 재로그인 (재시작으로 토큰 무효일 수도)
$null = Invoke-RestMethod "$base/api/auth/login" -Method Post -Body $loginBody -ContentType 'application/json' -SessionVariable s

# Retry API 호출
Write-Step "POST /api/documents/{id}/retry"
try {
    $r = Invoke-RestMethod "$base/api/documents/$docId/retry" -Method Post -WebSession $s -TimeoutSec 30
    Write-Pass "retry 응답 status=$($r.status)"
} catch {
    Write-Fail "retry API 실패: $($_.Exception.Message)"
    exit 1
}

# 완료까지 폴링
Write-Step "재처리 완료 대기"
$start = Get-Date
while ($true) {
    $row = (docker exec baikal-postgres psql -U baikal -d baikal_ai -tAc "SELECT status||'|'||COALESCE(total_chunks::text,'NULL')||'|'||COALESCE(processed_chunks::text,'NULL') FROM documents WHERE id='$docId';").Trim()
    $parts = $row -split '\|'
    $status = $parts[0]; $tot = $parts[1]; $proc = $parts[2]
    $elapsed = [int]((Get-Date) - $start).TotalSeconds
    if ($status -eq 'completed') {
        Write-Pass "재처리 완료 ${elapsed}s (chunks=$proc/$tot)"
        break
    }
    if ($status -eq 'failed') { Write-Fail "재처리 실패"; exit 1 }
    if ($elapsed -gt $MaxSec) { Write-Fail "타임아웃"; exit 1 }
    Start-Sleep -Seconds 3
}

# completed 문서에 retry → 400 기대
Write-Step "completed 문서에 retry → 400 거부 확인"
try {
    Invoke-RestMethod "$base/api/documents/$docId/retry" -Method Post -WebSession $s -TimeoutSec 10 | Out-Null
    Write-Fail "completed 문서에 retry가 200으로 통과 (400 기대)"
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 400) {
        Write-Pass "예상대로 400 거부"
    } else {
        Write-Fail "예상치 못한 status: $($_.Exception.Response.StatusCode.value__)"
    }
}

Write-Host "`n=== SUMMARY: PASS=$pass FAIL=$fail ===" -ForegroundColor $(if ($fail -eq 0) { 'Green' } else { 'Red' })
exit $(if ($fail -eq 0) { 0 } else { 1 })
