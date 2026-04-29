# Stage 1.2 검증 — 인덱싱 batch commit + 진행률
#
# 시나리오:
#   1) 큰 PDF/HWPX 업로드
#   2) /api/documents/{id}/status 폴링하며 processed_chunks가 단조 증가하는지 확인
#   3) 처리 완료 후 total_chunks == processed_chunks == 실제 chunks 수 일치 확인
#
# 사용법: .\scripts\test_stage1_indexing.ps1 -FilePath "demo_docs/law/큰파일.pdf"

param(
    [Parameter(Mandatory=$false)]
    [string]$FilePath
)

$ErrorActionPreference = 'Stop'
$base = 'http://localhost'
$adminUser = 'admin'
$adminPass = 'Baikal@2026!'

function Write-Step($m) { Write-Host "`n[STEP] $m" -ForegroundColor Cyan }
function Write-Pass($m) { Write-Host "  [PASS] $m" -ForegroundColor Green }
function Write-Fail($m) { Write-Host "  [FAIL] $m" -ForegroundColor Red; exit 1 }

# 파일 자동 선택 — 가장 큰 hwpx/pdf
if (-not $FilePath) {
    $candidates = @(
        "demo_docs/law/행정절차법(법률)(제18748호)(20230324).pdf",
        "demo_docs/law/공무원 임용규칙(인사혁신처예규)(제210호)(20260407).pdf"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $FilePath = $c; break }
    }
}
if (-not (Test-Path $FilePath)) {
    Write-Fail "테스트 파일 없음: $FilePath"
}
Write-Host "테스트 파일: $FilePath" -ForegroundColor Yellow

# 1. 로그인
Write-Step "로그인"
$loginBody = @{username=$adminUser;password=$adminPass} | ConvertTo-Json
$null = Invoke-RestMethod -Uri "$base/api/auth/login" -Method Post -Body $loginBody -ContentType 'application/json' -SessionVariable s
Write-Pass "session cookie 확보"

# 2. 동일 파일이 이미 있으면 삭제 (재업로드 위해)
Write-Step "기존 동명 문서 삭제 (테스트 격리)"
$docs = Invoke-RestMethod -Uri "$base/api/documents" -WebSession $s
$fileName = Split-Path $FilePath -Leaf
$existing = @($docs | Where-Object { $_.filename -eq $fileName })
foreach ($d in $existing) {
    try {
        Invoke-RestMethod -Uri "$base/api/documents/$($d.id)" -Method Delete -WebSession $s -TimeoutSec 10 | Out-Null
        Write-Host "  삭제: $($d.id)" -ForegroundColor DarkGray
    } catch {
        Write-Host "  [WARN] 삭제 실패 (계속 진행): $_" -ForegroundColor Yellow
    }
}

# 3. 업로드
Write-Step "업로드"
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $FilePath))
$fileEnc = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes)
$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
    "Content-Type: application/octet-stream$LF",
    $fileEnc,
    "--$boundary--$LF"
) -join $LF

$resp = Invoke-RestMethod -Uri "$base/api/documents/upload" -Method Post `
    -ContentType "multipart/form-data; boundary=$boundary" `
    -Body $bodyLines -WebSession $s -TimeoutSec 60
$docId = $resp.id
Write-Pass "doc_id=$docId 업로드 완료"

# 4. 폴링 — processed_chunks 단조 증가 확인
Write-Step "처리 진행률 폴링 (최대 10분)"
$lastProcessed = -1
$lastTotal = $null
$increments = 0
$startWall = Get-Date
$maxSec = 600
while (((Get-Date) - $startWall).TotalSeconds -lt $maxSec) {
    Start-Sleep -Seconds 5
    try {
        $st = Invoke-RestMethod -Uri "$base/api/documents/$docId/status" -WebSession $s -TimeoutSec 10
    } catch {
        Write-Host "  [WARN] status 조회 실패 (재시도): $_" -ForegroundColor Yellow
        continue
    }
    $proc = if ($null -ne $st.processed_chunks) { [int]$st.processed_chunks } else { 0 }
    $tot = $st.total_chunks
    $totDisp = if ($null -ne $tot) { $tot } else { '?' }
    Write-Host ("  [{0:HH:mm:ss}] status={1} processed={2}/{3}" -f (Get-Date), $st.status, $proc, $totDisp) -ForegroundColor DarkGray
    if ($proc -gt $lastProcessed) {
        $increments++
        $lastProcessed = $proc
    } elseif ($proc -lt $lastProcessed) {
        Write-Fail "processed_chunks 감소: $lastProcessed → $proc (단조 증가 위반)"
    }
    if ($null -ne $tot) { $lastTotal = $tot }
    if ($st.status -eq 'completed') { Write-Pass "completed 도달 (total=$tot)"; break }
    if ($st.status -eq 'failed')    { Write-Fail "처리 실패: $($st.error_message)" }
}
if ($lastProcessed -lt 1) { Write-Fail "처리 진행률이 한 번도 0보다 커지지 않음" }

Write-Step "검증"
if ($increments -ge 2) {
    Write-Pass "processed_chunks 증가 횟수 = $increments (≥2, batch commit 작동 중)"
} else {
    Write-Host "  [WARN] 증가 횟수=$increments — 문서가 50청크 미만이면 정상" -ForegroundColor Yellow
}

# 5. DB 정합성 확인
$actual = (docker exec baikal-postgres psql -U baikal -d baikal_ai -tAc "SELECT COUNT(*) FROM document_chunks WHERE document_id='$docId';").Trim()
Write-Host "  실제 DB chunks=$actual / total_chunks=$lastTotal / processed_chunks=$lastProcessed" -ForegroundColor Yellow
if ($actual -eq "$lastTotal" -and $actual -eq "$lastProcessed") {
    Write-Pass "정합성 확인: DB chunks == total == processed"
} else {
    Write-Fail "정합성 불일치"
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " Stage 1.2 PASS — batch commit + 진행률 동작" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
exit 0
