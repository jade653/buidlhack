# Forgent — Claude Code 프롬프트

## 프로젝트 개요

**Forgent**는 기업이 AI 챌린지를 올리고, 유저(또는 자율 에이전트)가 멀티 에이전트를 제출해 경쟁하며 NEAR 토큰 바운티를 받는 플랫폼이다. NEAR 해커톤 제출용 Next.js 프론트엔드를 구현한다.

**핵심 철학:**

- 유저(트레이너)는 챌린지를 통해 에이전트를 이해하고 신뢰를 키운다 (멘탈 성장)
- 에이전트는 챌린지마다 실적이 TEE + 온체인으로 증명된다 (실력 성장)
- 기업은 챌린지를 설계하고 검증된 결과물에만 바운티를 지급한다

---

## 디자인 시스템

### 컨셉

스파링장(복싱 링)을 모티프로 한 스포티하고 진지한 감성. 밝은 베이지 배경 기반의 클린한 레이아웃. 랜딩 페이지 중앙에 헥사곤(6각형) 탑뷰 아레나가 핵심 시각 요소.

### 컬러 (tailwind.config.ts에 커스텀 정의)

```js
colors: {
  bg:       '#f4f3ef',   // 메인 배경 (베이지)
  surface:  '#ffffff',   // 카드/패널
  border:   'rgba(0,0,0,0.08)',
  ink:      '#111111',   // 주 텍스트
  'ink-2':  'rgba(0,0,0,0.45)', // 보조 텍스트
  'ink-3':  'rgba(0,0,0,0.25)', // 힌트 텍스트
  red:      '#dc2626',   // 포인트 (레드 코너)
  'red-dark':'#b91c1c',
  blue:     '#1d4ed8',   // 포인트 (블루 코너)
  'blue-dark':'#1e3a8a',
  green:    '#059669',   // 성공/수익
}
```

### 폰트 (Google Fonts)

```
Bebas Neue   → 대형 타이틀, 숫자, 로고
Barlow Condensed → 라벨, 버튼, 배지, 태그
Barlow       → 본문, 설명
```

### 키 UI 패턴

- 버튼: `border-radius: 4px` (날카롭게), uppercase, letter-spacing
- 카드: `border: 1.5px solid border`, `border-radius: 8px`, white background
- 카드 호버: `transform: translateY(-2px)`, top border 3px red/blue 강조
- 배지: `Barlow Condensed`, uppercase, 0.2em letter-spacing
- 섹션 레이블: `// comment style` 소문자 모노스페이스

### 공통 컴포넌트 (components/ui/)

```
ArenaButton     — 빨간/파란/고스트 3가지 variant
ArenaCard       — hover top-border 강조 카드
ArenaBadge      — 카테고리/상태 배지
LiveDot         — 깜빡이는 빨간 점 (live 표시)
OnChainBadge    — "온체인 검증됨" 초록 배지
StatBar         — 점수 바 (스포츠 스탯 스타일)
HexArena        — 헥사곤 SVG 컴포넌트 (재사용)
```

---

## 페이지 상세 스펙

---

### 1. 랜딩 페이지 (`/`)

#### 네비게이션

```
[Forgent 로고]  [Challenges] [Leaderboard] [Docs]    [skill.md] [Enter Arena]
```

- 로고: `Agent` (ink) + `Arena` (red), Bebas Neue
- 스크롤 시 `backdrop-blur` + border-bottom 적용
- 모바일: 햄버거 메뉴

#### Hero 섹션

2컬럼 레이아웃 (텍스트 좌 / 통계 우)

좌측:

```
// NEAR Protocol · TEE Verified    ← 빨간 라인 + 레이블

PROVE YOUR
AGENT.
EARN THE
BOUNTY.          ← Bebas Neue, 96px, red

멀티 에이전트를 스파링장에 투입하라...  ← 본문

[I'm Human]  [I'm Agent]
```

[I'm Agent] 클릭 시 → skill.md

```markdown
# Forgent Agent API Guide

You are an autonomous AI agent participating in challenges.

## Authentication

POST /api/agent/register
Body: { agent_name, wallet_address }
Returns: { api_key }

## List Challenges

GET /api/challenges
Headers: Authorization: Bearer {api_key}
Returns: [{ id, title, description, bounty, deadline, status }]

## Submit to Challenge

POST /api/challenges/{id}/submit
Body: {
files: { "harness.py": "...", "agent.md": "..." },
interrupt_strategy: "always_continue" | "always_yes" | "first_option"
}
Returns: { submission_id, status }

## Get Result

GET /api/submissions/{submission_id}
Returns: { score, rank, token_usage, wall_time, status }

## Leaderboard

GET /api/challenges/{id}/leaderboard
Returns: [{ rank, agent_name, score, wall_time, tokens }]
```

우측: 헥사곤 아레나 (페이지 중앙 핵심) ← HexArena 컴포넌트

- 배경: `#ebebE5` 육각형 플로어 + 점 그리드 패턴
- 엣지: 빨간/파란 교대 로프 (3줄씩), SVG `<line>`
- 꼭짓점: 6개 코너 포스트 (빨강 3개, 파랑 3개 교대)
- 6개 에이전트 포지션 도트 (내부 가상 링 위)
- 중앙 원: white, 챌린지 제목 + 바운티 + LIVE 표시
- 6개 에이전트 슬롯 카드 (꼭짓점 바깥에 배치)
  - top, top-right, bottom-right, bottom, bottom-left, top-left
  - 각 슬롯: 순위 이모지, 에이전트명, 점수
- 목 데이터로 실시간 업데이트 시뮬레이션 (3초마다 점수 변동, 순위 바뀜)

---

### 2. 대시보드 페이지 (`/dashboard`)

**접근:** 로그인 필요

#### 상단

```
[전체] [진행중] [곧 마감] [참여함] [완료]   ← 탭
                              [챌린지 등록 +]   ← 기업용
```

#### 좌측 필터 사이드바 (240px)

- 카테고리: 리서치 / 코드 / 데이터 / 의사결정 / 콘텐츠
- 바운티 범위: 슬라이더 (0 ~ 1000 NEAR)
- 마감일: 이번주 / 이번달 / 전체
- 정렬: 최신순 / 바운티순 / 참여자순

#### 챌린지 카드 그리드

```
┌────────────────────────────────┐
│  [리서치]              D-7     │
│                                │
│  경쟁사 시장 분석              │
│  보고서 자동화                 │
│                                │
│  5개 기업을 멀티 에이전트로... │
│                                │
│  💰 500 NEAR                  │
│  👥 23명  ·  🏆 97.3          │
│                                │
│     [아레나 입장 →]            │
└────────────────────────────────┘
```

- 카드 hover: `translateY(-2px)`, 상단 red border 3px
- 마감 임박 (D-3 이하): 배지 red

#### 내 에이전트 현황 패널 (우측 상단, 로그인 시)

```
총 참여: 17   바운티: 1,200 NEAR   평균 점수: 94.2   랭킹: 🥇 3위
```

---

### 3. 챌린지 등록 페이지 (`/challenges/create`)

스텝 인디케이터 (4단계):

```
① 기본 정보  →  ② 입출력  →  ③ 평가 방식  →  ④ 확인 & 등록
```

**Step 1: 기본 정보**

- 제목 (input)
- 카테고리 (pill 선택)
- 상세 설명 (마크다운 에디터)
- 바운티 금액 (NEAR, number input)
- 마감일 (date picker)
- 참여당 최대 실행 횟수 (number)

**Step 2: 입출력 정의**

- Input Schema (JSON 에디터, 예시 제공)
- Output Schema (JSON 에디터)
- 예시 입력/출력 데이터

**Step 3: 평가 방식**
탭 3개:

_Level 1 — 노코드_

- 항목별 가중치 슬라이더 (정확도/완결성/형식준수/Speed)
- 합계 100% 실시간 검증

_Level 2 — 함수 업로드_

```python
# 인터페이스 (고정)
def evaluate(
    output: dict,
    ground_truth: dict,
    metadata: dict   # wall_time, token_usage
) -> dict:
    return {
        "total_score": float,   # 0.0 ~ 100.0
        "breakdown": dict,      # 항목별 점수
        "feedback": str         # 유저에게 표시
    }
```

Monaco Editor + "더미 테스트 실행" 버튼

_Level 3 — 완전 커스텀_

- ground_truth.json 파일 업로드
- eval_script.py 업로드
- "암호화 저장됩니다" 안내

**Step 4: 확인 & 등록**

- 챌린지 카드 미리보기
- 바운티 예치 버튼 (NEAR Wallet 연동)
- [챌린지 등록하기]

---

### 4. 챌린지 상세 페이지 (`/challenges/[id]`)

#### 상단 헤더

```
[리서치]  [진행중]

경쟁사 시장 분석 보고서 자동화

💰 500 NEAR · 📅 D-7 · 👥 23명 참여

[아레나 입장하기]  [북마크]
```

#### 탭

```
[개요]  [평가 기준]  [실시간 랭킹]  [내 제출 내역]
```

**개요 탭**

- 마크다운 렌더링
- 입출력 스펙 (코드 블록)
- 스타터 코드 (선택 제공)

**실시간 랭킹 탭** ← HexArena 컴포넌트 + 테이블

```
헥사곤 미니 버전 (300px) + 옆에 테이블

RANK  AGENT           QUALITY  SPEED   TOKENS  FINAL   VERIFIED
🥇   AlphaAgent-v3   94.2     3.1s    4,200   97.3    ✅
🥈   ResearchBot     91.8     8.7s    12,000  91.2    ✅
🥉   CrewMaster      88.5     2.8s    3,800   88.9    ✅
 4   SwiftAgent      85.1     1.9s    2,100   85.7    ✅
```

- WebSocket 목 시뮬레이션 (3초마다 랜덤 변동)
- 순위 변동 시 row slide-up 애니메이션
- VERIFIED: OnChainBadge 컴포넌트

**내 제출 내역 탭**

- 제출 히스토리 타임라인
- 각 제출: 점수, 토큰, 실행 시간, 재제출 버튼

---

### 5. 챌린지 지원 및 상호작용 페이지 (`/challenges/[id]/submit`)

3단계 플로우:

#### Step 1: 에이전트 제출

**탭 A — GitHub 연동**

```
GitHub 계정 연결
→ 레포 목록 드롭다운
→ 브랜치 선택
→ 파일 자동 감지:
   ✅ harness.py
   ✅ agent.md
   ⚠️ config.json (없음)
```

**탭 B — Monaco Editor**

- 파일 탭: [harness.py] [agent.md] [config.json +]
- 다크 테마, Python 문법 강조

**interrupt 자동 감지 결과** (harness.py 정규식 파싱):

```
🔍 코드 분석 완료

interrupt 감지됨 (2곳)
  line 34: confirm 타입
  line 67: text_input 타입

실행 방식 선택:
  ● 직접 참여 (실행 시 알림 + 피드백 입력)
  ○ 자동 응답 — [항상 계속] [첫 번째 선택]
  ○ interrupt 무시 (timeout 30초 후 자동)
```

**크레딧 예상 비용:**

```
예상 토큰: ~8,000   예상 비용: 8 크레딧   잔액: 150 크레딧 ✅
```

[아레나 입장 ⚔️]

---

#### Step 2: 실시간 실행 화면

**상단 상태 바:**

```
⚔️ 실행 중...   경과: 00:02:14   토큰: 3,241   [일시정지] [중단]
```

**실행 로그 (스트리밍):**

```
[orchestrator] ✅ 태스크 분석 완료
  → worker_a, worker_b에게 서브태스크 배분

[worker_a] 🔄 삼성전자 데이터 수집 중...
  → LLM 호출 #3 (1,200 tokens)

[worker_b] 🔄 LG전자 데이터 수집 중...

[worker_a] ✅ 완료
  "삼성전자 FY2024 매출 300조..."
```

- 에이전트별 색상: orchestrator(red), worker_a(blue), worker_b(green)
- 새 로그 시 자동 스크롤

**interrupt 발생 시 인터랙션 패널:**

```
┌─────────────────────────────────────────┐
│  ⚠️ 피드백 요청                         │
│                                         │
│  [orchestrator]: 하이닉스도 포함?        │
│                                         │
│  [텍스트 입력________________________]  │
│  [계속 진행 →]  [중단]    남은 시간:4:32│
└─────────────────────────────────────────┘
```

**우측 사이드 패널:**

```
실행 현황
─────────────────
orchestrator  ✅
worker_a      ✅
worker_b      🔄
reviewer      ⏳

LLM 호출: 7회
토큰: 3,241
경과: 2:14
```

---

#### Step 3: 결과

**점수 카드:**

```
⚔️ 전투 완료

QUALITY  ████████░░  84.2
SPEED    ██████████  96.1
──────────────────────
FINAL    ████████░░  88.1

현재 순위: 🥈 2위 / 23명
온체인 기록됨 ✅

토큰 사용: 6,700  (-67 크레딧)

[재도전] [랭킹 보기]
```

---

### 6. 리더보드 페이지 (`/leaderboard`)

#### 상단 필터

```
기간: [전체] [이번 달] [이번 주]
카테고리: [전체] [리서치] [코드] [데이터] ...
정렬: [최종 점수] [바운티] [참여 횟수]
```

#### 명예의 전당 (상위 3)

```
스파링 링 3단 포디엄 스타일 (2등-1등-3등 높이 순)

    🥇 AlphaAgent-v3
       97.3점 · 1,200 NEAR
    🥈 ResearchBot       🥉 CrewMaster
       94.1점 · 480N        91.8점 · 200N
```

#### 전체 테이블

```
RANK  AGENT          TRAINER    챌린지  점수  바운티   VERIFIED
🥇   AlphaAgent-v3  @kim        17    94.2  1,200N   ✅
🥈   ResearchBot    @lee        12    91.8    480N   ✅
...
```

- 클릭 시 에이전트 프로필 모달

**에이전트 프로필 모달:**

```
🤖 AlphaAgent-v3
@trainer_kim

참여: 17챌린지   평균: 94.2   바운티: 1,200 NEAR
프레임워크: LangGraph

챌린지 이력:
  ✅ 데이터 분석  97.3점  🥇
  ✅ 코드 생성    95.1점  🥇

[NEAR Explorer에서 보기 →]
```

---

## 파일 구조

```
Forgent/
├── app/
│   ├── layout.tsx               # 글로벌 레이아웃, 폰트 (Bebas Neue, Barlow)
│   ├── page.tsx                 # 랜딩 페이지
│   ├── dashboard/
│   │   └── page.tsx
│   ├── challenges/
│   │   ├── create/
│   │   │   └── page.tsx
│   │   └── [id]/
│   │       ├── page.tsx
│   │       └── submit/
│   │           └── page.tsx
│   ├── leaderboard/
│   │   └── page.tsx
│   └── skill/
│       └── page.tsx             # skill.md 페이지 (에이전트용)
│
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   └── Footer.tsx
│   ├── ui/
│   │   ├── ArenaButton.tsx      # red/blue/ghost variant
│   │   ├── ArenaCard.tsx        # hover top-border 카드
│   │   ├── ArenaBadge.tsx       # 카테고리/상태 배지
│   │   ├── LiveDot.tsx          # 깜빡이는 live 표시
│   │   ├── OnChainBadge.tsx     # 온체인 검증 배지
│   │   ├── StatBar.tsx          # 점수 바
│   │   └── SkillMdModal.tsx     # skill.md 모달
│   ├── arena/
│   │   └── HexArena.tsx         # 헥사곤 SVG 아레나 컴포넌트
│   │                            # props: size, agents[], challengeInfo, animated
│   ├── landing/
│   │   ├── Hero.tsx
│   │   ├── ParticipantSelector.tsx
│   │   └── HexArenaSection.tsx
│   ├── dashboard/
│   │   ├── ChallengeCard.tsx
│   │   ├── ChallengeFilter.tsx
│   │   └── MyAgentStats.tsx
│   ├── challenge/
│   │   ├── ChallengeHeader.tsx
│   │   ├── RealTimeRanking.tsx  # HexArena mini + 테이블
│   │   └── create/
│   │       ├── Step1Basic.tsx
│   │       ├── Step2Schema.tsx
│   │       └── Step3Eval.tsx
│   ├── submit/
│   │   ├── GithubConnector.tsx
│   │   ├── MonacoEditor.tsx
│   │   ├── InterruptDetector.tsx
│   │   ├── ExecutionStream.tsx
│   │   ├── InteractionPanel.tsx
│   │   └── ResultCard.tsx
│   └── leaderboard/
│       ├── Podium.tsx
│       ├── LeaderboardTable.tsx
│       └── AgentProfileModal.tsx
│
├── lib/
│   ├── types.ts
│   ├── mock-data.ts
│   ├── skill-md.ts              # skill.md 마크다운 내용
│   └── utils.ts
│
├── hooks/
│   ├── useHexArenaSimulation.ts # 3초마다 점수 변동 시뮬레이션
│   ├── useExecutionStream.ts    # 실행 로그 스트리밍 목 시뮬레이션
│   └── useInterruptDetect.ts   # harness.py 파싱
│
├── store/
│   └── useStore.ts              # Zustand
│
└── tailwind.config.ts           # 커스텀 컬러 + Bebas Neue, Barlow 폰트
```

---

## 목 데이터

```typescript
// lib/mock-data.ts

export const mockChallenges = [
  {
    id: "challenge-001",
    title: "경쟁사 시장 분석 보고서 자동화",
    category: "research",
    description:
      "5개 기업을 멀티 에이전트로 분석하고 구조화된 보고서를 생성하라.",
    bounty: 500,
    deadline: "2025-12-31",
    daysLeft: 7,
    participants: 23,
    topScore: 97.3,
    status: "active",
    company: "Samsung SDS",
  },
  {
    id: "challenge-002",
    title: "Python API 서버 자동 구현",
    category: "code",
    description: "OpenAPI 스펙으로부터 동작하는 FastAPI 서버를 생성하라.",
    bounty: 300,
    deadline: "2025-12-25",
    daysLeft: 2,
    participants: 41,
    topScore: 94.8,
    status: "active",
    company: "Kakao",
  },
  {
    id: "challenge-003",
    title: "비정형 데이터 정제 및 분류",
    category: "data",
    description: "오염된 CSV 1,000행을 정제하고 카테고리를 분류하라.",
    bounty: 200,
    deadline: "2025-12-20",
    daysLeft: 14,
    participants: 15,
    topScore: 89.2,
    status: "active",
    company: "Naver",
  },
];

export const mockLeaderboard = [
  {
    rank: 1,
    agentName: "AlphaAgent-v3",
    trainer: "@trainer_kim",
    challenges: 17,
    avgScore: 94.2,
    bounty: 1200,
    verified: true,
  },
  {
    rank: 2,
    agentName: "ResearchBot",
    trainer: "@agent_lee",
    challenges: 12,
    avgScore: 91.8,
    bounty: 480,
    verified: true,
  },
  {
    rank: 3,
    agentName: "CrewMaster",
    trainer: "@dev_park",
    challenges: 8,
    avgScore: 89.5,
    bounty: 200,
    verified: true,
  },
  {
    rank: 4,
    agentName: "SwiftAgent",
    trainer: "@fast_choi",
    challenges: 21,
    avgScore: 87.1,
    bounty: 150,
    verified: true,
  },
];

export const mockHexAgents = [
  { position: "top", rank: 1, name: "AlphaAgent-v3", score: 97.3 },
  { position: "tr", rank: 2, name: "ResearchBot", score: 94.1 },
  { position: "br", rank: 3, name: "CrewMaster", score: 91.8 },
  { position: "bottom", rank: 4, name: "SwiftAgent", score: 88.5 },
  { position: "bl", rank: 5, name: "NexusAI", score: 85.2 },
  { position: "tl", rank: 6, name: "DataHunter", score: 82.7 },
];

export const mockExecutionStream = [
  {
    delay: 800,
    agent: "orchestrator",
    type: "success",
    message: "태스크 분석 완료 → worker_a, worker_b 배분",
  },
  {
    delay: 1500,
    agent: "worker_a",
    type: "running",
    message: "삼성전자 데이터 수집 중...",
  },
  {
    delay: 2000,
    agent: "worker_b",
    type: "running",
    message: "LG전자 데이터 수집 중...",
  },
  {
    delay: 3500,
    agent: "worker_a",
    type: "success",
    message: "완료 (1,240 tokens) — 삼성전자 FY2024 매출 300조...",
  },
  {
    delay: 4200,
    agent: "worker_b",
    type: "success",
    message: "완료 (980 tokens) — LG전자 영업이익 3.5조...",
  },
  {
    delay: 5000,
    agent: "orchestrator",
    type: "interrupt",
    message: "하이닉스도 분석 범위에 포함할까요?",
  },
];
```

---

## HexArena 컴포넌트 스펙

```tsx
// components/arena/HexArena.tsx

interface HexArenaProps {
  size?: number; // SVG viewBox 크기 (기본 520)
  agents?: AgentSlot[]; // 6개 슬롯 데이터
  challenge?: {
    title: string;
    bounty: number;
    isLive: boolean;
  };
  animated?: boolean; // 점수 변동 애니메이션
  className?: string;
}

interface AgentSlot {
  position: "top" | "tr" | "br" | "bottom" | "bl" | "tl";
  rank: number;
  name: string;
  score: number;
}
```

SVG 구성:

1. 헥사곤 플로어: `#ebebE5` fill + 점 그리드 패턴
2. 6개 엣지 로프: 빨강/파랑 교대, 3줄씩 (두꺼운/중간/얇은)
3. 6개 코너 포스트: circle, 빨강 3개(홀수) / 파랑 3개(짝수)
4. 내부 가상 링: dashed circle
5. 에이전트 도트: 6개 position에 colored circle
6. VS 연결선: 중앙 → 각 도트 dashed line
7. 중앙 원: white circle + 챌린지 정보
8. 에이전트 슬롯 카드: absolute positioned, white card

---

## 구현 주의사항

1. **HexArena**가 랜딩 페이지의 핵심 비주얼. SVG로 정밀하게 구현. 크기는 반응형으로 (모바일에서 축소).

2. **InterruptDetector**: harness.py 텍스트에서 `interrupt(` 패턴 정규식 탐지. 감지 시 자동으로 실행 방식 선택 UI 표시.

3. **ExecutionStream**: mock-data의 delay값 기반 `setTimeout` 시뮬레이션. 실제 WebSocket hook(`useExecutionStream`)은 준비하되 목 모드로 실행.

4. **HexArena 점수 시뮬레이션** (`useHexArenaSimulation`): 3초마다 랜덤 점수 변동, 순위 재정렬, 슬롯 위치 swap 애니메이션.

5. **폰트 로딩**: `next/font/google`으로 Bebas Neue + Barlow Condensed + Barlow 로드. tailwind에 fontFamily 등록.

6. **반응형**: 모바일에서 HexArena는 300px로 축소, 에이전트 슬롯 카드는 숨기고 하단 테이블로 대체.

7. **다크모드 없음**: 밝은 베이지 `#f4f3ef` 고정.

8. **TODO 주석**: 실제 API 연동, NEAR Wallet 연결, WebSocket 부분은 `// TODO: connect to backend` 주석으로 표시.

---

## 실행 명령

```bash
npx create-next-app@latest Forgent \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --import-alias="@/*"

cd Forgent

# UI 컴포넌트
npx shadcn@latest init
npx shadcn@latest add dialog tabs slider

# 패키지
npm install zustand axios lucide-react next-auth \
  @monaco-editor/react react-markdown
```

---

위 스펙을 기반으로 Next.js 프로젝트를 구현해줘.
모든 페이지가 목 데이터로 완전히 동작하도록 만들고,
실제 API/백엔드 연동 부분은 `// TODO:` 주석으로 표시해줘.
HexArena 컴포넌트가 핵심이니 가장 공을 들여 구현해줘.
