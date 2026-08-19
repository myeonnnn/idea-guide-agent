# 아이디어 검증 & 로드맵 에이전트

스타트업 아이디어를 실제로 개발하기 전에, **아이디어에 대한 전반적인 로드맵 초안을 제안해주는 로컬 AI 도구**입니다. 이 아이디어를 "만들 만한지 아닌지"를 대신 판단해주지는 않습니다 — 판단에 필요한 재료(타겟층, 시장, 가설, 리스크, MVP 범위, 비즈니스모델)를 정리해서 로드맵 형태로 보여주는 것까지가 이 도구의 역할입니다.

아이디어 하나를 입력하면 AI가 다음 8단계를 순서대로 진행합니다.

> **타겟층 → 시장조사 → 가치제안 → 가설 수립 → 가설 검증 → MVP/MLP 정의 → 비즈니스모델 → 로드맵 요약**

최종 결과물은 완성된 사업계획서가 아니라, **다음 결정을 위해 필요한 것들을 정리한 로드맵 초안**입니다.

특히 이 프로젝트에서는 그럴듯한 숫자나 근거 없는 시장 규모를 만들어내는 것보다, **모르는 것을 모른다고 표시하는 것**을 중요하게 생각합니다.

---

## 왜 만들었나

기존의 AI 아이디어 검증 서비스들은 짧은 시간 안에 꽤 그럴듯한 리포트를 만들어줍니다.

문제는 그 안에 들어가는 시장 규모, 통계, 경쟁사 정보 등의 **근거가 실제로 맞는지 확인하기 어렵다는 점**입니다.

이 프로젝트는 그 부분을 조금 다르게 접근합니다.

> **모르는 것보다 잘못된 정보를 주는 것이 더 나쁘다.**

그래서 각 단계에서 사실에 가까운 정보와 추정치를 구분하고, 사실을 주장하는 경우에는 가능한 한 출처를 함께 남깁니다.

이 도구가 만들어내는 결과는 "이 사업은 성공합니다"라는 답이 아니라,

* 지금 알고 있는 것은 무엇인지
* 아직 검증하지 못한 것은 무엇인지
* 가장 위험한 가정은 무엇인지
* 다음에 무엇을 검증해야 하는지

를 정리한 **로드맵 초안**입니다. "진행할지 말지"는 이 로드맵을 들고 사람이 직접 판단할 몫으로 남겨둡니다.

---

# 전체 동작 방식

이 프로젝트에서 "에이전트"라고 부르는 것은 복잡한 멀티 에이전트 프레임워크를 의미하지 않습니다.

구조는 최대한 단순하게 유지하고, **코드가 전체 흐름을 제어하고 LLM은 각 단계에서 판단이 필요한 부분만 담당하도록** 만들었습니다.

전체 구조는 다음과 같습니다.

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

아이디어는 처음 한 번만 입력하면 되고, 이후 8개의 단계가 순서대로 실행됩니다.

단계 순서에도 의도가 있습니다.

예를 들어 처음부터 시장 규모를 조사하면 "시장이 크다 → 이 시장을 노려야 한다"는 식으로 접근하기 쉽습니다. 그래서 이 프로젝트에서는 먼저 **누구의 어떤 문제를 해결하려는지 정의한 뒤 시장조사로 넘어갑니다.**

마지막 단계에서는 앞의 7단계 결과를 다시 한 번 모아서, 판단은 내리지 않고 **하나의 로드맵으로 종합·요약**합니다 (다음 액션, 아직 검증되지 않은 것, 근거 품질 요약).

---

# 1. 추론 엔진

현재는 Anthropic API를 직접 호출하지 않고, **로컬에 로그인되어 있는 Claude Code CLI를 서브프로세스로 실행**해서 추론 엔진으로 사용합니다.

덕분에 별도의 API 키를 설정하지 않고도 기존에 사용 중인 Claude 환경을 그대로 활용할 수 있습니다.

추론 엔진은 `Engine` 인터페이스로 추상화되어 있습니다.

```python
# app/engine/base.py

class Engine(Protocol):
    def generate(
        self,
        prompt: str,
        history: list[Message]
    ) -> EngineResponse: ...
```

현재 구현은 `ClaudeCodeCLIEngine` 하나입니다.

```python
subprocess.run(
    ["claude", "-p", prompt, "--output-format", "json"]
)
```

실제로 하는 일은 단순합니다.

1. 프롬프트를 만든다.
2. `claude` CLI를 실행한다.
3. 결과를 파싱한다.
4. `EngineResponse`로 반환한다.

나중에 Anthropic API나 OpenAI API를 사용하고 싶다면 `Engine`을 구현하는 클래스를 추가하면 됩니다.

파이프라인에서는 구체적으로 어떤 엔진을 사용하는지 알 필요가 없습니다.

---

# 2. 8단계 파이프라인

실제 에이전트의 핵심은 8개의 구조화된 단계입니다.

각 단계는 이전 단계의 결과를 입력으로 받고, 미리 정의된 Pydantic 스키마에 맞는 JSON을 반환합니다.

각 단계는 `app/stages/` 아래에서 독립적으로 관리합니다.

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

각 단계가 하는 일은 명확하게 나뉘어 있습니다.

* `build_prompt()`는 필요한 컨텍스트를 모아 프롬프트를 만듭니다.
* LLM은 정해진 JSON 형식으로 결과를 반환합니다.
* Pydantic이 결과의 구조와 검증 규칙을 확인합니다.
* 검증을 통과한 결과만 다음 단계로 전달합니다.

실행 순서는 `app/orchestrator.py`의 `PIPELINE`에서 관리합니다.

```python
PIPELINE = [
    ...,
]
```

즉, 오케스트레이터가 하는 일은 사실상 하나입니다.

> 현재 단계를 실행하고 → 성공하면 세션에 저장하고 → 다음 단계로 이동한다.

그래서 전체 구조를 이해하기 위해 복잡한 에이전트 프레임워크를 따라갈 필요가 없습니다.

---

# 3. 출처와 주장에 대한 검증

이 프로젝트에서 가장 중요하게 생각하는 부분입니다.

LLM에게

> "출처가 불확실하면 추정이라고 표시해줘."

라고 요청하는 것만으로는 충분하지 않다고 봤습니다.

그래서 가능한 한 **프롬프트가 아니라 코드 수준에서 검증하도록 만들었습니다.**

예를 들어 사실을 주장하는 데이터는 다음과 같이 표현합니다.

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

출처 등급은 다음 세 가지로 나눕니다.

| 등급          | 의미                  |
| ----------- | ------------------- |
| `PRIMARY`   | 공식 통계, 학술자료 등 1차 출처 |
| `SECONDARY` | 기사, 업계 자료 등 2차 출처   |
| `ESTIMATE`  | AI가 추정한 값           |

예를 들어 `PRIMARY`나 `SECONDARY`로 표시했다면 출처 URL이 반드시 있어야 합니다.

이 검증은 `app/verification/checks.py`의 `validate_claims()`에서 처리합니다.

따라서 LLM이 출처 등급을 잘못 붙이거나 필수 정보를 빼먹으면 해당 응답은 정상적인 결과로 취급하지 않습니다.

---

# 4. 파싱과 재시도

LLM 응답은 항상 깔끔하게 떨어지지 않습니다.

실제로 테스트하면서 다음과 같은 문제들을 발견했고, 공통 실행기인 `app/stages/base.py`의 `run_stage()`에서 처리하도록 했습니다.

### Markdown 코드펜스

JSON만 요청해도 다음처럼 반환되는 경우가 있습니다.

````text
```json
{
  ...
}
````

````

그래서 코드펜스로 감싸진 JSON을 먼저 추출한 뒤 파싱합니다.

### 스키마 검증 실패

JSON 파싱이나 Pydantic 검증에 실패하면 한 번 재시도합니다.

재시도에서는 스키마에 정확히 맞는 JSON만 반환하도록 추가 지시를 붙입니다.

### 재시도도 실패한 경우

두 번째 시도까지 실패했다고 전체 파이프라인을 종료시키지는 않습니다.

대신 다음 형태의 결과를 반환합니다.

```python
StageResult(
    output=None,
    warning=...,
    raw_text=...
)
````

API에서는 이를 `warning` 상태로 전달하고, 프론트엔드에서는 해당 단계에 경고와 재시도 버튼을 보여줍니다.

### Claude CLI 자체가 실패한 경우

CLI 타임아웃이나 프로세스 종료 같은 `EngineError`도 같은 방식으로 처리합니다.

처음에는 이런 경우 API가 그대로 500 에러를 반환했는데, 실제 E2E 테스트를 하면서 발견해 현재 구조로 변경했습니다.

---

# 5. 프론트엔드

프론트엔드는 가능한 한 단순하게 유지했습니다.

기술 스택은 다음과 같습니다.

* Vite
* React
* TypeScript

프론트엔드에는 별도의 에이전트 로직이 없습니다.

사용자가 아이디어를 입력하면 첫 번째 단계가 실행되고, 응답이 성공할 때마다 다음 단계의 API를 다시 호출합니다.

즉,

```text
아이디어 입력
   ↓
01 실행
   ↓
02 실행
   ↓
03 실행
   ↓
...
   ↓
08 실행
```

형태로 진행됩니다.

모든 결과는 단계별 카드 형태로 화면에 쌓이고, 중간 단계에서 오류가 발생하면 해당 단계에서 멈춘 뒤 사용자가 다시 시도할 수 있습니다.

프론트엔드의 역할은 **파이프라인을 실행시키고 결과를 보여주는 것**에 가깝습니다.

---

# 아키텍처

전체 구조는 다음과 같습니다.

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

특징은 다음과 같습니다.

* **로컬 전용**: API 서버는 `127.0.0.1`에 바인딩
* **외부 DB 없음**: 세션은 로컬 JSON 파일로 저장
* **외부 API 키 불필요**: 로컬 `claude` CLI 사용
* **백엔드 / 프론트엔드 분리**: 서로 독립적인 프로세스로 실행
* **CORS 통신**: 프론트엔드가 FastAPI 서버를 호출
* **추론 엔진 추상화**: CLI 대신 다른 LLM API를 붙일 수 있도록 `Engine` 인터페이스 사용

프론트엔드 API 주소는 `VITE_API_BASE_URL` 환경변수로 변경할 수 있으며, 기본값은 다음과 같습니다.

```text
http://127.0.0.1:8000
```

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

# 문서

제품과 구현에 대한 자세한 내용은 아래 문서에 정리되어 있습니다.

* 제품 컨셉
  `docs/superpowers/specs/2026-08-18-idea-validation-agent-concept.md`

* MVP 아키텍처 설계
  `docs/superpowers/specs/2026-08-18-idea-validation-agent-mvp-design.md`

* MVP 구현 플랜
  `docs/superpowers/plans/2026-08-18-idea-validation-agent-mvp.md`

---

# 로컬 실행

## Backend

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000
```

백엔드:

```text
http://127.0.0.1:8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

프론트엔드:

```text
http://localhost:5173
```

브라우저에서는 **5173번 포트**로 접속하면 됩니다.

---

# 현재 상태

현재 MVP 구현은 완료된 상태입니다.

구현된 범위는 다음과 같습니다.

* 8단계 아이디어 검증 파이프라인
* 로컬 Claude Code CLI 연동
* 단계별 Pydantic 스키마 검증
* 출처 등급 및 Claim 검증
* 리스크 우선순위화
* 로드맵 요약 (판단이 아니라 정리)
* 단계별 실패 및 재시도 처리
* 세션 JSON 저장
* 결과 마크다운 저장
* Vite + React 프론트엔드
* 실제 Claude CLI를 이용한 전체 파이프라인 E2E 검증

현재 프로젝트의 초점은 **"AI가 그럴듯한 사업계획서를 써주는 것"보다 "검증 과정에서 무엇을 알고 있고 무엇을 모르는지 구분해주는 것"**에 있습니다.
