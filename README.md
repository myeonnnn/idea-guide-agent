# 아이디어 검증 & 로드맵 에이전트

## 컨셉과 목표

스타트업 아이디어를 실제로 만들기 전에, AI 에이전트가 8단계 프로토콜(타겟층 → 시장조사 →
가치제안 → 가설 수립 → 가설 검증 → MVP/MLP 정의 → 비즈니스모델 → 종합 판단)을 자동으로
돌려서 **검증된 초안**을 한 번에 만들어주는 개인용 로컬 도구다.

기존 "AI 아이디어 검증 도구"(ValidatorAI, IdeaProof, DimeADozen 등)는 그럴듯한 리포트를
빠르게 뽑아주는 데 최적화돼 있고, 그 안의 시장 규모·통계·근거가 실제로 맞는지 검증하는
장치가 약하다. 이 프로젝트의 목표는 그 반대다:

> **"모르는 것보다 잘못된 정보를 주는 것이 더 나쁘다."**

그래서 이 에이전트가 만드는 모든 결과물은 특정 프로덕트를 실제로 구현하는 게 아니라
"만들지 말지, 무엇을 만들지"를 결정하기 위한 **의사결정용 초안**이며, 그 안의 모든 수치·
주장에는 출처 등급이 붙는다.

## AI 에이전트는 어떻게 동작하는가

이 섹션이 이 문서에서 가장 중요한 부분이다. "에이전트"라고 부르지만 LangChain류의 복잡한
멀티에이전트 프레임워크가 아니라, **구조는 최대한 단순하게 코드로 짜고, 판단이 필요한
부분만 LLM에 위임**하는 방식으로 만들었다.

### 1. 추론 엔진: 로컬 Claude Code CLI

Anthropic API 키를 발급받아 쓰는 대신, 이미 로그인돼 있는 로컬 `claude` CLI(Claude Code)를
서브프로세스로 호출해서 추론 엔진으로 쓴다. 별도 과금 없이 기존 Claude 구독으로 동작한다.

이 부분은 `Engine`이라는 프로토콜(인터페이스)로 추상화되어 있다.

```python
# app/engine/base.py
class Engine(Protocol):
    def generate(self, prompt: str, history: list[Message]) -> EngineResponse: ...
```

지금은 `ClaudeCodeCLIEngine`(`app/engine/claude_cli.py`) 하나만 있고, 이게 하는 일은
`subprocess.run(["claude", "-p", prompt, "--output-format", "json"])`을 실행하고 결과를
파싱하는 것뿐이다. 나중에 Anthropic/OpenAI API로 바꾸고 싶으면 이 인터페이스를 구현하는
새 클래스 하나만 추가하면 되고, 아래에서 설명할 파이프라인 코드는 한 줄도 건드릴 필요가
없다 — 파이프라인은 `Engine`이라는 계약만 알지, 그 뒤에 CLI가 있는지 API가 있는지 모른다.

### 2. 파이프라인: "8번의 구조화된 LLM 호출"

에이전트의 본체는 자유로운 대화가 아니라, **정해진 순서로 8번 호출되는 구조화된 함수들의
체인**이다. 각 단계는 "이전 단계들의 결과를 입력으로 받아, 정해진 JSON 스키마로 출력하는"
하나의 순수한 작업 단위로 설계했다.

```mermaid
graph LR
  A["아이디어 입력<br/>(한 번만)"] --> S1["01 타겟층 설정"]
  S1 --> S2["02 시장조사"]
  S2 --> S3["03 가치제안 · 차별화"]
  S3 --> S4["04 가설 수립"]
  S4 --> S5["05 가설 검증<br/>(리스키스트 어썸션 우선순위화)"]
  S5 --> S6["06 MVP / MLP 정의"]
  S6 --> S7["07 비즈니스모델 가정"]
  S7 --> S8["08 종합 판단<br/>(진행 / 피벗 / 보류)"]
  S8 --> D["완성된 초안<br/>(마크다운 저장 가능)"]
```

단계 순서가 임의로 정해진 게 아니다. 예를 들어 시장 통계(시장조사)보다 타겟층·페인포인트
정의를 먼저 두어서, "그럴듯한 시장 규모부터 찾고 거기에 타겟층을 끼워 맞추는" 하향식
편향을 피하도록 했다. 마지막 종합 판단 단계는 앞의 7단계 결과 전체를 다시 입력받아
"진행 / 피벗 / 보류"를 근거와 함께 판단하는, 파이프라인을 닫는 역할을 한다.

각 단계는 `app/stages/` 아래 파일 하나씩으로 구현돼 있고, 전부 같은 모양을 하고 있다:

```python
# app/stages/*.py 의 공통 패턴
class SomeStageOutput(BaseModel):        # 1. 이 단계가 반드시 지켜야 할 출력 스키마
    ...

class SomeStage(StageDefinition[SomeStageOutput]):
    name = "some_stage"
    output_model = SomeStageOutput

    def build_prompt(self, idea, prior_outputs, user_message=""):
        # 2. 이전 단계 결과들을 컨텍스트로 넣어 프롬프트를 조립
        ...
```

이 정의들을 순서대로 실행하는 게 `app/orchestrator.py`의 `Orchestrator`다. 하는 일은
딱 하나: "지금 몇 번째 단계인지 보고, 그 단계를 실행하고, 성공하면 결과를 세션에 저장하고
다음 단계로 넘어간다"는 상태 기계(state machine)다. 8줄짜리 `PIPELINE` 리스트 순서를
바꾸는 것만으로 단계 순서를 바꿀 수 있다.

### 3. 자가검증(Self-verification): 프롬프트가 아니라 코드로 강제

이 에이전트의 핵심 차별점이다. "출처가 불확실하면 추정이라고 표시해줘" 같은 부탁을
프롬프트에 적어두는 방식은 LLM이 종종 잊어버린다. 그래서 이걸 **Pydantic 검증 로직으로
강제**했다.

```python
# app/verification/models.py
class SourceTier(str, Enum):
    PRIMARY = "PRIMARY"      # 1차 공식 통계/학술자료
    SECONDARY = "SECONDARY"  # 2차 해석/뉴스기사
    ESTIMATE = "ESTIMATE"    # AI 추정치

class Claim(BaseModel):
    text: str
    source_tier: SourceTier
    source_url: str | None = None
```

시장 규모, 경쟁사 분석처럼 사실 주장이 들어가는 모든 필드는 `list[Claim]` 타입으로
선언돼 있고, `validate_claims()`(`app/verification/checks.py`)가 "PRIMARY/SECONDARY
라벨인데 출처 URL이 없으면 검증 실패"라는 규칙을 코드로 강제한다. LLM 응답이 이 규칙을
어기면 Pydantic이 `ValidationError`를 던지고, 아래에서 설명할 재시도 로직이 발동한다.
즉 "출처 등급을 붙여야 한다"는 건 프롬프트의 부탁이 아니라, 어기면 그 응답 자체가
무효 처리되는 스키마 제약이다.

### 4. 파싱/재시도 전략: 실제로 겪은 실패를 반영한 방어 로직

`app/stages/base.py`의 `run_stage()`가 모든 단계 호출의 공통 실행기다. 실제로 브라우저에서
전체 파이프라인을 여러 번 돌려보면서 마주쳤던 실패 패턴들을 그대로 코드에 반영했다:

1. **마크다운 코드펜스 벗기기** — Claude가 순수 JSON만 달라고 해도 ` ```json ... ``` `
   로 감싸서 주는 경우가 많고, 심지어 그 뒤에 설명 문구를 덧붙이기도 한다. 정규식으로
   첫 번째 코드펜스 블록만 추출한 뒤 파싱한다.
2. **1회 재시도** — JSON 파싱이나 스키마 검증(자가검증 포함)이 실패하면, "정확히 스키마와
   일치하는 JSON만 응답하라"는 문구를 덧붙여 한 번 더 호출한다.
3. **그래도 실패하면 경고로 전환** — 재시도까지 실패하면 예외를 던지는 대신
   `StageResult(output=None, warning=..., raw_text=...)`를 반환한다. API 레이어
   (`app/api.py`)는 이걸 `{"status": "warning", ...}` 응답으로 바꿔서 프론트엔드가
   "이번 응답을 정리하지 못했습니다 + 재시도 버튼"을 보여주게 한다.
4. **엔진 자체가 실패해도(타임아웃 등) 죽지 않는다** — `claude` CLI가 타임아웃나거나
   프로세스가 죽는 경우(`EngineError`)도 같은 방식으로 경고로 변환된다. 처음엔 이 부분이
   빠져있어서 500 에러로 튕겨나가는 걸 실제로 겪고 나서 추가했다.

### 5. 프론트엔드는 이 파이프라인을 "그냥 순서대로 호출"할 뿐이다

프론트(`frontend/`, Vite+React+TypeScript)는 별도의 로직을 갖지 않는다. 아이디어를 한 번
제출하면 `POST /session/{id}/message`를 성공할 때마다 재귀적으로 다시 호출해서, 8단계가
끝날 때까지(`complete: true`) 자동으로 진행한다(`frontend/src/App.tsx`의 `runStage`).
사용자는 아이디어 입력 한 번 외에는 개입하지 않고, 단계마다 결과 카드가 보드에 쌓이는
걸 지켜보기만 하면 된다. 실패해서 경고가 뜨면 그 시점에만 재시도 버튼으로 개입한다.

## 아키텍처 요약

- 로컬 전용(127.0.0.1), 외부 API 키 없이 로컬 `claude` CLI(Claude Code)를 추론 엔진으로 사용
- 백엔드(API 서버)와 프론트엔드(웹뷰)는 완전히 분리된 별개 프로세스로 호스팅되고, CORS를 통해 서로 통신한다 — 한쪽이 다른 쪽을 서빙하지 않는다
- 백엔드: Python/FastAPI (`app/`). 파이프라인 오케스트레이션과 자가검증 로직은 코드로 구현(스킬/프롬프트 지시문에만 의존하지 않음)
- 프론트엔드: Vite + React + TypeScript (`frontend/`), 개발 시 `localhost:5173`에서 독립적으로 뜬다. API 서버 주소는 `VITE_API_BASE_URL` 환경변수로 지정 가능(기본값 `http://127.0.0.1:8000`)
- 세션 상태는 로컬 JSON 파일(`data/sessions/`)로 저장 — 외부 DB 없음

## 문서

- 제품 컨셉: [`docs/superpowers/specs/2026-08-18-idea-validation-agent-concept.md`](docs/superpowers/specs/2026-08-18-idea-validation-agent-concept.md)
- MVP 아키텍처 설계: [`docs/superpowers/specs/2026-08-18-idea-validation-agent-mvp-design.md`](docs/superpowers/specs/2026-08-18-idea-validation-agent-mvp-design.md)
- MVP 구현 플랜: [`docs/superpowers/plans/2026-08-18-idea-validation-agent-mvp.md`](docs/superpowers/plans/2026-08-18-idea-validation-agent-mvp.md)

## 로컬 실행

백엔드와 프론트엔드를 각각 별도 터미널에서 띄운다.

```bash
# 백엔드 (http://127.0.0.1:8000)
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000
```

```bash
# 프론트엔드 (http://localhost:5173)
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`으로 접속한다 (8000번이 아니라 5173번).

## 현재 상태

MVP 구현 완료 (백엔드 8단계 파이프라인 + Vite/React 프론트엔드, 리스크 우선순위화·종합판단·마크다운 저장 포함). 실제 `claude` CLI로 전체 파이프라인 E2E 검증 완료.
