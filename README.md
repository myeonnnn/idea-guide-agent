# 아이디어 검증 & 로드맵 에이전트

**아이디어에 대한 전반적인 로드맵 초안을 제안해주는 로컬 AI 도구**입니다. 타겟층, 시장, 가설, 리스크, MVP 범위, 비즈니스모델을 정리해서 로드맵 형태로 보여줍니다.

아이디어 하나를 입력하면 AI가 다음 8단계를 순서대로 진행합니다.

> **타겟층 → 시장조사 → 가치제안 → 가설 수립 → 가설 검증 → MVP/MLP 정의 → 비즈니스모델 → 로드맵 요약**

---

# 전체 동작 방식

```mermaid
graph LR
  A["아이디어 입력"] --> S1["01 타겟층 설정"]
  S1 --> S2["02 시장조사"]
  S2 --> S3["03 가치제안 · 차별화"]
  S3 --> S4["04 가설 수립"]
  S4 --> S5["05 가설 검증<br/>리스키스트 어썸션"]
  S5 --> S6["06 MVP / MLP 정의"]
  S6 --> S7["07 비즈니스모델 가정"]
  S7 --> S8["08 로드맵 요약"]
  S8 --> D["완성된 로드맵 초안"]
```

아이디어는 처음 한 번만 입력하면 되고, 이후 8개의 단계가 순서대로 실행됩니다. 마지막 단계는 앞의 7단계 결과를 판단 없이 **하나의 로드맵으로 종합·요약**합니다.

---

# 1. 추론 엔진

Anthropic API를 직접 호출하지 않고, **로컬에 로그인되어 있는 Claude Code CLI를 서브프로세스로 실행**해서 추론 엔진으로 사용합니다. 별도 API 키 없이 기존 Claude 환경을 그대로 씁니다.

`Engine` 인터페이스로 추상화되어 있습니다.

```python
# app/engine/base.py

class Engine(Protocol):
    def generate(
        self,
        prompt: str,
        history: list[Message]
    ) -> EngineResponse: ...
```

현재 구현은 `ClaudeCodeCLIEngine` 하나이고, 하는 일은 이게 전부입니다.

```python
subprocess.run(
    ["claude", "-p", prompt, "--output-format", "json"]
)
```

나중에 Anthropic/OpenAI API로 바꾸려면 `Engine`을 구현하는 클래스만 추가하면 됩니다. 파이프라인은 어떤 엔진을 쓰는지 알 필요가 없습니다.

---

# 2. 8단계 파이프라인

각 단계는 이전 단계의 결과를 입력으로 받고, 정의된 Pydantic 스키마에 맞는 JSON을 반환합니다. `app/stages/` 아래에서 단계별로 독립적으로 관리합니다.

```python
class SomeStageOutput(BaseModel):
    ...

class SomeStage(StageDefinition[SomeStageOutput]):
    name = "some_stage"
    output_model = SomeStageOutput

    def build_prompt(
        self,
        idea,
        prior_outputs,
        user_message=""
    ):
        ...
```

- `build_prompt()`는 필요한 컨텍스트를 모아 프롬프트를 만듭니다.
- LLM은 정해진 JSON 형식으로 결과를 반환합니다.
- Pydantic이 결과의 구조와 검증 규칙을 확인합니다.
- 검증을 통과한 결과만 다음 단계로 전달합니다.

실행 순서는 `app/orchestrator.py`의 `PIPELINE`에서 관리하고, 오케스트레이터는 다음 한 가지만 합니다.

> 현재 단계를 실행 → 성공하면 세션에 저장 → 다음 단계로 이동

---

# 3. 출처와 주장에 대한 검증

"출처가 불확실하면 추정이라고 표시해줘" 같은 프롬프트 요청만으로는 부족해서, **코드 수준에서 검증**하도록 만들었습니다.

```python
class SourceTier(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    ESTIMATE = "ESTIMATE"


class Claim(BaseModel):
    text: str
    source_tier: SourceTier
    source_url: str | None = None
```

| 등급 | 의미 |
| --- | --- |
| `PRIMARY` | 공식 통계, 학술자료 등 1차 출처 |
| `SECONDARY` | 기사, 업계 자료 등 2차 출처 |
| `ESTIMATE` | AI가 추정한 값 |

`PRIMARY`/`SECONDARY`는 출처 URL이 반드시 있어야 하며, `app/verification/checks.py`의 `validate_claims()`가 이를 검증합니다. 규칙을 어긴 응답은 정상 결과로 취급하지 않습니다.

---

# 4. 프론트엔드

Vite + React + TypeScript. 별도의 에이전트 로직 없이, 아이디어를 입력하면 첫 단계가 실행되고 응답이 성공할 때마다 다음 단계 API를 재귀적으로 호출합니다.

결과는 단계별 카드로 화면에 쌓이고, 중간에 오류가 나면 해당 단계에서 멈춰 재시도 버튼을 보여줍니다. 프론트엔드의 역할은 **파이프라인을 순서대로 호출하고 결과를 보여주는 것**뿐입니다.

---

# 아키텍처

```text
┌─────────────────────────────┐
│        React / Vite         │
│     localhost:5173          │
└──────────────┬──────────────┘
               │ HTTP / CORS
               ▼
┌─────────────────────────────┐
│         FastAPI             │
│      127.0.0.1:8000         │
│                             │
│  Orchestrator               │
│  Stage definitions          │
│  Verification               │
│  Session management         │
└──────────────┬──────────────┘
               │ subprocess
               ▼
┌─────────────────────────────┐
│       Claude Code CLI       │
└─────────────────────────────┘

Session
   │
   ▼
data/sessions/*.json
```

- **로컬 전용**: API 서버는 `127.0.0.1`에 바인딩
- **외부 DB 없음**: 세션은 로컬 JSON 파일로 저장
- **외부 API 키 불필요**: 로컬 `claude` CLI 사용
- **백엔드 / 프론트엔드 분리**: 서로 독립적인 프로세스로 실행, CORS로 통신
- **추론 엔진 추상화**: `Engine` 인터페이스로 다른 LLM API도 붙일 수 있음

프론트엔드 API 주소는 `VITE_API_BASE_URL` 환경변수로 변경 가능 (기본값 `http://127.0.0.1:8000`).

---

# 프로젝트 구조

```text
.
├── app/
│   ├── api.py
│   ├── orchestrator.py
│   ├── engine/
│   │   ├── base.py
│   │   └── claude_cli.py
│   ├── stages/
│   │   ├── base.py
│   │   ├── target_segment.py
│   │   ├── market_research.py
│   │   ├── value_proposition.py
│   │   ├── hypothesis.py
│   │   ├── hypothesis_validation.py
│   │   ├── mvp_mlp.py
│   │   ├── business_model.py
│   │   └── roadmap_summary.py
│   └── verification/
│       ├── models.py
│       └── checks.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── data/
│   └── sessions/
│
└── docs/
    └── superpowers/
        ├── specs/
        └── plans/
```

---

# 로컬 실행

## Backend

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000
```

→ `http://127.0.0.1:8000`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

→ `http://localhost:5173` (브라우저는 이 5173번 포트로 접속)

---

# 현재 상태

MVP 구현 완료.

- 8단계 아이디어 검증 파이프라인
- 로컬 Claude Code CLI 연동
- 단계별 Pydantic 스키마 검증
- 출처 등급 및 Claim 검증
- 리스크 우선순위화
- 로드맵 요약 (판단이 아니라 정리)
- 단계별 실패 및 재시도 처리
- 세션 JSON 저장
- 결과 마크다운 저장
- Vite + React 프론트엔드
- 실제 Claude CLI를 이용한 전체 파이프라인 E2E 검증
