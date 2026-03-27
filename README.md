<div align="center">

# da24 MCP Server

이사 견적 문의(InquiryCreate)를 AI 에이전트에서 바로 접수할 수 있는 MCP 서버입니다.
외부 AI 에이전트가 MCP 프로토콜로 da24 플랫폼에 이사 접수를 생성합니다.

<br>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-8B5CF6.svg)](https://modelcontextprotocol.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

</div>

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
이사 접수해줘. 홍길동, 010-1234-5678, 가정이사, 2026-05-10, 서울 강남구 → 경기 성남시
```

<br>

### ![Claude Code](https://img.shields.io/badge/Claude_Code-D4A27F?logo=anthropic&logoColor=white)

> `~/.claude.json` 또는 프로젝트 `.mcp.json`에 추가

```json
{
  "mcpServers": {
    "da24-inquiry": {
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
    "da24-inquiry": {
      "url": "https://mcp.wematch.com/sse",
      "headers": {
        "X-API-Key": "발급받은 키"
      }
    }
  }
}
```

> DEV 환경: `https://mcp-dev.wematch.com`

<br>

---

<br>

## 제공 도구 (MCP Tool)

### `create_inquiry` — 이사 접수 생성

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|:----:|------|
| `name` | string | ✅ | 고객명 |
| `tel` | string | ✅ | 연락처 (예: 010-1234-5678) |
| `moving_type` | string | ✅ | 이사종류: `원룸이사` \| `가정이사` \| `사무실이사` |
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
{ "success": true, "inquiry_id": "암호화된접수ID" }

// 실패 (잘못된 API 키)
{ "success": false, "error": "Invalid or inactive API key" }

// 실패 (da24 API 오류)
{ "success": false, "error": "접수 실패: {에러 메시지}" }
```

<br>

---

<br>

## API 키 발급 (관리자)

API 키는 `X-Admin-Secret` 헤더로 보호된 관리자 API를 통해 발급합니다.

### 키 발급

```bash
curl -X POST https://mcp.wematch.com/admin/keys \
  -H "X-Admin-Secret: {admin-secret}" \
  -H "Content-Type: application/json" \
  -d '{"name": "서비스명 또는 키 소유자"}'
```

```json
{
  "key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "서비스명",
  "created_at": "2026-04-01 00:00:00"
}
```

> ⚠️ 키는 발급 응답에서 **딱 한 번만** 평문으로 노출됩니다. 분실 시 새 키를 발급해야 합니다.

### 키 관리

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/admin/keys` | 전체 키 목록 조회 |
| `PATCH` | `/admin/keys/{key}` | 키 활성화/비활성화 (`{"is_active": true/false}`) |
| `DELETE` | `/admin/keys/{key}` | 키 비활성화 (soft delete) |

<br>

---

<br>

## 아키텍처

```
AI 에이전트 (Claude, GPT 등)
    │
    │ MCP SSE  ·  Header: X-API-Key: {발급된 키}
    ▼
da24-mcp-server (Python 3.11, 포트 8000)
    ├─ GET  /sse           — MCP SSE 엔드포인트
    ├─ POST /messages/     — MCP 메시지 핸들러
    └─ /admin/keys         — API 키 관리 (X-Admin-Secret 보호)
    │
    ├─ mcp_api_keys (MSSQL) — API 키 검증 및 사용량 기록
    │
    ▼
da24 API  →  POST /move/inquiry
    │
    ▼
MSSQL (queryhistory 테이블)
```

**기술 스택:**
- Python 3.11 · FastAPI · uvicorn · MCP SDK
- pyodbc (MSSQL) · httpx

<br>

---

<br>

## 로컬 실행

### 1. 환경 설정

```bash
cd da24-mcp-server
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일에 실제 값 입력
```

```env
DA24_API_URL=http://localhost:8001
ADMIN_SECRET=your-admin-secret
MSSQL_SERVER=your-mssql-server
MSSQL_DATABASE=your-database
MSSQL_USERNAME=your-username
MSSQL_PASSWORD=your-password
MCP_PORT=8000
```

### 3. DB 테이블 생성

```sql
CREATE TABLE mcp_api_keys (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    [key]        NVARCHAR(100) UNIQUE NOT NULL,
    name         NVARCHAR(200) NOT NULL,
    is_active    BIT DEFAULT 1,
    created_at   DATETIME DEFAULT GETDATE(),
    last_used_at DATETIME NULL,
    usage_count  INT DEFAULT 0
);
```

### 4. 서버 시작

```bash
python main.py
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### 5. 테스트

```bash
pytest tests/ -v
```

<br>

---

<br>

## 배포

EKS + ArgoCD GitOps 패턴으로 배포합니다.

| 환경 | 브랜치 | 도메인 | ArgoCD Sync |
|------|--------|--------|-------------|
| DEV | `feature` | `mcp-dev.wematch.com` | 자동 |
| PROD | `master` | `mcp.wematch.com` | 수동 |

`feature` 또는 `master` 브랜치에 push 하면 GitHub Actions가 ECR에 이미지를 빌드·푸시하고,
`marketdesigners/k8` 레포의 `resources.yaml` 이미지 태그를 자동 업데이트합니다.

<br>

---

<div align="center">

MIT License

</div>
