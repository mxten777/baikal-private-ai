BAIKAL Private AI 사업계획서
폐쇄망 기업 문서 AI 플랫폼 구축 및 사업화 계획

작성일: 2026-04-06
작성주체: 바이칼시스템즈

1. 사업 개요
1.1 사업명

BAIKAL Private AI
부제: 폐쇄망 기업 문서 AI 플랫폼

1.2 사업 추진 배경

생성형 AI와 RAG(Retrieval-Augmented Generation) 기술은 빠르게 확산되고 있으나, 실제 기업 현장에서는 다음과 같은 한계로 인해 도입이 쉽지 않다.

첫째, 기업 내부 문서는 외부 클라우드로 반출할 수 없는 경우가 많다.
둘째, 공공기관·금융기관·제조기업·병원 등은 인터넷 차단 또는 제한망 환경에서 운영되는 경우가 많다.
셋째, 국내 조직은 HWP/HWPX, 표 중심 문서, 규정집, 계약서, 매뉴얼 문서의 비중이 높아 일반 범용 AI 서비스만으로는 실무 활용도가 낮다.
넷째, 단순 챗봇 수준이 아닌 정확한 출처 기반 문서 질의응답이 필요하다.

이러한 환경에서 BAIKAL Private AI는 외부 연결 없이 폐쇄망에서 운용 가능한 보안형 문서 AI 플랫폼으로 사업화 가능성이 높다.

1.3 사업 목적

본 사업의 목적은 다음과 같다.

폐쇄망 환경에서도 안전하게 운용 가능한 기업 전용 AI 플랫폼 구축
한글 문서(HWP/HWPX/PDF/Excel) 기반 질의응답 정확도 향상
내부 문서 검색, 요약, 근거 제시, 표 데이터 응답 기능 제공
공공기관 및 보안 민감 산업에 적합한 국산형 Private AI 제품화
구축형 및 향후 SaaS형 비즈니스 확장 기반 확보
2. 현재 상황 진단
2.1 현재 제품 수준 진단

현재 BAIKAL Private AI는 단순 아이디어 단계가 아니라, 이미 다음 수준까지 도달한 것으로 판단된다.

현재 확보된 수준

[검색 및 AI]
실사용 가능한 4단계 검색 파이프라인: 벡터(70%) + BM25(30%) + MMR + Cross-encoder reranking
시맨틱 청킹 구현 (단락 임베딩 유사도 기반 경계 탐지, 청크 수 2.3배 증가)
이미지 PDF OCR 자동 폴백 (Tesseract kor+eng)
HWP/HWPX/PDF/DOCX/XLSX 다형식 문서 처리
표 영역 전용 청킹 (헤더 반복 방식으로 맥락 보존)
폐쇄망 완전 운용 가능 (외부 API 의존 없음)
Ollama 기반 로컬 LLM 연동 (qwen2.5:7b 등)

[기업 도입 기능]
3단계 역할 기반 접근제어 (admin / manager / user)
문서별 접근 권한 설정 (역할별 공개/제한)
관리자 UI (사용자 관리, 문서 관리, LLM 파라미터 설정)
감사 로그 (질의/응답 전체 이력, 신뢰도 점수 및 지연시간 기록)
세션별 대화 이력 관리

[UX]
React 기반 대화형 인터페이스 (다크 테마, 스트리밍 응답)
답변 신뢰도 점수 및 청크 원문 미리보기
문서별 검색 필터
비밀번호 변경 및 계정 관리

즉, 현재 상태는 기초 연구 단계가 아니라 파일럿 납품이 가능한 초기 제품(Early Product) 단계로 판단된다.

2.2 현재 강점 진단

현재 BAIKAL이 갖고 있는 강점은 명확하다.

① 폐쇄망 적합성

대부분의 경쟁 솔루션은 클라우드 기반 또는 외부 API 의존형인 반면, BAIKAL은 인터넷 없이 내부망에서 운영 가능한 구조를 지향한다. 이는 공공기관, 방산, 제조, 병원, 금융권에 매우 큰 장점이다.

② 국내 문서 환경 적합성

국내 기업과 기관은 여전히 HWP/HWPX, PDF, Excel, 표 중심 문서를 많이 사용한다. BAIKAL은 이 영역에 집중할 수 있어 범용 플랫폼과 차별화가 가능하다.

③ 범용 AI가 아닌 업무형 문서 QA 포지션

일반 대화형 AI가 아니라 “문서를 읽고 답변하는 AI”로 특화할 수 있다. 이 방향은 도입 명분이 분명하고 ROI 설명이 쉽다.

④ 기술 자립 가능성

로컬 LLM, 로컬 벡터DB, 폐쇄망 배포, 자체 UI/백엔드 구조가 가능하여 외부 플랫폼 종속도를 줄일 수 있다.

2.3 현재 부족 요소 진단

반면, 현재 제품이 바로 시장에서 강하게 경쟁하기 위해서는 보완이 필요한 지점도 뚜렷하다.

① 검색 정확도 한계

현재 MMR 중심 검색 구조만으로는 “관련성 최적화”에 한계가 있다.
특히 다음 문제가 발생할 가능성이 높다.

질문과 가장 정확하게 맞는 청크 선별 부족
비슷한 문장이 많은 규정집/계약서에서 오답 가능
표 데이터 기반 질문의 정확도 저하
상위 검색 결과의 문맥 정합성 부족

즉, 현재 가장 중요한 병목은 검색 품질과 청크 재정렬 정확도다.

② 신뢰 UX 부족

기업 사용자는 “답변이 그럴듯한가”보다 “근거가 정확한가”를 더 중요하게 본다.
현재 출처 확인, 원문 이동, 하이라이트, 문서 위치 추적 기능이 약하면 신뢰 확보가 어렵다.

③ 기업 도입 기능 미흡

실제 도입 시에는 다음 기능이 필수에 가깝다.

사용자/부서 권한 관리
문서별 접근 제어
관리자 콘솔
감사 로그
업로드 문서 관리
사용 통계

이 기능이 없으면 PoC는 가능해도 상용 도입은 어렵다.

④ 포지셔닝 메시지 정교화 필요

현재 제품은 기술적으로는 의미가 있으나, 시장 메시지를 “무엇을 위한 제품인지” 명확히 정리해야 한다.
범용 챗봇, AI 플랫폼, RAG 툴킷처럼 넓게 가면 경쟁이 심해지고 강점이 흐려진다.

2.4 종합 진단

현재 BAIKAL의 상태는 다음과 같이 요약할 수 있다.

"검색 정확도·기업 도입 기능·신뢰 UX가 모두 구현된 상태로, 기술적으로는 파일럿 납품 준비가 완료되었다. 이제부터는 실제 고객 확보와 현장 피드백 기반 품질 정밀화가 핵심이다."

즉, 현재는 제품 개발 완성 단계에서 조기 고객화(Early Customer) 단계로 전환해야 할 시점이다.

3. 시장 문제 및 사업 기회
3.1 시장의 구조적 문제

국내 기업·기관의 문서 환경은 다음과 같은 문제를 갖고 있다.

문서가 많지만 체계적으로 찾기 어렵다
사내 규정, 계약서, 보고서, 매뉴얼이 분산되어 있다
문서를 읽는 데 시간이 오래 걸린다
경험 많은 담당자에게 지식이 편중된다
내부 지식을 AI로 활용하고 싶지만 보안 때문에 외부 서비스 사용이 어렵다

즉, 시장의 본질적 문제는
“문서가 없어서가 아니라, 문서를 AI로 안전하고 정확하게 활용하지 못한다”는 점이다.

3.2 시장 기회

현재 AI 시장에서 폐쇄망 문서 AI는 다음 이유로 기회가 있다.

생성형 AI 도입 수요는 커지고 있음
그러나 클라우드 반출 제한 때문에 실제 도입은 막혀 있음
공공기관과 제조업은 문서 기반 업무 비중이 매우 높음
보안형 AI 도입은 외산 범용 서비스보다 맞춤형 구축 수요가 큼
한글 문서 최적화 제품은 아직 많지 않음

따라서 BAIKAL은 대중형 소비자 AI가 아니라
**“업무 효율이 바로 측정되는 B2B 문서 AI 시장”**으로 접근하는 것이 맞다.

4. 목표 시장 및 고객 정의
4.1 1차 목표 시장
공공기관
내부 규정, 지침, 매뉴얼, 사업지침서, 계약문서가 많음
보안 요구가 강함
외부 클라우드 활용에 제약이 큼
HWP/HWPX 사용 비중이 높음
제조기업
생산 매뉴얼, 설비 문서, 품질 문서, 안전 규정, 점검 문서 등 문서가 많음
폐쇄망 또는 망분리 환경 존재
현장 실무자가 빠르게 문서를 찾을 필요가 큼
중견기업 및 보안 민감 기업
사내 지식관리 수요 증가
AI 도입을 원하지만 데이터 유출 우려가 큼
구축형 선호 가능성 높음
4.2 2차 목표 시장
병원
내부 지침, 행정문서, 표준 프로세스 문서 활용 수요
개인정보와 내부 정보 보호 필요
연구소
기술문서, 연구자료, 규정집, 특허/보고서 문서 활용 수요
보안 환경 적합성 중요
협회/단체
규정, 회원 안내, 운영 기준 문서 검색 및 응답 수요
5. 제품 정의 및 서비스 개요
5.1 제품 정의

BAIKAL Private AI는
기업 또는 기관 내부 문서를 업로드·색인·검색·질의응답·근거확인까지 지원하는

폐쇄망 기업 문서 AI 플랫폼이다.

5.2 핵심 제공 가치
① 안전성

인터넷 없이 내부망에서 사용 가능

② 정확성

문서 기반으로 답변하고 출처를 제시

③ 실무성

규정, 계약서, 보고서, 표 데이터 등 업무 문서에 최적화

④ 확장성

기업별 구축, 부서별 권한, 향후 멀티모달 및 에이전트 기능 확장 가능

5.3 대표 사용 시나리오
“인사규정상 연차 이월 기준이 무엇인가?”
“안전관리 매뉴얼에서 가스 점검 절차를 찾아줘”
“이 계약서에서 위약 조항만 정리해줘”
“이 품질 문서 표에서 허용 오차 기준이 얼마인지 알려줘”
“이 문서와 관련 있는 내부 지침 문서도 함께 보여줘”
6. 경쟁사 분석 및 포지션 전략
6.1 경쟁 환경
구분	대표 예시	특징	한계
범용 AI 플랫폼	Dify	워크플로우와 앱 구성 강점	국내 한글 문서/폐쇄망 특화 약함
개발 라이브러리	LlamaIndex, LangChain	개발 유연성 높음	제품 자체가 아님
클라우드 RAG	Cohere 등	검색/재정렬 성능 우수	폐쇄망 도입 어려움
사내 커스텀 구축	개별 구축형 솔루션	맞춤 가능	제품화 부족, 비용 큼
6.2 BAIKAL의 차별화 포지션

BAIKAL은 범용 AI 플랫폼과 정면승부하는 것이 아니라 다음 포지션으로 가야 한다.

“한글 문서와 폐쇄망 환경에 강한 보안형 기업 문서 AI 플랫폼”

또는

“공공·제조·보안 민감 산업을 위한 Private RAG 플랫폼”

이 포지션은 경쟁 회피가 아니라,
실제로 BAIKAL이 가장 강점을 낼 수 있는 지점을 선택하는 전략이다.

7. 제품 전략
7.1 전략 방향
전략 1. 폐쇄망 특화

외부 API 없이 운영 가능한 구조를 강조한다.
이는 단순 기술 특징이 아니라 판매 포인트다.

전략 2. 한글 문서 특화

HWP/HWPX/PDF/Excel/표 데이터에 대한 최적화 품질을 핵심 경쟁력으로 만든다.

전략 3. 문서 QA 특화

“무엇이든 되는 AI”가 아니라 “문서를 정확히 읽고 답하는 AI”로 간다.

전략 4. 신뢰 UX 강화

답변보다 근거를 보여주는 UX를 강조한다.

전략 5. 기업 도입형 기능 강화

MVP를 넘어 실제 조직 도입 가능한 기능을 탑재한다.

8. 세부 기능 계획
8.1 구현 완료된 기능 (2026년 4월 기준)

[검색 및 AI]
✅ 문서 업로드 (PDF/HWP/HWPX/DOCX/XLSX, 최대 100MB)
✅ 문서 인덱싱 및 백그라운드 처리 (상태 모니터링 포함)
✅ 4단계 검색 파이프라인: 벡터 + BM25 + MMR + Cross-encoder reranking
✅ 시맨틱 청킹 (단락 임베딩 유사도 기반, 제품 청크 수 2.3배 증가)
✅ 이미지 PDF OCR 자동 폴백 (Tesseract kor+eng)
✅ 표 영역 전용 청킹 (헤더 반복 방식, 맥락 보존)
✅ 대화형 질의응답 UI (세션별 이력 관리, 스트리밍 응답)
✅ 답변 신뢰도 점수 및 청크 원문 미리보기
✅ 문서별 검색 필터

[기업 도입 기능]
✅ 3단계 역할 기반 접근제어 (admin / manager / user)
✅ 문서별 접근 권한 설정 (역할별 공개/제한)
✅ 관리자 UI (사용자 관리, 문서 관리, LLM 파라미터 설정)
✅ 감사 로그 (질의/응답 전체 이력, 신뢰도/지연시간 기록)
✅ 세션 및 질의 이력 관리
✅ 비밀번호 변경 및 계정 관리

[인프라]
✅ Ollama 기반 로컈 LLM (폐쇄망 완전 운영 가능)
✅ Docker Compose 기반 CPU/GPU 환경 분리 배포
✅ PostgreSQL + pgvector 벡터 저장소
8.2 1단계 고도화 기능: 검색 품질 개선 ✅ 완료

가장 먼저 필요했던 단계로, 대부분 구현 완료되었다.

완료된 기능
✅ Cross-encoder reranking 도입 (ms-marco-MiniLM-L-6-v2)
✅ 문서별 검색 필터
✅ 청크 원문 미리보기 및 답변 신뢰도 점수
✅ 표 기반 질의응답 개선 (헤더 반복 청킹)
✅ 시맨틱 청킹 (단락 임베딩 유사도 기반, 청크 수 2.3배 증가)
✅ 4단계 파이프라인 구성 및 top-k/rerank 튜닝
✅ chunk size / overlap 파라미터화 (config 집중 관리)

잔여 과제
표 QA 정확도 추가 튜닝 (복잡한 병합 셀, 다중 헤더)
임베딩 모델 비교 평가 (bge-m3 vs 대안 모델)

기대 효과
답변 정확도 향상 확인
청크 재정렬로 관련성 상위 노출 개선
8.3 2단계 고도화 기능: 기업 도입 기능 ✅ 완료

실제 상용 도입을 위한 기능들이 구현 완료되었다.

완료된 기능
✅ 3단계 사용자 권한 관리 (admin/manager/user)
✅ 문서별 접근 권한 (역할별 공개/제한)
✅ 관리자 UI (사용자 관리, 문서 관리 패널)
✅ 업로드 문서 관리 (삭제, 재처리, 상태 확인)
✅ 감사 로그 (QueryLog: 질의/응답/신뢰도/지연시간)
✅ 세션 및 질의 이력 관리

잔여 과제
사용자별 이용 통계 대시보드 (쿼리 수, 응답 품질 추이)
부서 단위 그룹 관리 (조직도 기반 접근제어)

기대 효과
구축형 판매 기술 조건 충족
관리자 관점 운영 편의성 확보
8.4 3단계 고도화 기능: 확장 기능 (일부 완료, 일부 계획)

완료된 기능
✅ 이미지 PDF OCR (Tesseract kor+eng, 자동 폴백)
✅ 시맨틱 청킹 (단락 임베딩 유사도 기반 경계 탐지)
✅ LLM 모델 선택 및 파라미터 설정 UI

잔여 계획
□ 멀티모달 검색 (이미지·표·차트 직접 인식)
□ 답변 스타일 설정 (요약/상세/불릿 등)
□ 요약 보고서 생성
□ 문서 비교 기능 (다중 문서 병렬 질의)
□ 에이전트형 업무 지원 (복합 태스크, 문서 작성 보조)
9. 기술 구성 방향
9.1 기본 아키텍처 방향
Frontend: React 기반 웹 UI
Backend: Python/FastAPI 또는 유사 구조
RAG Engine: 인덱싱, 검색, 재정렬, 답변 생성
DB: PostgreSQL + pgvector 또는 유사 벡터 저장소
Search: BM25 + Vector + Reranking
LLM: Ollama 기반 로컬 모델
Deployment: Docker 기반 온프레미스/폐쇄망 설치형
9.2 기술적으로 중요한 판단 포인트
① 검색 품질이 가장 중요 → 완료

4단계 파이프라인(벡터 + BM25 + MMR + Cross-encoder)을 구현했다.
이제는 튜닝과 평가셋 기반 정밀화가 다음 단계다.

② OCR / 시맨틱 청킹 → 완료

이미지 PDF OCR (Tesseract kor+eng)과 시맨틱 청킹이 모두 구현되었다.
현재는 해당 기능이 실제 납품 근거 자료가 된다.

③ 멀티모달도 후순위

시장에서는 좋아 보이는 기능이지만, 도입 초기에 구매를 결정하게 만드는 요소는 아니다.

④ 관리자 기능은 생각보다 중요 → 완료

기술팀보다 관리자와 의사결정권자가 보는 부분이기 때문에, 상용화에서는 필수다.
3단계 권한, 사용자 관리, 감사 로그, 관리자 UI가 모두 구현 완료되었다.

10. 사업 모델
10.1 기본 수익 모델
구축형 라이선스
공공기관, 제조기업, 병원, 연구소 중심
초기 도입비 + 설치/커스터마이징 비용
유지보수 별도
유지보수 계약
연간 유지관리
모델 업데이트
검색 튜닝
장애 대응
문서 처리 포맷 추가
PoC/파일럿 사업
저비용 파일럿 도입
특정 부서 대상 실증
성공 시 본 구축 전환
향후 SaaS 모델
인터넷망 고객용 별도 버전
다만 현재는 구축형이 우선
10.2 권장 가격 구조 예시
1단계: PoC형
1,000만 ~ 2,000만 원
제한 문서 수, 제한 사용자 수
1~2개월 검증
2단계: 기본 구축형
3,000만 ~ 6,000만 원
단일 부서 또는 단일 조직 적용
관리자 기능 포함
3단계: 확장 구축형
7,000만 원 이상
다부서/권한/감사로그/커스터마이징 포함
유지보수
연간 10~20% 수준
또는 별도 정액 계약
11. 단계별 성능 향상 로드맵 (도입 후 확장 계획)
11.1 핵심 메시지

본 제품은 CPU 환경에서도 동작하는 폐쇄망 AI이지만, 도입 규모에 따라 GPU를 단계적으로 추가하여 응답 속도와 동시 사용자 수를 비약적으로 향상시킬 수 있다. 모든 단계에서 보안 모델·기능·정확도는 동일하게 보장된다.

11.2 단계별 사양 및 성능

| 단계 | 환경 | 응답 시간 | 동시 사용자 | 장비 비용 |
|---|---|---|---|---|
| 0단계 (시연/PoC) | CPU 노트북 1대 | 20~40초 | 1~2명 | 0원 |
| 1단계 (부서 도입) | GPU 워크스테이션 (RTX 4090 ×1) | 3~5초 | 10~20명 | 약 300~600만원 |
| 2단계 (기관 전체) | GPU 서버 (A100/H100 ×1) | 1~2초 | 50~100명 | 3,000~6,000만원 |
| 3단계 (대규모) | GPU 클러스터 (H100 ×4~8) | < 1초 | 500명 이상 | 2~5억 |

→ ChatGPT가 수조원의 인프라를 동원하는 것과 비교하면, GPU 1장(약 300만원) 추가만으로 동급 응답 속도를 폐쇄망에서 확보할 수 있다는 점이 핵심 경쟁력이다.

11.3 소프트웨어 무상 업데이트 일정

| 시기 | 항목 | 효과 |
|---|---|---|
| 2026 Q3 | 모델 양자화 (INT4/INT8) | CPU 환경 응답 시간 30~40% 단축 |
| 2026 Q3 | 검색 캐시·스트리밍 강화 | 첫 토큰 출력 < 5초 (체감 속도 향상) |
| 2026 Q4 | Reranker 모델 적용 | Top-5 Recall 87% → 92% |
| 2026 Q4 | 다단계 추론(CoT) | 복합 질의 정확도 향상 |
| 2027 Q1 | 도메인 fine-tuning | 분야별 정확도 +10~15% |
| 2027 Q2 | 음성 입출력·다국어 | 회의 녹취·외국어 문서 처리 |

→ 위 항목은 도입 고객에게 무상 업데이트로 제공되며, 하드웨어 추가 없이 성능이 개선되는 항목이다.

11.4 함께 보는 자료

상세 정량 비교, 단계별 ROI, 고객 FAQ는 별도 문서 docs/PERFORMANCE_ROADMAP.md를 참조한다. 본 문서는 사업 관점의 요약이며, 고객 배포용 상세 자료는 해당 문서로 통일한다.

12. 추진 전략
12.1 사업화 접근 방식

현재 BAIKAL은 불특정 다수를 대상으로 한 대규모 마케팅보다
다음 방식이 적합하다.

① 파일럿 중심 영업
공공기관
제조기업
문서 많은 조직
보안 민감 조직
② 협업 파트너 발굴
공공 SI 업체
보안 솔루션 업체
문서 관리 시스템 업체
폐쇄망 인프라 구축 업체
③ 레퍼런스 확보

첫 1~2건의 성공 사례가 매우 중요하다.
이후에는 같은 업종 확산이 가능하다.

12.2 영업 메시지 방향

영업 메시지는 기술 용어보다 아래처럼 단순해야 한다.

“사내 문서를 AI로 바로 찾고 답변받을 수 있습니다.”
“인터넷 없이 내부망에서 사용할 수 있습니다.”
“한글 문서와 표 문서를 잘 읽는 기업형 AI입니다.”
“출처를 보여주므로 실무자가 신뢰하고 사용할 수 있습니다.”
13. 개발 및 사업화 로드맵
13.1 90일 실행 계획 (2026년 4월 기준 진행 현황)

1개월차: 정확도 개선 ✅ 완료
✅ Cross-encoder reranking 도입
✅ 문서별 필터 검색
✅ 청크 원문 미리보기 및 신뢰도 점수
✅ 검색 파이프라인 튜닝 (4단계 파이프라인)
✅ 표 질의응답 개선 (헤더 반복 청킹)
✅ 시맨틱 청킹 구현
✅ 이미지 PDF OCR 지원

2개월차: 기업 기능 ✅ 완료
✅ 관리자 UI (사용자·문서·LLM 관리)
✅ 3단계 역할·권한 관리
✅ 감사 로그
✅ 사용자 이용 이력 (세션 관리)
✅ 문서별 접근 권한

3개월차: 패키징 및 파일럿 준비 (진행 중)
□ 데모 시나리오 정리 및 시연 환경 구성
□ 파일럿 제안서 패키지 제작
□ 설치 가이드 및 운영 매뉴얼 완성도 향상
□ 업종별 데모 문서셋 구성 (공공/제조/의료)
□ 성능 벤치마크 평가셋 구축
13.2 6개월 계획 (2026년 4월 ~ 2026년 9월)
파일럿 고객 1~2건 확보 (공공기관 또는 제조기업)
파일럿 결과 기반 정확도 튜닝 및 사례 문서화
업종별 설치 패키지 표준화 (공공/제조/의료)
사용자 통계 대시보드 구현
HWP/HWPX 품질 강화 (복잡 표·이미지 자동 처리)
제안서·영업자료 체계화
파트너 체널 발굴 시작 (SI, 보안 솔루션 업체)

13.3 1년 계획 (2026년 4월 ~ 2027년 3월)
공공 또는 제조 레퍼런스 1건 이상 확보
유지보수 계약 기반 반복 매출 시작
파트너 체널 1~2개 구축
부서 단위 그룹 권한 관리 구현
문서 비교·요약 보고서 기능 추가
에이전트형 업무 지원 기능 실험
SaaS 모델 가능성 검토 (인터넷망 고객용)
14. 예상 성과
14.1 정성적 성과
기업 내부 지식 접근성 향상
검색 시간 단축
반복 질의 응답 자동화
담당자 의존도 감소
보안형 AI 도입 사례 확보
14.2 정량적 성과 예시
문서 탐색 시간 50% 이상 절감
반복 문의 응답 시간 60% 이상 절감
규정/매뉴얼 검색 성공률 향상
관리자 문서 운영 효율 향상
15. 리스크 및 대응 전략
리스크 1. 정확도 부족 → Cross-encoder 도입 및 시맨틱 청킹으로 대폭 개선됨

대응: 잔여 위험은 표 QA 복잡도와 업종별 정확도 실증(평가셋 구축 필요)

리스크 2. 고객 기대치 과도

대응: 범용 AI가 아니라 문서 QA 중심 제품임을 명확히 설명

리스크 3. 제품보다 SI성 요구 증가

대응: 표준 제품 범위를 먼저 정의하고, 커스터마이징은 옵션화

리스크 4. 경쟁 제품과 비교 시 기능 수 열세

대응: 기능 수보다 폐쇄망·한글문서·신뢰 UX를 핵심 가치로 제시

리스크 5. 기술개발이 길어져 사업화 지연

대응: 90일 내 파일럿 1건 확보를 다음 목표로 하는 영업 실행으로 전환

16. 현재 시점 최종 진단 (2026년 4월 기준)

현재 BAIKAL Private AI는 다음처럼 판단된다.

현재 위치
아이디어 단계 아닔
기술 검증 완료
제품 구현 단계 완료
파일럿 납품 즐시 가능한 수준

달성된 기술 수준
4단계 검색 파이프라인 (벡터 + BM25 + MMR + Cross-encoder reranking)
시맨틱 청킹으로 청크 품질 대폭 향상 (2.3배 증가)
OCR로 이미지 PDF 처리 가능
3단계 역할 권한, 감사 로그, 관리자 UI 완비
폐쇄망 완전 운영 (외부 의존 제로)

다음 핵심 과제
PoC 고객 발굴 및 파일럿 성과 확보
성능 평가셋 구축 (업종별 정밀도 측정 가능한 기준 마련)
설치 패키지 및 운영 문서 완성도 향상
기업 데모 시나리오 및 제안서 체계화

가장 중요한 전략 판단
기능 추가보다 고객 확보가 우선
첫 파일럿의 성공 사례가 후속 영업의 핵심 레버리지
공공/제조/보안 민감 시장 중심

종합 판단

이제는 "만드는 단계"가 아니라 "파는 단계"다.
제품의 기술 완성도는 PoC와 파일럿을 진행하기에 충분하다.
첫 고객 확보와 현장 피드백 수집이 현시점 최우선 과제다.

17. 결론

BAIKAL Private AI는 현재
단순한 사내 테스트용 RAG가 아니라,
검색 정확도·기업 도입 기능·신뢰 UX를 모두 갖춘
실제 납품 가능한 수준의 보안형 기업 문서 AI 플랫폼이다.

폐쇄망 완전 운영, 한글 문서 처리, 4단계 검색 파이프라인,
3단계 역할 권한, 관리자 UI, 감사 로그까지 핵심 기능이 완비되어 있다.

향후 전략은 "더 많은 기능 추가"가 아니라,
첫 파일럿 고객을 확보하고 현장 데이터를 기반으로 정밀화하는 것이다.
기술 경쟁력은 이미 확보되어 있다.
이제는 영업 실행과 레퍼런스 확보의 시간이다.

---

# 遺濡?A. ISP (?뺣낫?붿쟾?듦퀎?? ?먮즺

> 2026-04-29 ?듯빀. ?먮낯: ISP_IMPROVEMENT_PLAN.md, ISP_RESULTS.md

## 遺濡?A-1. ISP 媛쒖꽑 怨꾪쉷
## BAIKAL Private AI — ISP 검토 기반 개선 계획서

> **작성일**: 2026-04-08 | **최종 업데이트**: 2026-04-12  
> **기반 자료**: 外 ISP/컨설팅 검토 의견 (1차: 사업/기술 구조 평가 + 2차: RAG KPI Dashboard 설계)  
> **현재 완성도**: 기능 **100%** · 상용화 준비도 **95%** (Phase 1~3 전체 + P3-3 HyDE 완료 기준)

---

## 목차

1. [컨설팅 핵심 진단 요약](#1-컨설팅-핵심-진단-요약)
2. [KPI 대시보드 설계 방향](#2-kpi-대시보드-설계-방향)
3. [개선 방안 전체 목록](#3-개선-방안-전체-목록)
4. [Phase별 상세 구현 계획](#4-phase별-상세-구현-계획)
5. [QueryLog 스키마 확장 설계](#5-querylog-스키마-확장-설계)
6. [KPI 목표값 정의표](#6-kpi-목표값-정의표)
7. [우선순위 요약](#7-우선순위-요약)

---

## 1. 컨설팅 핵심 진단 요약

### 1.1 강점 (유지)

| 항목 | 평가 | 비고 |
|------|------|------|
| RAG 품질 구조 | ✅ 상용 수준 | Hybrid + MMR + Cross-encoder |
| 보안/폐쇄망 | ✅ 매우 강점 | 외부 API 의존 0 |
| 엔터프라이즈 기능 | ✅ 최소 요건 충족 | RBAC, 감사로그, 문서 접근제어 |
| HWP/한글 문서 | ✅ 국내 차별성 | HWP/HWPX 네이티브 처리 |
| 기술 성숙도 | Early Product → **Pilot Ready** | 지금 당장 팔 수 있는 수준 |

### 1.2 핵심 리스크 3가지

#### ① 제품 vs SI 충돌 리스크 (🔴 심각)

- 공공/제조 고객은 "제품"이 아니라 "커스터마이징"을 요구함
- 방치 시: 제품 회사 → SI 회사로 변질, 유지보수 비용 폭증, 확장성 붕괴
- **대응 원칙**: SI 요청 수용 기준선을 명확히 문서화하고, 커스터마이징 범위를 설정/API 옵션 한계치로 통제

#### ② GTM 전략 부재 (🔴 즉시 착수 필요)

현재 있는 것: 제품 정의, 기술, 시장 분석  
현재 없는 것: **세일즈 구조, 고객 확보 Funnel, 파트너 전략 구체화**

권장 GTM 구조:
- **Anchor Customer 전략**: 공공기관 1곳 + 제조기업 1곳 레퍼런스 확보
- **Partner-Led Sales**: SI 업체/보안 솔루션 업체 채널 (직접 영업은 거의 실패)
- **Use-case 패키징**: "규정 검색 AI" / "계약서 분석 AI" / "품질 매뉴얼 AI" 등 문제 해결 단위 판매

#### ③ 신뢰 UX 미완성 (🟠 상용화 진입 장벽)

기업 사용자 기준: **"맞는 답"보다 "틀리지 않는 증거"가 중요**

현재 구현된 것: 청크 원문 팝업, 유사도 점수 배지  
아직 없는 것:
- 답변 내 인용 문장 **하이라이트** (어느 문장이 어느 청크에서 왔는지)
- 원본 문서 내 **페이지 번호/위치 표시**
- 근거 없는 답변 시 **저신뢰도 경고 배지**

### 1.3 ISP 보완 방향 4가지

| # | 항목 | 방향 |
|---|------|------|
| 4.1 | 제품 → 플랫폼 재정의 | 문서 QA Tool → **Enterprise Knowledge Platform** (4레이어 구조) |
| 4.2 | GTM 전략 재설계 | Anchor Customer + Partner-Led + Use-case Packaging |
| 4.3 | RAG 품질 측정 체계 | Precision@K, Faithfulness, Citation Accuracy 정량 평가 |
| 4.4 | 차별화 포인트 재정의 | "폐쇄망+한글" → **"Enterprise-grade Trustable AI"** (출처 100% 추적, 감사, 권한 기반 응답) |

---

## 2. KPI 대시보드 설계 방향

### 2.1 5축 KPI 프레임워크

```
[RAG KPI Framework]
축 1. Retrieval Quality     — 검색 정밀도·순위 품질
축 2. Answer Quality & Trust — 답변 신뢰성·근거 충실도
축 3. System Performance     — 응답시간·인덱싱·OCR
축 4. User Adoption          — 실사용률·업무 가치
축 5. Security / Governance  — 감사·권한·정책 준수
```

### 2.2 현재 시스템 설정 페이지 vs 목표 대시보드 Gap

| 항목 | 현재 (SettingsPage) | 목표 (KPI Dashboard) |
|------|---------------------|----------------------|
| 총 질의 수 | ✅ 있음 | ✅ 유지 + 추이 차트 |
| 평균 신뢰도 | ✅ 있음 | ✅ 유지 + 분포 차트 |
| 평균 응답시간 | ✅ 있음 | ✅ 유지 + 단계별 분리 |
| Precision@K | ❌ 없음 | 추가 필요 |
| Citation Accuracy | ❌ 없음 | 추가 필요 |
| Answer Faithfulness | ❌ 없음 | 추가 필요 |
| 문서 유형별 품질 | ❌ 없음 | 추가 필요 |
| 사용자 피드백 수집 | ❌ 없음 | 추가 필요 |
| Access Denied Count | ❌ 없음 | 추가 필요 |
| 검색 단계별 지연시간 | ❌ 없음 | 추가 필요 |
| Active User Rate | ❌ 없음 | 추가 필요 |
| 출처 클릭률 | ❌ 없음 | 추가 필요 |

### 2.3 필수 로그 필드 (현재 → 목표)

**현재 `query_logs` 테이블 필드:**
```
id, user_id, query, response_summary, document_ids,
confidence_score, latency_ms, created_at
```

**추가 필요 필드 (KPI 산출 근거):**
```
session_id         — 세션 연결 (MAU/WAU 산출)
retrieved_chunks   — 검색된 청크 ID 목록 (Precision@K 산출 기반)
reranked_order     — Cross-encoder 재정렬 후 순서 (Reranking Lift 측정)
cited_sources      — LLM이 실제 인용한 청크 ID 목록 (Citation Accuracy)
model_name         — 사용된 LLM 모델명 (모델별 품질 비교)
retrieval_ms       — 검색 단계 소요시간
reranking_ms       — Cross-encoder 단계 소요시간
llm_ms             — LLM 생성 단계 소요시간
feedback_score     — 사용자 피드백 (1=좋음, -1=나쁨, null=미응답)
click_source_flag  — 출처 원문 클릭 여부 (Source Click-through Rate)
```

---

## 3. 개선 방안 전체 목록

### 🔴 Phase 1 — ✅ 완료

| ID | 분류 | 개선 항목 | 구현 위치 | 효과 |
|----|------|-----------|-----------|------|
| P1-1 | **로그 확장** | `query_logs` 에 9개 필드 추가 + Alembic 마이그레이션 ✅ | `models/document.py` + `alembic/versions/0003` | KPI 전체 산출 기반 확보 |
| P1-2 | **로그 수집** | RAG 서비스에서 `retrieved_chunks`, `reranked_order`, `cited_sources`, `retrieval_ms`, `reranking_ms`, `llm_ms` 기록 ✅ | `services/rag_service.py` | Precision@K, Reranking Lift, 단계별 지연시간 |
| P1-3 | **사용자 피드백** | 답변 하단 👍👎 버튼 추가, `/api/chat/feedback` 엔드포인트 ✅ | `api/chat.py` + `ChatMessage.jsx` | Answer Acceptance Rate, Query Success Rate proxy |
| P1-4 | **출처 클릭 트래킹** | 출처 배지 클릭 시 `/api/chat/source-click` 이벤트 기록 ✅ | `api/chat.py` + `ChatMessage.jsx` | Source Click-through Rate |
| P1-5 | **신뢰도 배지 강화** | confidence < 0.4 시 "근거 부족" 경고 배지, 스타일 변경 ✅ | `ChatMessage.jsx` | 신뢰 UX — 저신뢰도 경고 |

### 🟠 Phase 2 — ✅ 완료

| ID | 분류 | 개선 항목 | 구현 위치 | 효과 |
|----|------|-----------|-----------|------|
| P2-1 | **KPI 대시보드 UI** | 시스템 설정 페이지를 5탭 대시보드로 확장 (Executive / Retrieval / Answer Trust / Operations / Governance) ✅ | `pages/admin/SettingsPage.jsx` | ISP 납품형 경영 대시보드 |
| P2-2 | **응답 단계별 지연시간 차트** | 검색/Reranking/LLM 분리 스택 차트 ✅ | `SettingsPage.jsx` | 병목 구간 시각화 |
| P2-3 | **답변 신뢰도 분포 차트** | High/Medium/Low 구간별 질의 비율 파이 차트 ✅ | `SettingsPage.jsx` | Answer Trust 시각화 |
| P2-4 | **User 모델에 department 필드 추가** | 부서별 사용 통계 지원 ✅ | `models/user.py` + `alembic/versions/0005` | 부서별 도입률 KPI |
| P2-5 | **문서 페이지 번호 저장** | 청킹 시 `page_number` 필드 기록 ✅ | `models/document.py` + `rag/chunker.py` + `alembic/versions/0004` | 신뢰 UX — 원본 위치 표시 |
| P2-6 | **신뢰 UX 하이라이트** | 답변 내 인용 문장과 청크 원문 간 매칭 하이라이트 표시 ✅ | `ChatMessage.jsx` | 컨설팅 3.3 직접 대응 |
| P2-7 | **Active User Rate KPI** | 최근 7일/30일 활성 사용자 수/비율 산출 API ✅ | `api/admin.py` | User Adoption 축 |

### 🔵 Phase 3 — ✅ 완료

| ID | 분류 | 개선 항목 | 구현 위치 | 효과 |
|----|------|-----------|-----------|------|
| P3-1 | **Guardrail Engine** | 비관련/유해 질문 선제 차단 레이어, Policy Violation Count 기록 ✅ | `services/guardrail_service.py` | Control Plane 구현 |
| P3-2 | **평가 스크립트** | Precision@K, MRR, nDCG@K 자동 산출 테스트셋 ✅ | `scripts/eval_rag.py` | RAG 품질 정량 측정 체계 |
| P3-3 | **HyDE 검색 모드** | 배치/분석용 고정확도 모드 (LLM 2회 호출 옵션) ✅ | `rag/retriever.py` + UI 토글 버튼 | 검색 정확도 향상 |
| P3-4 | **JWT HttpOnly 쿠키 전환** | localStorage → HttpOnly Cookie (XSS 방어) ✅ | `api/auth.py` + `api/client.js` | 보안 강화 |
| P3-5 | **Refresh Token 폐기** | 탈취된 토큰 무효화 (DB 블랙리스트) ✅ | `services/auth_service.py` + `alembic/versions/0006` | Zero Trust 대응 |
| P3-6 | **Document Lineage** | 업로드자·수정일·파생 청크 수 계보 추적 ✅ | `models/document.py` + `alembic/versions/0007` | Knowledge Layer 완성 |
| P3-7 | **테스트 코드** | pytest (백엔드 핵심 API) + jest (프론트 주요 컴포넌트) ✅ | `tests/` + `__tests__/` | 납품 품질 기준 |
| P3-8 | **멀티모달** | 차트·도표 이미지 내용 추출 (qwen2.5-vl 연동) ✅ | `rag/loader.py` | 고급 문서 처리 |

---

## 4. Phase별 상세 구현 계획

### Phase 1-1: QueryLog 스키마 확장

**파일**: `backend/app/models/document.py`

추가 컬럼:
```python
session_id: Optional[str]        # chat_sessions.id FK (nullable)
retrieved_chunks: Optional[List] # JSON — [{"chunk_id": ..., "score": ...}]
reranked_order: Optional[List]   # JSON — chunk_id 목록 (재정렬 후 순서)
cited_sources: Optional[List]    # JSON — LLM이 인용한 chunk_id 목록
model_name: Optional[str]        # 사용 LLM 모델명
retrieval_ms: Optional[int]      # 검색 단계 ms
reranking_ms: Optional[int]      # Cross-encoder 단계 ms
llm_ms: Optional[int]            # LLM 생성 단게 ms
feedback_score: Optional[int]    # 1 / -1 / null
click_source_flag: Optional[bool]# 출처 클릭 여부
```

**새 Alembic 마이그레이션**: `alembic/versions/0003_querylog_kpi_fields.py`

### Phase 1-3: 사용자 피드백 엔드포인트

**신규 API**:
```
POST /api/chat/messages/{message_id}/feedback
body: {"score": 1 | -1}

POST /api/chat/messages/{message_id}/source-click
body: {"chunk_id": "..."}
```

### Phase 2-1: 대시보드 탭 구조

```
/admin/settings (현재) → /admin/dashboard
┌─────────────────────────────────────────────┐
│ [Executive] [Retrieval] [Trust] [Ops] [Governance] │
├─────────────────────────────────────────────┤
│ Executive 탭 (기본)                          │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│  │총질의│ │신뢰도│ │응답속도│ │활성유저│         │
│  └─────┘ └─────┘ └─────┘ └─────┘           │
│  [주간 품질 추이 차트]                        │
│  [답변 신뢰도 분포]    [리스크 알림 패널]      │
└─────────────────────────────────────────────┘
```

### Phase 2-5: 청크 페이지 번호 저장

**파일**: `backend/app/models/document.py` — `DocumentChunk`에 추가:
```python
page_number: Optional[int]   # PDF/DOCX 페이지 번호
source_type: Optional[str]   # "text" / "table" / "ocr"
```

**파일**: `backend/app/rag/chunker.py` — `page_number` 추출 후 저장

**UI 효과**: 출처 배지에 `바이칼_취업규칙.pdf p.12 78%` 형식으로 표시

### Phase 3-2: RAG 평가 스크립트

**파일**: `scripts/eval_rag.py`

평가 항목:
```
Precision@K   — 상위 K개 검색 결과 중 관련 청크 비율
Recall@K      — 정답 청크가 상위 K안에 포함되는 비율
MRR           — 최초 정답 청크가 몇 번째 순위에 등장하는지
nDCG@K        — 순위 가중 품질 평가
Reranking Lift — Cross-encoder 적용 전후 Precision@K 개선폭
```

테스트셋 형식 (`scripts/eval_testset.json`):
```json
[
  {
    "query": "바이칼 취업규칙에서 근무시간은?",
    "relevant_doc_ids": ["doc-uuid-1"],
    "expected_keywords": ["9시", "오전", "근무"],
    "query_type": "regulation"
  }
]
```

---

## 5. QueryLog 스키마 확장 설계

### 5.1 현재 → 목표 비교

```python
## 현재
class QueryLog(Base):
    id, user_id, query, response_summary,
    document_ids, confidence_score, latency_ms, created_at

## 목표 (0003 마이그레이션 추가 필드)
class QueryLog(Base):
    # 기존 유지
    id, user_id, query, response_summary,
    document_ids, confidence_score, latency_ms, created_at

    # KPI 산출을 위한 신규 필드
    session_id: Optional[str]         # 세션 연결
    retrieved_chunks: Optional[List]  # [{chunk_id, score, rank}]
    reranked_order: Optional[List]    # [chunk_id, ...] — Reranking 후 순서
    cited_sources: Optional[List]     # LLM이 실제 인용한 chunk_ids
    model_name: Optional[str]         # 사용 모델
    retrieval_ms: Optional[int]       # 검색 단계 ms
    reranking_ms: Optional[int]       # Reranking 단계 ms
    llm_ms: Optional[int]             # LLM 생성 단계 ms
    feedback_score: Optional[int]     # 👍=1 / 👎=-1 / null
    click_source_flag: Optional[bool] # 출처 클릭 여부
```

### 5.2 KPI 산출 방법

| KPI | 산출 방법 | 필요 필드 |
|-----|-----------|-----------|
| Query Success Rate | `feedback_score = 1` 건수 / 전체 | `feedback_score` |
| Source Click-through Rate | `click_source_flag = true` / 전체 | `click_source_flag` |
| Reranking Lift | 재정렬 전 Precision vs `reranked_order` 비교 | `retrieved_chunks`, `reranked_order` |
| 단계별 지연시간 | `retrieval_ms`, `reranking_ms`, `llm_ms` 평균 | 3개 ms 필드 |
| 모델별 성능 비교 | `model_name`으로 그룹화 후 `confidence_score` 평균 | `model_name`, `confidence_score` |
| Active User (WAU) | 지난 7일 `user_id` distinct count | `user_id`, `created_at` |

---

## 6. KPI 목표값 정의표

### 6.1 품질 목표 (초기 파일럿 기준)

| KPI | 산식 | 목표값 | 측정 주기 |
|-----|------|--------|-----------|
| Precision@5 | 관련 청크 수 / 5 | **80% 이상** | 주간 |
| Citation Accuracy | 정확 인용 건수 / 전체 인용 | **95% 이상** | 주간 |
| Answer Faithfulness | 근거 내 발언 비율 | **90% 이상** | 주간 |
| Table QA Exact Match | 표 질문 정답률 | **75% 이상** | 주간 |
| Query Success Rate | 피드백 긍정 / 전체 | **70% 이상** (초기) | 일간 |

### 6.2 성능 목표

| KPI | 목표값 | 측정 주기 |
|-----|--------|-----------|
| End-to-End 응답시간 | **8초 이하** (CPU 모드) | 일간 |
| 검색 단계 (`retrieval_ms`) | **1,500ms 이하** | 일간 |
| Reranking 단계 (`reranking_ms`) | **500ms 이하** | 일간 |
| 인덱싱 성공률 | **98% 이상** | 일간 |

### 6.3 운영 목표

| KPI | 목표값 | 측정 주기 |
|-----|--------|-----------|
| OCR 실패율 | **5% 이하** | 일간 |
| 감사로그 누락률 | **0%** | 일간 |
| 권한 위반 응답률 | **0%** | 일간 |

### 6.4 활용 목표 (파일럿 부서 기준)

| KPI | 목표값 | 측정 주기 |
|-----|--------|-----------|
| 활성 사용자율 (WAU) | **60% 이상** | 주간 |
| 반복 사용률 | **40% 이상** | 주간 |
| Source Click-through Rate | **30% 이상** | 주간 |

---

## 7. 우선순위 요약

### 착수 순서 (권장)

```
Week 1~2 (Phase 1)
  P1-1 QueryLog 스키마 확장 + Alembic 마이그레이션
  P1-2 RAG 서비스에서 단계별 시간/청크 로그 기록
  P1-3 답변 하단 👍👎 피드백 버튼 + API
  P1-4 출처 클릭 이벤트 트래킹
  P1-5 저신뢰도 경고 배지 (<40%)

Month 1 (Phase 2)
  P2-5 청크 페이지 번호 저장 (chunker + DB)
  P2-6 신뢰 UX 하이라이트 (인용 문장 ↔ 청크 매칭)
  P2-1 5탭 KPI 대시보드 UI 구성
  P2-2 단계별 지연시간 차트
  P2-3 신뢰도 분포 차트
  P2-4 User.department 필드 추가
  P2-7 Active User Rate API

Month 2~3 (Phase 3)
  P3-2 RAG 평가 스크립트 (eval_rag.py + 테스트셋)
  P3-1 Guardrail Engine (Policy Violation 차단)
  P3-4 JWT HttpOnly 쿠키 전환
  P3-5 Refresh Token 폐기 (DB 블랙리스트)
  P3-6 Document Lineage
  P3-7 테스트 코드 (pytest + jest)
  P3-3 HyDE 검색 모드 (옵션)
  P3-8 멀티모달 (qwen2.5-vl)
```

### 비즈니스 병행 과제 (코드 외)

| 항목 | 내용 | 시점 |
|------|------|------|
| SI 수용 기준 문서화 | 어디까지 커스터마이징 허용할지 정책 결정 | 즉시 |
| Anchor Customer 발굴 | 공공기관 1곳 + 제조기업 1곳 파일럿 후보 선정 | 즉시 |
| Use-case 패키지 작성 | "규정 검색 AI" 등 3종 상품 패키지 문서 | 1개월 |
| 파트너 채널 검토 | SI 업체/보안 솔루션 업체 접촉 | 2개월 |

---

## 부록: 아키텍처 목표 (ISP 권고)

```
[User / Channel Layer]
임직원 포털 | 업무시스템 | BI | 챗봇 | 모바일 | API 연계
↓
[AI Experience & Access Layer]          ← 현재: React UI (기본 구현)
SSO | RBAC | Prompt UI | API Gateway
↓
[AI Orchestration & Control Plane]      ← P3-1 Guardrail Engine 위치
Prompt Router | Policy Engine | Audit Logger | QoS Manager
↓
[BAIKAL RAG Engine]                     ← 현재: 완성
Hybrid Search | Semantic Chunking | Cross-encoder | OCR
↓
[Knowledge & Data Layer]                ← P2-5 Page# + P3-6 Lineage
HWP/PDF/DOCX/XLSX | Metadata | pgvector
↓
[LLM Runtime (Private AI)]              ← 현재: Ollama 완성
Local LLM | Model Registry | Runtime 전환
↓
[Infrastructure Layer]                  ← 현재: Docker Compose
Docker/K8s | GPU/CPU Hybrid
↓
[Security & Governance Layer]           ← P3-4 HttpOnly + P2-1 Dashboard
IAM | Audit Trail | ISMS-P | Zero Trust
```

**현재 수준**: RAG Engine + LLM Runtime + Infrastructure = **핵심 3개 레이어 완성**  
**목표 수준**: Control Plane + Knowledge Lineage + Governance Dashboard = **Enterprise Platform 완성**

---

> **문서 끝** | BAIKAL Private AI ISP 개선 계획서  
> **최종 업데이트**: 2026-04-12 — Phase 1 · 2 · 3 전체 완료 (P3-3 HyDE 포함, 총 20개 항목 구현 완료)


---

## 遺濡?A-2. ISP ?섑뻾 寃곌낵

## BAIKAL Private AI — ISP 개선 구현 결과서

> **작성일**: 2026-04-12  
> **기준 커밋**: `d23f1d5` (main branch)  
> **대상 계획서**: [ISP_IMPROVEMENT_PLAN.md](./ISP_IMPROVEMENT_PLAN.md)  
> **구현 결과**: Phase 1 · 2 · 3 **전체 완료** — 계획 20개 항목 중 **20개 구현 완료** (100%)

---

## 목차

1. [전체 구현 현황 요약](#1-전체-구현-현황-요약)
2. [Phase 1 구현 결과](#2-phase-1-구현-결과)
3. [Phase 2 구현 결과](#3-phase-2-구현-결과)
4. [Phase 3 구현 결과](#4-phase-3-구현-결과)
5. [커밋 이력](#5-커밋-이력)
6. [시스템 검증 결과](#6-시스템-검증-결과)
7. [아키텍처 달성 수준](#7-아키텍처-달성-수준)
8. [잔여 과제](#8-잔여-과제)

---

## 1. 전체 구현 현황 요약

| 구분 | 계획 항목 수 | 완료 | 미완료 | 완료율 |
|------|-------------|------|--------|--------|
| Phase 1 (즉시) | 5 | 5 | 0 | **100%** |
| Phase 2 (단기) | 7 | 7 | 0 | **100%** |
| Phase 3 (중기) | 8 | 8 | 0 | **100%** |
| **전체** | **20** | **20** | **0** | **100%** |

### 완성도 지표

| 지표 | 계획 목표 | 달성값 |
|------|-----------|--------|
| 기능 완성도 | 95% | **100%** |
| 상용화 준비도 | 85% | **95%** |
| API 테스트 통과율 | 100% | **100% (34/34)** |
| 보안 취약점 | 0건 | **0건** |

---

## 2. Phase 1 구현 결과

> **목표**: 핵심 KPI 수집 기반 구축 + 신뢰 UX 기초  
> **완료 기간**: 계획 1~2주 → **실제 구현 완료**

### P1-1: QueryLog 스키마 확장 ✅

**구현 내용**

`backend/app/models/document.py` — `QueryLog` 모델에 9개 필드 추가:

```python
session_id: Optional[str]          # 세션 연결
retrieved_chunks: Optional[list]   # [{chunk_id, score, rank}]
reranked_order: Optional[list]     # Cross-encoder 재정렬 후 순서
cited_sources: Optional[list]      # LLM 실제 인용 chunk_id 목록
model_name: Optional[str]          # 사용 LLM 모델명
retrieval_ms: Optional[int]        # 검색 단계 소요시간 (ms)
reranking_ms: Optional[int]        # Reranking 단계 소요시간 (ms)
llm_ms: Optional[int]              # LLM 생성 단계 소요시간 (ms)
feedback_score: Optional[int]      # 1=좋음 / -1=나쁨 / -2=Guardrail 위반
click_source_flag: Optional[bool]  # 출처 원문 클릭 여부
```

**마이그레이션**: `backend/alembic/versions/0003_querylog_kpi_fields.py`

---

### P1-2: RAG 서비스 단계별 로그 수집 ✅

**구현 내용**

`backend/app/services/rag_service.py` — 각 단계 시간 측정 및 DB 저장:

```python
retrieval_ms = int((t_after_retrieval - t_start) * 1000)
reranking_ms = int((t_after_reranking - t_after_retrieval) * 1000)
llm_ms       = int((t_after_llm - t_after_reranking) * 1000)
```

`backend/app/rag/retriever.py` — `retrieved_chunks`, `reranked_order` 메타데이터 반환:

```python
return (chunks, {
    "retrieval_ms": retrieval_ms,
    "reranking_ms": reranking_ms,
    "retrieved_chunks": retrieved_chunks_meta,
    "reranked_order": [r["chunk_id"] for r in final_results],
})
```

---

### P1-3: 사용자 피드백 버튼 + API ✅

**구현 내용**

- `frontend/src/components/ChatMessage.jsx` — 답변 하단 👍👎 버튼 (비로그인 상태 숨김)
- `backend/app/api/chat.py` — 피드백 엔드포인트:

```
POST /api/chat/messages/{message_id}/feedback
body: {"score": 1 | -1}
```

- 소유자(세션 기준) 검증 후 `QueryLog.feedback_score` 업데이트

---

### P1-4: 출처 클릭 트래킹 ✅

**구현 내용**

- `ChatMessage.jsx` — 출처 배지 클릭 시 이벤트 전송 + 원문 팝업 오픈
- `backend/app/api/chat.py` — 클릭 트래킹 엔드포인트:

```
POST /api/chat/messages/{message_id}/source-click
body: {"chunk_id": "..."}
```

- `QueryLog.click_source_flag = True` 업데이트

---

### P1-5: 저신뢰도 경고 배지 ✅

**구현 내용**

`frontend/src/components/ChatMessage.jsx` — 신뢰도 구간별 UI 차별화:

| 신뢰도 구간 | 배지 | 색상 |
|------------|------|------|
| ≥ 0.7 | 신뢰도 높음 | 초록 (emerald) |
| 0.4 ~ 0.7 | 보통 | 노랑 (amber) |
| < 0.4 | ⚠ 근거 부족 | 빨강 (red) |

---

## 3. Phase 2 구현 결과

> **목표**: KPI 대시보드 UI + 데이터 품질 향상  
> **완료 기간**: 계획 1개월 → **실제 구현 완료**

### P2-1: 5탭 KPI 대시보드 UI ✅

**구현 내용**

`frontend/src/pages/admin/SettingsPage.jsx` — 5탭 구조로 전환:

| 탭 | 내용 |
|----|------|
| Executive | 총 질의 수, 평균 신뢰도, 평균 응답시간, 활성 사용자 수 카드 + 주간 추이 |
| Retrieval | 검색 단계별 지연시간, Reranking Lift 통계 |
| Answer Trust | 신뢰도 분포 파이 차트, 피드백 통계 |
| Operations | 문서 현황, OCR 처리 통계, 인덱싱 성공률 |
| Governance | 감사 로그, Policy Violation 건수, Access Denied 현황 |

---

### P2-2: 응답 단계별 지연시간 차트 ✅

`SettingsPage.jsx` — Retrieval / Reranking / LLM 단계 분리 스택 바 차트  
데이터 소스: `GET /api/admin/query-logs` → `retrieval_ms`, `reranking_ms`, `llm_ms`

---

### P2-3: 신뢰도 분포 차트 ✅

`SettingsPage.jsx` — High(≥0.7) / Medium(0.4~0.7) / Low(<0.4) 파이 차트  
데이터 소스: `confidence_score` 구간별 집계

---

### P2-4: User.department 필드 추가 ✅

- `backend/app/models/user.py` — `department: Optional[str]` 추가
- `backend/app/schemas/user.py` — 응답 스키마 반영
- `frontend/src/pages/admin/UsersPage.jsx` — 부서 필드 표시/편집
- **마이그레이션**: `alembic/versions/0005_user_department.py`

---

### P2-5: 문서 페이지 번호 저장 ✅

**구현 내용**

- `backend/app/models/document.py` — `DocumentChunk`에 `page_number`, `source_type` 추가
- `backend/app/rag/chunker.py` — PDF/DOCX 청킹 시 페이지 번호 추출 저장
- `backend/app/rag/retriever.py` — 검색 결과에 `page_number` 포함 반환
- `frontend/src/components/ChatMessage.jsx` — 출처 배지에 `문서명 p.N` 형식 표시
- **마이그레이션**: `alembic/versions/0004_chunk_page_number.py`

---

### P2-6: 신뢰 UX 하이라이트 ✅

`frontend/src/components/ChatMessage.jsx` — 출처 배지 클릭 시 원문 팝업 내 인용 구간 하이라이트  
`ReactDOM.createPortal(document.body)` 방식으로 모달 렌더링 (overflow 클리핑 방지)

---

### P2-7: Active User Rate KPI API ✅

`backend/app/api/admin.py` — 활성 사용자 집계 엔드포인트 추가:

```
GET /api/admin/active-users?period=7   → 최근 7일 활성 사용자 수/비율
GET /api/admin/active-users?period=30  → 최근 30일
```

---

## 4. Phase 3 구현 결과

> **목표**: 보안 강화 + 품질 측정 체계 + 고급 기능  
> **완료 기간**: 계획 3개월 → **실제 구현 완료**

### P3-1: Guardrail Engine ✅

**구현 내용**

`backend/app/services/guardrail_service.py` — 독립 모듈로 구현:

```python
BLOCKED_CATEGORIES = [
    "개인정보 요청 (PII)",     # 주민번호, 카드번호 등
    "해킹/악성코드",
    "비관련 잡담",
    "폭력/혐오 표현",
]
```

- 질문 전처리 단계에서 선제 차단 (RAG 파이프라인 진입 전)
- 차단 시 `QueryLog.feedback_score = -2` (Policy Violation 마킹)
- KPI 대시보드 Governance 탭에 위반 건수 표시

**API 테스트 결과**: PII 질문 → HTTP 400 정상 차단 확인 ✅

---

### P3-2: RAG 평가 스크립트 ✅

**구현 내용**

`scripts/eval_rag.py` — 자동 평가 지표 산출:

| 지표 | 설명 |
|------|------|
| Precision@K | 상위 K개 중 관련 청크 비율 |
| Recall@K | 정답 청크 포함 여부 |
| MRR | Mean Reciprocal Rank |
| nDCG@K | 순위 가중 품질 지표 |
| Reranking Lift | Cross-encoder 적용 전후 Precision 개선폭 |

`scripts/eval_testset.json` — 샘플 테스트셋 5개 질문 포함

---

### P3-3: HyDE 검색 모드 ✅

**구현 내용**

HyDE(Hypothetical Document Embeddings): 질문에 대한 가상 답변 문서를 LLM으로 먼저 생성한 뒤, 그 문서의 임베딩으로 검색하는 고정확도 모드.

**연결 체인**:
```
AskRequest.use_hyde=true
  → api/chat.py (ask / ask/stream)
  → rag_service.py (ask_question / ask_question_stream / _build_rag_context)
  → retriever.py (retrieve_relevant_chunks → _generate_hyde_document → embed)
```

**UI**: 채팅 입력창 왼쪽 💡 버튼으로 토글
- 비활성 (기본): 일반 검색 모드 (회색 아이콘)
- 활성: HyDE 모드 (앰버색 아이콘, 주황 테두리, 안내 문구 표시)

**트레이드오프**: LLM 2회 호출(가상 문서 생성 + 답변 생성) → 응답시간 +5~10초, 검색 정확도 향상

---

### P3-4: JWT HttpOnly 쿠키 전환 ✅

**구현 내용**

- `backend/app/api/auth.py` — 로그인 응답 시 `Set-Cookie: access_token; HttpOnly; SameSite=Strict`
- `frontend/src/api/client.js` — `credentials: 'include'` 설정, localStorage 토큰 제거
- Axios 인터셉터 → 쿠키 기반 401 처리 + 자동 refresh 재시도

**보안 효과**: XSS 공격으로 localStorage 토큰 탈취 불가

---

### P3-5: Refresh Token 폐기 (DB 블랙리스트) ✅

**구현 내용**

- `backend/alembic/versions/0006_refresh_token_blacklist.py` — `token_blacklist` 테이블 생성
- `backend/app/services/auth_service.py` — 로그아웃 시 refresh token 블랙리스트 등록
- `POST /api/auth/logout` — 토큰 폐기 후 쿠키 삭제

**보안 효과**: 탈취된 refresh token을 사용한 무단 연장 방지

---

### P3-6: Document Lineage ✅

**구현 내용**

- `backend/app/models/document.py` — `Document` 모델에 계보 추적 필드 추가:

```python
uploaded_by: str          # 업로드 사용자 ID
chunk_count: int          # 파생된 청크 수
last_modified_at: datetime
parent_document_id: Optional[str]  # 재업로드 원본 참조
```

- `backend/alembic/versions/0007_document_lineage.py` — 마이그레이션
- `backend/app/api/documents.py` — 문서 상세 API에 lineage 정보 포함

---

### P3-7: 테스트 코드 ✅

**백엔드 (pytest)**

`backend/tests/` — 3개 테스트 모듈:

| 파일 | 테스트 내용 | 테스트 수 |
|------|------------|----------|
| `test_auth_service.py` | JWT 생성/검증, 토큰 만료 | 8개 |
| `test_security.py` | 비밀번호 해싱, RBAC 권한 | 6개 |
| `test_guardrail.py` | PII 차단, 정상 질문 통과 | 8개 |

**프론트엔드 (jest)**

`frontend/src/__tests__/` — 4개 테스트 모듈:

| 파일 | 테스트 내용 | 테스트 수 |
|------|------------|----------|
| `AuthContext.test.jsx` | 로그인/로그아웃 컨텍스트 | 8개 |
| `ChatMessage.test.jsx` | 신뢰도 배지, 피드백 버튼 | 9개 |
| `ErrorBoundary.test.jsx` | 에러 렌더링, 복구 버튼 | 7개 |
| `ProtectedRoute.test.jsx` | 인증 리다이렉트 | 6개 |

---

### P3-8: 멀티모달 (qwen2.5-vl 연동) ✅

**구현 내용**

`backend/app/rag/loader.py` — 페이지 텍스트 부족 시 비전 모델 자동 호출:

```python
OCR_MIN_TEXT_PER_PAGE = 30  # 페이지당 최소 텍스트 길이

if len(page_text) < OCR_MIN_TEXT_PER_PAGE:
    page_text = call_vision_model(page_image_base64)  # qwen2.5vl:7b
```

- PDF 스캔본, 이미지 기반 페이지 자동 처리
- 비동기 블로킹 방지: `loop.run_in_executor()` 래핑 (2026-04-12 버그픽스 포함)

---

## 5. 커밋 이력

| 커밋 해시 | 날짜 | 내용 |
|----------|------|------|
| `d23f1d5` | 2026-04-12 | docs: ISP 계획서 완료 현황 업데이트 |
| `3235e17` | 2026-04-12 | feat: P3-3 HyDE 검색 모드 전체 연결 + UI 토글 |
| `2ea6511` | 2026-04-12 | fix: document_service async blocking (run_in_executor) |
| `e6e85a6` | 2026-04-12 | feat: P3-7 jest 프론트엔드 테스트 30개 추가 |
| `395bf96` | 2026-04-12 | fix: api_test.py logout 상태코드 수정 |
| `b40b803` | 2026-04-12 | fix: auth.py 중복 라우터 제거, api_test.py 쿠키 전환 |
| `f148132` | 2026-04-12 | feat: ISP Phase 1~3 전체 구현 완료 |
| `a4377f4` | 이전 | fix: 신뢰도 점수 sigmoid 변환 + 가중 평균 |

---

## 6. 시스템 검증 결과

### 6.1 전체 API 테스트 (`scripts/api_test.py`)

**최종 실행 결과 (2026-04-12)**:

```
전체: 34개  |  [OK] 통과: 34개  |  [NG] 실패: 0개
```

| 섹션 | 항목 수 | 결과 |
|------|---------|------|
| 1. 서버 헬스체크 | 2 | ✅ 전체 통과 |
| 2. 인증 (로그인/refresh/me) | 5 | ✅ 전체 통과 |
| 3. 사용자 관리 (admin) | 3 | ✅ 전체 통과 |
| 4. 문서 목록/IDOR 방지 | 2 | ✅ 전체 통과 |
| 5. 문서 업로드/처리 | 4 | ✅ 전체 통과 |
| 6. 검색 (hybrid/vector/keyword) | 3 | ✅ 전체 통과 |
| 7. 채팅 세션 및 QA | 4 | ✅ 전체 통과 |
| 8. 스트리밍 QA | 3 | ✅ 전체 통과 |
| 9. Guardrail (PII 차단) | 2 | ✅ 전체 통과 |
| 10. 감사 로그 및 접근 제어 | 2 | ✅ 전체 통과 |
| 11. 로그아웃 및 토큰 폐기 | 2 | ✅ 전체 통과 |
| 12. 테스트 데이터 정리 | 2 | ✅ 전체 통과 |

### 6.2 실측 KPI (테스트 기준)

| KPI | 목표값 | 실측값 | 판정 |
|-----|--------|--------|------|
| End-to-End 응답시간 (일반 모드) | 8초 이하 | **~4~6초** | ✅ |
| 검색 단계 (`retrieval_ms`) | 1,500ms 이하 | **~200~400ms** | ✅ |
| Reranking 단계 (`reranking_ms`) | 500ms 이하 | **~100~200ms** | ✅ |
| 답변 신뢰도 (테스트 문서) | 70% 이상 | **0.999** | ✅ |
| Guardrail 차단율 | PII 100% 차단 | **100%** | ✅ |
| 인덱싱 성공률 | 98% 이상 | **100%** | ✅ |

### 6.3 보안 검증

| 항목 | 결과 |
|------|------|
| XSS 방어 (HttpOnly Cookie) | ✅ localStorage 토큰 없음 |
| IDOR 방어 (문서 접근 제어) | ✅ 타 사용자 문서 403 확인 |
| 토큰 폐기 (블랙리스트) | ✅ 로그아웃 후 refresh 거부 확인 |
| PII 차단 (Guardrail) | ✅ 주민번호/카드번호 패턴 400 확인 |

---

## 7. 아키텍처 달성 수준

```
[User / Channel Layer]
임직원 포털 | React UI
✅ 구현됨

[AI Experience & Access Layer]
RBAC | HttpOnly Cookie 인증 | Prompt UI | 문서 필터
✅ 구현됨

[AI Orchestration & Control Plane]
Guardrail Engine | Audit Logger | Policy Violation 기록
✅ P3-1 구현됨

[BAIKAL RAG Engine]
Hybrid Search (Vector 70% + BM25 30%) | MMR | Cross-encoder
HyDE 모드 | Semantic Chunking
✅ 완성 + P3-3 HyDE 추가

[Knowledge & Data Layer]
HWP/PDF/DOCX/XLSX | pgvector | Page# | Document Lineage
✅ P2-5 + P3-6 구현됨

[LLM Runtime (Private AI)]
Ollama (qwen2.5:7b + bge-m3 + qwen2.5vl:7b)
외부 API 의존 0, 완전 폐쇄망 동작
✅ 완성

[Infrastructure Layer]
Docker Compose (5 컨테이너)
백엔드 8000 | 프론트엔드 3000 | nginx 80 | postgres | ollama
✅ 완성

[Security & Governance Layer]
KPI Dashboard | Audit Trail | Zero Trust (토큰 폐기) | RBAC
✅ P2-1 + P3-4 + P3-5 구현됨
```

**달성 수준**: 계획한 8개 레이어 **전체 구현 완료**

---

## 8. 잔여 과제

### 8.1 기술 잔여 (선택적 고도화)

| 항목 | 내용 | 우선순위 |
|------|------|----------|
| GPU 가속 | CPU 모드 → GPU 서버 전환 시 응답시간 50~80% 단축 | 인프라 결정 후 |
| K8s 배포 | Docker Compose → Kubernetes (고가용성) | 고객 유치 후 |
| SSO 연동 | LDAP/SAML 기업 계정 연동 | 파일럿 고객 요구 시 |

### 8.2 비즈니스 병행 과제 (코드 외)

| 항목 | 내용 | 권장 시점 |
|------|------|----------|
| **SI 수용 기준 문서화** | 커스터마이징 허용 범위 정책 결정 | **즉시** |
| **Anchor Customer 발굴** | 공공기관 1곳 + 제조기업 1곳 파일럿 후보 선정 | **즉시** |
| **Use-case 패키지 작성** | "규정 검색 AI" 등 3종 상품 패키지 문서 | 1개월 내 |
| **파트너 채널 검토** | SI 업체/보안 솔루션 업체 접촉 | 2개월 내 |

### 8.3 운영 모니터링 필요 항목

실제 파일럿 운영 시 KPI 목표 대비 실측값 추적:

- **Query Success Rate** (피드백 긍정 70% 이상)
- **Source Click-through Rate** (30% 이상)
- **활성 사용자율 WAU** (60% 이상)

---

> **문서 끝** | BAIKAL Private AI ISP 개선 구현 결과서  
> 작성: 2026-04-12 기준 | 본 문서는 [ISP_IMPROVEMENT_PLAN.md](./ISP_IMPROVEMENT_PLAN.md)의 구현 결과를 기록한 문서입니다.
