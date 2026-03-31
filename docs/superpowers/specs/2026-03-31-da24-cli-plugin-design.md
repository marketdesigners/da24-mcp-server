# da24 CLI Plugin Design

## Goal

`npx da24` 로 설치하고 Claude Code slash command로 이사 견적 계산 및 접수를 할 수 있는 공개 npm 패키지를 만든다.

## Background

현재 da24 MCP 서버(`mcp.wematch.com`)는 Claude, ChatGPT, Grok, Gemini CLI에서 수동으로 설정해야 사용 가능하다. 개발자가 `npx da24 init` 한 번으로 Claude Code 설정을 자동화하고, slash command로 바로 사용할 수 있게 한다.

## Architecture

```
da24-cli (npm 패키지: da24)
├── bin/
│   └── da24.js          ← CLI 진입점
├── lib/
│   ├── init.js          ← ~/.claude.json MCP 설정 자동 추가
│   ├── estimate.js      ← 대화형 메뉴 + REST API 호출 (견적)
│   └── inquiry.js       ← 대화형 메뉴 + REST API 호출 (접수)
├── skills/
│   └── da24.md          ← Claude Code slash command 스킬 정의
├── package.json
└── README.md
```

## CLI Commands

### `npx da24 init`
- `~/.claude.json`의 `mcpServers`에 da24 MCP 설정 자동 추가
- API 키 입력 프롬프트 (없으면 스킵 — 견적 계산은 키 없이도 동작)
- API 키 있으면 MCP URL을 `https://mcp.wematch.com/sse?api_key=KEY` 형태로 저장
- API 키 없으면 MCP URL을 `https://mcp.wematch.com/sse` 로 저장
- 이미 설정된 경우 덮어쓸지 확인
- 완료 후 "Claude Code를 재시작하고 /da24 를 써보세요!" 안내

### `npx da24 estimate`
터미널 대화형 메뉴로 짐 목록을 선택하고 견적 계산:

```
? 짐 항목 선택 (스페이스로 선택, 엔터로 확인)
  ◉ 침대
  ◯ 냉장고
  ◯ 세탁기
  ...

? 침대 옵션 선택
  ◉ 싱글
  ◯ 슈퍼싱글
  ◯ 퀸
  ...

? 포장 서비스 필요 여부 (Y/n)
```

- 카테고리 선택 → 옵션 선택 → 수량 입력 순서로 진행
- `mcp.wematch.com/rest/estimate` 호출
- 결과 출력 + 다이사 링크 안내

### `npx da24 inquiry`
터미널 대화형으로 접수 정보 입력:

```
? 이름: 홍길동
? 연락처: 010-1234-5678
? 이사 유형: (가정이사 / 원룸이사 / 사무실이사 / 보관이사 / 용달이사)
? 이사 날짜 (YYYY-MM-DD 또는 미정): 2026-05-01
? 출발지 시/도: 서울
? 출발지 구/군: 강남구
? 도착지 시/도: 경기도
? 도착지 구/군: 성남시
```

- API 키 없으면 "API 키가 필요합니다. `npx da24 init` 을 먼저 실행하세요." 안내
- API 키는 `~/.claude.json` mcpServers URL의 `?api_key=` 파라미터에서 파싱
- `DA24_API_KEY` 환경변수가 있으면 우선 사용
- `mcp.wematch.com/rest/inquiry` 호출 (X-API-Key 헤더로 전달)

## API Key 처리 우선순위

```
1. DA24_API_KEY 환경변수
2. ~/.claude.json mcpServers.da24.url 의 ?api_key= 파라미터
3. 없으면 → 견적만 가능, 접수 불가
```

## Slash Command (skills/da24.md)

Claude Code에서 `/da24` 입력 시 로드되는 스킬 — **MCP 툴 호출을 위한 프롬프트 가이드** 역할.

```
/da24 원룸 이사 견적 계산해줘
/da24 접수해줘. 홍길동, 010-1234-5678, 2026-05-01, 서울 강남구 → 경기 성남시
```

스킬 내용:
- MCP 서버의 `calculate_estimate` / `create_inquiry` 툴 호출 방법 안내
- 짐 항목 변환 가이드 (사용자 표현 → `카테고리:옵션` 형식)
- 견적 결과에 다이사 cta 링크 포함 지침
- 접수 시 필수 정보 수집 방법

## REST API (터미널 CLI 전용)

| 엔드포인트 | 인증 | 설명 |
|-----------|------|------|
| `POST /rest/estimate` | 불필요 | 견적 계산 |
| `POST /rest/inquiry` | X-API-Key 헤더 | 이사 접수 |

요청 형식:
```json
// estimate
{"items": [{"item": "침대:퀸", "quantity": 1}], "need_packing": false}

// inquiry
{"name": "홍길동", "tel": "010-1234-5678", "moving_type": "가정이사",
 "moving_date": "2026-05-01", "sido": "서울", "gugun": "강남구",
 "sido2": "경기도", "gugun2": "성남시"}
```

## Tech Stack

- **Node.js 18+** — 내장 `fetch`, `readline` 사용 (외부 의존성 최소화)
- **inquirer** — 대화형 메뉴 (유일한 외부 의존성)
- npm 패키지명: `da24`

## Distribution

- `npx da24` 로 설치 없이 바로 실행
- GitHub: `github.com/marketdesigners/da24-cli` (별도 레포)
- npm: `npmjs.com/package/da24`

## Out of Scope

- 웹 UI
- 다국어 지원
- 견적 히스토리 저장
- Superpowers 플러그인 시스템 연동
