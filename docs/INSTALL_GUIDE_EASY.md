# BAIKAL Private AI — 설치 가이드 (비개발자용)

> **대상**: IT 비전공자, 담당 공무원, 총무·기획팀 직원  
> **소요 시간**: 초기 설치 약 30~40분 (이후 재시작은 1분)  
> **필요 사항**: Windows 10/11 PC, 인터넷 연결 (설치 중만 필요), 저장 공간 20GB 이상

---

## 📋 설치 순서 한눈에 보기

```
1단계  Docker Desktop 설치     (10분)
   ↓
2단계  BAIKAL 파일 준비         (2분)
   ↓
3단계  서비스 시작              (5분)
   ↓
4단계  AI 모델 다운로드         (10~20분, 기다리기만 하면 됨)
   ↓
5단계  접속 확인                (1분)
   ↓
✅ 완료 — 이후 재시작은 명령어 1줄
```

---

## 1단계 — Docker Desktop 설치

> Docker는 BAIKAL이 작동하는 데 필요한 실행 환경입니다.  
> 한 번만 설치하면 이후에는 필요 없습니다.

### 1-1. Docker Desktop 다운로드

1. 웹 브라우저(Chrome/Edge)에서 아래 주소로 이동합니다  
   → `https://www.docker.com/products/docker-desktop/`

2. **"Download for Windows"** 버튼을 클릭합니다

3. 파일이 다운로드되면 실행합니다 (파일명: `Docker Desktop Installer.exe`)

### 1-2. 설치 진행

1. 설치 화면에서 **"OK"** 또는 **"다음"** 을 계속 클릭합니다
2. 설치 완료 후 **PC를 재시작**합니다 (중요!)

### 1-3. 설치 확인

재시작 후 화면 우하단 시스템 트레이(시계 옆)에서 고래 아이콘🐳을 확인합니다.

| 아이콘 색상 | 상태 |
|-----------|------|
| 🟢 초록색 | 준비 완료 ✅ |
| 🟡 노란색/회색 | 아직 시작 중, 잠시 기다리세요 |
| 🔴 빨간색 | 오류 → [7단계 트러블슈팅](#7단계--문제-해결) 참고 |

> **초록색이 될 때까지 기다린 후 다음 단계로 넘어가세요.**

---

## 2단계 — BAIKAL 파일 준비

> 관리자로부터 받은 BAIKAL 설치 파일을 PC에 배치합니다.

### 방법 A — USB/파일로 받은 경우 (폐쇄망)

1. USB를 PC에 연결합니다
2. USB 안의 `baikal-private-ai` 폴더를 `C:\baikal777\` 위치에 복사합니다
3. 복사 완료 후 경로가 `C:\baikal777\baikal-private-ai\` 인지 확인합니다

### 방법 B — 인터넷으로 받는 경우

관리자가 제공한 다운로드 링크에서 ZIP 파일을 받아 `C:\baikal777\` 에 압축 해제합니다.

---

## 3단계 — 서비스 시작

### 3-1. PowerShell 열기

**방법 1** (권장):  
키보드에서 `Windows 키 + X` 를 누르고 **"Windows PowerShell"** 또는 **"터미널"** 을 클릭합니다

**방법 2**:  
화면 하단 검색창에 `powershell` 을 입력하고 엔터를 누릅니다

### 3-2. BAIKAL 폴더로 이동

검은 화면(PowerShell)에 아래 명령어를 입력하고 엔터를 누릅니다:

```
cd C:\baikal777\baikal-private-ai
```

### 3-3. 서비스 시작 명령어 실행

아래 명령어를 입력하고 엔터를 누릅니다:

```
docker compose -f docker-compose.cpu.yml up -d
```

> 처음 실행하면 필요한 파일을 자동으로 다운로드합니다 (약 2~5분 소요).

### 3-4. 완료 확인

아래와 같이 5개의 ✔ 표시가 나오면 성공입니다:

```
✔ Container baikal-postgres   Started
✔ Container baikal-ollama     Started
✔ Container baikal-backend    Started
✔ Container baikal-frontend   Started
✔ Container baikal-nginx      Started
```

---

## 4단계 — AI 모델 다운로드

> AI가 사용하는 언어 모델을 다운로드합니다. **처음 한 번만** 하면 됩니다.  
> 이후 재시작할 때는 이 단계를 건너뜁니다.

### 4-1. 언어 모델 다운로드 (약 5GB, 10~15분)

PowerShell에서 아래 명령어를 입력합니다:

```
docker exec baikal-ollama ollama pull qwen2.5:7b
```

다운로드 진행 상황이 표시됩니다. 100%가 될 때까지 기다립니다.

### 4-2. 임베딩 모델 다운로드 (약 1.2GB, 3~5분)

```
docker exec baikal-ollama ollama pull bge-m3
```

### 4-3. 모델 설치 확인

```
docker exec baikal-ollama ollama list
```

아래와 같이 2개 이상의 모델이 보이면 성공입니다:

```
NAME            SIZE
qwen2.5:7b      4.7 GB
bge-m3:latest   1.2 GB
```

---

## 5단계 — 접속 확인

### 5-1. 브라우저로 접속

1. Chrome 또는 Edge를 엽니다
2. 주소창에 아래 주소를 입력하고 엔터를 누릅니다:

```
http://localhost
```

3. BAIKAL Private AI 로그인 화면이 나타나면 ✅ 성공입니다

### 5-2. 로그인

| 항목 | 값 |
|------|-----|
| 아이디 | `admin` |
| 비밀번호 | 관리자에게 확인 |

---

## 6단계 — 문서 업로드 및 질문하기

### 문서 업로드

1. 왼쪽 메뉴에서 **"문서 관리"** 클릭
2. **"파일 업로드"** 버튼 클릭
3. PC에서 PDF, 한글(.hwp/.hwpx), Word(.docx), 엑셀(.xlsx) 파일 선택
4. 상태가 **"완료"** 로 바뀔 때까지 대기 (보통 30초~2분)

### AI에게 질문하기

1. 왼쪽 메뉴에서 **"AI 질문응답"** 클릭
2. **"+ 새 대화"** 버튼 클릭
3. 질문 입력 후 전송 버튼 클릭

**예시 질문:**
- "연차 휴가는 며칠인가요?"
- "2025년 3월 매출은 얼마인가요?"
- "출장비 규정을 알려주세요"

---

## 🔄 일상적인 사용법

### PC 재시작 후 BAIKAL 다시 켜기

PowerShell에서 아래 명령어 1줄만 입력합니다:

```
docker compose -f docker-compose.cpu.yml up -d
```

> Docker Desktop이 먼저 실행(초록불)되어 있어야 합니다.

### BAIKAL 끄기 (업무 후)

```
docker compose -f docker-compose.cpu.yml stop
```

데이터는 모두 PC에 안전하게 저장됩니다.

---

## 7단계 — 문제 해결

### ❌ Docker Desktop 아이콘이 빨간색일 때

1. 시스템 트레이의 Docker 아이콘 우클릭 → **"Restart"** 클릭
2. 또는 작업 관리자(`Ctrl+Shift+Esc`) → `Docker Desktop` 프로세스 종료 후 재시작

### ❌ `http://localhost` 접속이 안 될 때

PowerShell에서 실행:
```
docker ps
```
5개의 `baikal-` 컨테이너가 보이면 정상입니다.  
보이지 않으면 3단계부터 다시 진행합니다.

### ❌ AI가 답변을 안 할 때 (빈 화면)

모델 다운로드 확인:
```
docker exec baikal-ollama ollama list
```
`qwen2.5:7b` 가 없으면 4단계를 다시 진행합니다.

### ❌ "포트 80 이미 사용 중" 오류

PC에 IIS(웹 서버)나 다른 서비스가 80 포트를 사용 중입니다.  
관리자에게 문의하거나 기술 지원팀에 연락하세요.

### ❌ 문서 업로드 후 "실패" 상태

- 지원 파일 형식: PDF, DOCX, XLSX, HWP, HWPX
- 파일 크기: 100MB 이하
- `.txt` 파일은 지원하지 않습니다

---

## 📌 빠른 참조 카드

```
┌─────────────────────────────────────────────────┐
│         BAIKAL Private AI — 매일 시작 방법        │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. Docker Desktop 실행 → 🟢 초록불 확인         │
│                                                 │
│  2. PowerShell 열기                             │
│                                                 │
│  3. 아래 명령어 입력:                            │
│     cd C:\baikal777\baikal-private-ai           │
│     docker compose -f                           │
│       docker-compose.cpu.yml up -d              │
│                                                 │
│  4. 브라우저에서 http://localhost 접속           │
│                                                 │
│  5. admin 계정으로 로그인                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

> **도움이 필요하시면**: 시스템 관리자 또는 BAIKAL 기술 지원팀에 문의하세요.  
> 오류 화면이 보이면 PowerShell 창의 내용을 캡처해서 전달해 주시면 빠르게 해결됩니다.
