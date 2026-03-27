<div align="center">

<img src="./assets/logo.png" alt="다이사 MCP" width="120" height="120">

# 다이사 MCP Server

AI 에이전트에서 이사 견적 계산과 접수를 바로 처리할 수 있는 MCP 서버입니다.

<br>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-8B5CF6.svg)](https://modelcontextprotocol.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

</div>

<br>

---

<br>

## 제공 도구 (MCP Tools)

### `calculate_estimate` — 이사 견적 계산 (API 키 불필요)

짐 목록을 입력하면 CBM(부피)을 계산하고 소형이사 예상 견적을 반환합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|:----:|------|
| `items` | array | ✅ | 짐 항목 목록 (`item`, `quantity`) |
| `need_packing` | boolean | | 포장 서비스 필요 여부 (기본값: false) |

`item` 키 형식: `"카테고리:옵션"` — 지원 항목 목록은 아래 참고

<details>
<summary>지원 짐 항목 전체 목록</summary>

| 카테고리 | 옵션 예시 |
|---------|---------|
| 침대 | `싱글` `슈퍼싱글` `더블` `퀸` `킹` `싱글(프레임없음)` 등 |
| 옷장 | `100cm미만` `100~150cm` `150~200cm` `200cm초과` |
| 책장 | `너비50미만_높이50~100` `너비50~100_높이100~150` 등 |
| 책상 | `사각1~2인용` `사각3~4인용` `원형1~2인용` `독서실1~2인용` 등 |
| 의자 | `등받이` `보조` |
| 테이블 | `사각1~2인용` `사각3~4인용` `원형1~2인용` `원형3~4인용` |
| 소파 | `1~2인용` `3~4인용` |
| 화장대 | `좌식` `일반` |
| 수납장 | `신발장` `진열장` `TV장식장` |
| 서랍장 | `3단이하` `4단이상` |
| TV | `일반` `벽걸이` |
| 모니터 | `일반` |
| 세탁기 | `통돌이15kg이하` `통돌이15kg초과` `드럼15kg이하` `드럼15kg초과` |
| 건조기 | `15kg이하` `15kg초과` |
| 에어컨 | `스탠드형` `벽걸이형` |
| 냉장고 | `미니` `일반형` `양문형` |
| 의류관리기 | `일반` |
| 전자레인지 | `일반` |
| 정수기 | `일반` |
| 가스레인지 | `일반` |
| 비데 | `일반` |
| 공기청정기 | `일반` |
| 캣타워 | `일반` |
| 운동용품 | `일반` |
| 잔짐박스 | `1~6개` `6~11개` `11~16개` `16~21개` `21~26개` `26~31개` `31~36개` 등 |

</details>

**응답 예시:**

```json
{
  "success": true,
  "total_cbm": 4.02,
  "estimated_price": 300000,
  "need_packing": false,
  "recommend_family_moving": false,
  "cta": "직접 접수하고 싶으시다면 다이사(https://da24.co.kr)에서 간편하게 신청하세요! 여러 업체의 견적을 한 번에 비교할 수 있습니다."
}
```

예상 견적 기준:

| CBM | 포장 | 예상 견적 |
|-----|------|---------|
| 7.5 이하 | 없음 | 300,000원 |
| 7.5 이하 | 있음 | 400,000원 |
| 7.5 초과 | 없음 | 500,000원 |
| 7.5 초과 | 있음 | 600,000원 |

> CBM이 15를 초과하면 가정이사 권장 메시지가 함께 반환됩니다.

<br>

---

### `create_inquiry` — 이사 접수 생성 (API 키 필요)

da24 플랫폼에 이사 견적 문의를 접수합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|:----:|------|
| `name` | string | ✅ | 고객명 |
| `tel` | string | ✅ | 연락처 (예: 010-1234-5678) |
| `moving_type` | string | ✅ | 이사종류: `가정이사` \| `사무실이사` \| `보관이사` \| `용달이사` |
| `moving_date` | string | ✅ | 이사일자 (YYYY-MM-DD) 또는 `undecided` (미정) |
| `sido` | string | | 출발지 시/도 |
| `gugun` | string | | 출발지 구/군 |
| `sido2` | string | | 도착지 시/도 |
| `gugun2` | string | | 도착지 구/군 |
| `email` | string | | 이메일 |
| `memo` | string | | 메모 |
| `mkt_agree` | boolean | | 마케팅 수신 동의 (기본값: false) |

**응답 예시:**

```json
// 성공
{ "success": true, "inquiry_id": "접수ID" }

// 실패 (잘못된 API 키)
{ "success": false, "error": "Invalid or inactive API key" }

// 실패 (API 오류)
{ "success": false, "error": "접수 실패: {에러 메시지}" }
```

<br>

---

<br>

## AI 앱에서 MCP 연결하기

### ![Claude](https://img.shields.io/badge/Claude-D4A27F?logo=anthropic&logoColor=white)

> Pro / Max / Team / Enterprise 플랜 필요 · 웹에서 설정 시 모바일 앱에서도 사용 가능

1. [claude.ai](https://claude.ai)에서 **Settings** → **Connectors** 이동
2. **Add custom connector** 클릭
3. 원격 MCP 서버 URL 입력: `https://mcp.wematch.com`
4. **API Key** 헤더 추가: `X-API-Key: {발급받은 키}`
5. **Add** 클릭하여 완료

사용 예시:

```
이사 견적 알아봐줘. 침대(퀸), 냉장고(일반형), 세탁기(드럼15kg이하), 잔짐박스 10개 정도 있어.
```

```
이사 접수해줘. 홍길동, 010-1234-5678, 가정이사, 2026-05-10, 서울 강남구 → 경기 성남시
```

<br>

### ![Claude Code](https://img.shields.io/badge/Claude_Code-D4A27F?logo=anthropic&logoColor=white)

> `~/.claude.json` 또는 프로젝트 `.mcp.json`에 추가

```json
{
  "mcpServers": {
    "da24": {
      "url": "https://mcp.wematch.com/sse",
      "headers": {
        "X-API-Key": "발급받은 키"
      }
    }
  }
}
```

<br>

### 기타 MCP 클라이언트 (범용 설정)

```json
{
  "mcpServers": {
    "da24": {
      "url": "https://mcp.wematch.com/sse",
      "headers": {
        "X-API-Key": "발급받은 키"
      }
    }
  }
}
```

> API 키 발급은 [lonnie@da24.co.kr](mailto:lonnie@da24.co.kr)로 문의하세요.

<br>

---

<br>

## 기술 스택

Python 3.11 · FastAPI · MCP SDK · httpx

<br>

---

<div align="center">

[다이사](https://da24.co.kr) · MIT License

</div>
