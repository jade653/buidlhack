# Agent Challenge Platform — CLAUDE.md

## 프로젝트 개요

에이전트 챌린지 플랫폼. 기업이 챌린지를 올리고, 유저(또는 자율 에이전트)가 멀티 에이전트를 제출해 경쟁하며 바운티를 받는다. 핵심 차별점은 에이전트 코드와 결과물이 TEE 안에서만 실행되어 플랫폼조차 내용을 볼 수 없다는 것. NEAR 해커톤 트랙 제출용.

---

## 아키텍처 레이어 (5단계)

```
LAYER 1: ACTORS
  ├── User          → 브라우저에서 에이전트 파일 업로드 (TEE 공개키로 암호화)
  ├── Auto Agent    → REST API 또는 Browser Use로 자율 참여
  └── Enterprise    → 챌린지 등록 + 바운티 NEAR 토큰 예치

LAYER 2: PLATFORM BACKEND (FastAPI)
  └── 암호문만 중계, 내용 열람 불가
      점수(평문)만 수신 → DB 저장 → 리더보드
      크레딧 차감 (토큰 사용량 기반)

LAYER 3: PHALA CLOUD TEE (우리 Docker 이미지, 상시 실행)
  ├── Shade Agent SDK (@neardefi/shade-agent-js, TypeScript)
  │     TEE 부팅 → 임시 NEAR 계정 생성
  │     agent.register() → attestation 생성 → NEAR 컨트랙트 제출
  │     agent.call("submit_score") → 점수 온체인 기록
  │
  ├── 플랫폼 실행 엔진 + 샌드박스 (Python)
  │     유저 파일 복호화 (TEE 내부에서만)
  │     RestrictedPython 샌드박스로 harness.py 실행
  │     LangGraph / CrewAI 오케스트레이션 (유저가 자유롭게 구성)
  │     TokenTracker 콜백으로 LLM 호출별 토큰 집계
  │     실행 시간 측정 (Speed 메트릭)
  │
  └── Near AI Cloud (LLM inference, TEE 보장)
        inference.near.ai/v1 (OpenAI compatible)
        플랫폼 API 키 사용 (유저에게 노출 안 됨)
        멀티 에이전트 각 노드가 LLM 호출 시 사용
        사용 모델: deepseek-r1, qwen3, glm-5 등

  TEE OUTPUT:
    score: float          → 평문, 리더보드용
    encrypted_output      → 기업 공개키로 암호화, DB 잠금 보관
    wall_time_sec: float  → Speed 메트릭
    token_usage: dict     → 에이전트별 토큰 사용량
    attestation           → NEAR 컨트랙트 제출

LAYER 4: NEAR PROTOCOL (온체인)
  ├── Agent Contract (Rust, Shade Agent 기반)
  │     register_agent(attestation) → TEE 실행 검증 [Shade Agent 기본 제공]
  │     approve_measurements(hash)  → Docker 코드해시 검증 [Shade Agent 기본 제공]
  │     submit_score(score, user)   → 점수 온체인 기록 [우리가 추가]
  │     release_bounty(winner)      → 바운티 자동 지급 [우리가 추가]
  │     lock_output(encrypted)      → 결과 잠금 관리 [우리가 추가]
  │
  ├── Leaderboard (온체인 점수 기록, 조작 불가)
  └── Bounty Vault (기업 예치금 잠금, 마감 후 자동 지급)

LAYER 5: OUTPUT
  ├── 리더보드 실시간 업데이트 (WebSocket)
  ├── 유저 크레딧 차감
  └── 기업: 암호화 결과 + 복호화 키 수령 (바운티 지급 후)
```

---

## 핵심 데이터 흐름

```
[유저] harness.py 업로드
  → 브라우저에서 TEE 공개키로 암호화
  → Platform Backend (암호문만 통과, 내용 못 봄)
  → Phala TEE 수신
  → 복호화 (TEE 내부에서만)
  → 샌드박스에서 harness.py 실행
  → Near AI Cloud로 LLM 호출 (에이전트별 여러 번)
  → 점수 계산
  → Shade Agent: attestation 생성 → NEAR 컨트랙트 submit_score()
  → score(평문) → Platform DB → 리더보드
  → encrypted_output → DB 잠금 보관
  → token_usage → 유저 크레딧 차감

[기업] 바운티 지급 결정
  → NEAR 컨트랙트 release_bounty()
  → encrypted_output + 복호화 키 → 기업 전달
```

---

## 유저 에이전트 파일 구조

```
submission/
├── harness.py       # 필수. 실행 진입점. LangGraph/CrewAI 오케스트레이션 정의
├── agent.md         # 필수. 에이전트 시스템 프롬프트
├── config.json      # 선택. 모델명, 파라미터 등
└── rag/             # 선택. RAG 문서
    └── documents/
```

harness.py 표준 인터페이스:
```python
# 플랫폼이 주입하는 환경
# - llm: SandboxedNearAIClient (API 키 숨김)
# - challenge_input: dict (챌린지 데이터셋)
# 반환값 형식
result = {
    "output": ...,   # 챌린지 결과물
    "score": float,  # 자체 평가 점수 (옵션)
}
```

---

## 점수 산정

```
final_score = quality_score * 0.7 + speed_score * 0.3

quality_score: 챌린지별 기업이 정의한 평가 함수 적용
speed_score:   wall_time 기준 상대 순위 (가장 빠른 제출 = 100점)

Speed 불이익: LLM 호출 횟수 많을수록, 총 토큰 많을수록 감점 가능
```

---

## 비용 구조

```
유저 크레딧:
  1 credit = 1,000 토큰
  충전: NEAR 토큰으로 선불
  차감: 실행 완료 후 실제 token_usage 기준

실행 시작 전: 최대 크레딧 예약 (잠금)
실행 완료 후: 실제 사용량만 차감, 나머지 반환

Phala Cloud 실행 비용: 플랫폼이 흡수 (챌린지 참여 고정 요금에 포함)
```

---

## 보안 모델

```
플랫폼 서버:  에이전트 코드 못 봄 (암호화된 채로 포워딩)
다른 유저:    경쟁자 코드 못 봄 (TEE 내부 실행)
플랫폼 운영자: 점수 조작 불가 (NEAR 컨트랙트 + attestation)
기업:          결과물은 바운티 지급 전까지 암호화 잠금
```

---

## 기술 스택

| 레이어 | 기술 | 용도 |
|--------|------|------|
| 프론트엔드 | Next.js + TypeScript | 웹 플랫폼 UI, 리더보드 |
| 백엔드 | FastAPI (Python) | API 서버, 크레딧 정산 |
| DB | PostgreSQL + Redis | 점수/크레딧 저장, 캐싱 |
| TEE 인프라 | Phala Cloud (Dstack) | Docker 실행 환경 |
| TEE 증명 | Shade Agent SDK (NearDeFi) | attestation, NEAR 연동 |
| 에이전트 오케스트레이션 | LangGraph / CrewAI | 멀티 에이전트 실행 |
| LLM | Near AI Cloud | TEE LLM inference |
| 샌드박스 | RestrictedPython | 유저 코드 격리 |
| 온체인 | NEAR 스마트 컨트랙트 (Rust) | 점수 기록, 바운티 |
| 지갑 | NEAR Wallet | 유저/기업 인증 |

---

## 디렉토리 구조 (목표)

```
/
├── frontend/                  # Next.js
│   ├── pages/
│   │   ├── challenges/        # 챌린지 목록/상세
│   │   ├── submit/            # 에이전트 제출 (Monaco Editor / GitHub 연결)
│   │   └── leaderboard/       # 실시간 리더보드
│   └── components/
│
├── backend/                   # FastAPI
│   ├── api/
│   │   ├── challenges.py      # 챌린지 CRUD
│   │   ├── submissions.py     # 에이전트 제출 처리
│   │   ├── leaderboard.py     # 점수 조회
│   │   └── credits.py         # 크레딧 정산
│   └── services/
│       └── tee_forwarder.py   # Phala TEE로 포워딩
│
├── tee-engine/                # Phala TEE Docker 이미지
│   ├── Dockerfile             # Node + Python 모두 포함
│   ├── agent/                 # TypeScript (Shade Agent SDK)
│   │   ├── register.ts        # TEE 등록, attestation
│   │   └── submit_score.ts    # NEAR 컨트랙트 호출
│   ├── engine/                # Python (실행 엔진)
│   │   ├── sandbox.py         # RestrictedPython 샌드박스
│   │   ├── runner.py          # harness.py 실행
│   │   ├── tracker.py         # TokenTracker, Speed 측정
│   │   └── evaluator.py       # 점수 계산
│   └── docker-compose.yaml    # Phala Cloud 배포용
│
├── contract/                  # NEAR 스마트 컨트랙트 (Rust)
│   └── src/
│       └── lib.rs             # register_agent + submit_score + release_bounty
│
└── CLAUDE.md                  # 이 파일
```

---

## 구현 우선순위 (해커톤 MVP)

```
Phase 1: 핵심 플로우
  [ ] NEAR 컨트랙트 기본 (register_agent + submit_score)
  [ ] Phala TEE Docker 이미지 (Shade Agent SDK + Python 샌드박스)
  [ ] harness.py 실행 + Near AI Cloud 연동
  [ ] 점수 반환 + 리더보드 기본 UI

Phase 2: 플랫폼
  [ ] 챌린지 등록/조회 API
  [ ] 에이전트 파일 업로드 UI (Monaco Editor)
  [ ] 크레딧 시스템
  [ ] WebSocket 실시간 리더보드

Phase 3: 차별화
  [ ] GitHub 프라이빗 레포 연동
  [ ] Speed 메트릭 + 종합 점수
  [ ] 바운티 자동 지급 (release_bounty)
  [ ] 자율 에이전트 REST API
```

---

## 주요 제약사항 / 알아야 할 것

- Shade Agent SDK는 TypeScript 전용 → TEE 안에서 TypeScript(증명) + Python(실행) 두 프로세스 분리
- RestrictedPython 샌드박스: os, subprocess, socket, open 차단 / langgraph, crewai, openai 허용
- Near AI Cloud: OpenAI compatible API, 현재 베타. 코드 실행 TEE가 아닌 LLM inference TEE
- Shade Agent Framework: 2026년 4월 이후 공식 유지보수 종료, 오픈소스로 계속 사용 가능
- docker-compose.yaml의 codehash가 바뀌면 NEAR 컨트랙트의 approve_measurements 재호출 필요
- 유저 harness.py는 반드시 표준 인터페이스(llm, challenge_input 주입)를 따라야 함
