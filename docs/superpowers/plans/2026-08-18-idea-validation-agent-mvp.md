# 아이디어 검증 & 로드맵 에이전트 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로컬 `claude` CLI를 추론 엔진으로 사용하는, 6단계 파이프라인(시장조사→타겟층→가설수립→가설검증→MVP/MLP정의→BM가정) 기반 아이디어 검증 웹앱의 동작하는 MVP를 만든다.

**Architecture:** FastAPI 백엔드가 로컬 파일 기반 세션 상태를 관리하며, 각 파이프라인 단계는 `Engine` 프로토콜을 통해서만 추론 엔진(현재는 `ClaudeCodeCLIEngine`, 서브프로세스로 `claude -p`를 호출)과 통신한다. 각 단계는 Pydantic 스키마로 입출력을 강제하고, 사실 주장(claim)은 출처 등급(PRIMARY/SECONDARY/ESTIMATE) 라벨을 코드 레벨에서 검증한다. 프론트엔드는 빌드 스텝 없는 순수 HTML/JS.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, 순수 HTML/JS(프론트엔드)

## Global Constraints

- Anthropic API나 OpenAI API를 직접 호출하지 않는다. 추론은 로컬 `claude` CLI 서브프로세스를 통해서만 이루어진다.
- 모든 서비스는 `127.0.0.1`에만 바인딩한다 (외부 노출 없음).
- 세션 상태는 로컬 JSON 파일(`./data/sessions/`)로 저장한다. 외부 DB를 도입하지 않는다.
- 파이프라인/stage 코드는 `Engine` 프로토콜을 통해서만 추론 엔진에 접근한다. subprocess나 CLI 세부사항을 stage/orchestrator 코드에 직접 노출하지 않는다 (나중에 API 엔진으로 교체 시 stage 파일을 건드리지 않기 위함).
- 사실 주장을 담는 모든 필드는 `Claim` 모델(`source_tier`: PRIMARY/SECONDARY/ESTIMATE)을 사용해야 하며, PRIMARY/SECONDARY 라벨은 `source_url`을 필수로 요구한다.
- 프론트엔드는 빌드 스텝(webpack, npm 등) 없이 순수 HTML/JS로 작성한다.

---

## Task 1: 프로젝트 스캐폴딩 + Engine 인터페이스 + ClaudeCodeCLIEngine

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `app/__init__.py`
- Create: `app/engine/__init__.py`
- Create: `app/engine/base.py`
- Create: `app/engine/claude_cli.py`
- Test: `tests/engine/test_claude_cli.py`
- Test: `tests/__init__.py`, `tests/engine/__init__.py`

**Interfaces:**
- Produces: `Message` (TypedDict: `role: Literal["user","assistant"]`, `content: str`), `EngineResponse` (TypedDict: `text: str`, `raw: dict`), `Engine` (Protocol with `generate(self, prompt: str, history: list[Message]) -> EngineResponse`), `EngineError`/`EngineTimeoutError`/`EngineProcessError`/`EngineParseError` (exceptions, all in `app/engine/base.py`), `ClaudeCodeCLIEngine(timeout_seconds: int = 120, claude_bin: str = "claude")` with `.generate(prompt, history) -> EngineResponse` (in `app/engine/claude_cli.py`)

- [ ] **Step 1: 프로젝트 스캐폴딩**

```bash
mkdir -p app/engine tests/engine
touch app/__init__.py app/engine/__init__.py tests/__init__.py tests/engine/__init__.py
```

`requirements.txt`:
```
fastapi
uvicorn[standard]
pydantic>=2
pytest
httpx
```

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
data/sessions/
```

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 2: `claude` CLI의 실제 JSON 출력 형식을 수동으로 확인**

```bash
claude -p "1+1은 얼마야?" --output-format json
```

Claude Code 문서 기준 예상 출력 형태:
```json
{
  "type": "result",
  "subtype": "success",
  "result": "2입니다.",
  "session_id": "..."
}
```

최종 텍스트 응답이 `result` 필드에 들어있는지 확인한다. 만약 필드명이 다르면(`response`, `text` 등)
Step 6에서 작성할 `ClaudeCodeCLIEngine`의 파싱 로직에서 실제 필드명으로 교체한다.

- [ ] **Step 3: Engine 프로토콜/타입/예외 작성** (`app/engine/base.py`)

```python
from typing import Literal, Protocol, TypedDict


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class EngineResponse(TypedDict):
    text: str
    raw: dict


class EngineError(Exception):
    """Base class for all engine failures."""


class EngineTimeoutError(EngineError):
    pass


class EngineProcessError(EngineError):
    def __init__(self, message: str, stderr: str = "", returncode: int | None = None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


class EngineParseError(EngineError):
    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


class Engine(Protocol):
    def generate(self, prompt: str, history: list[Message]) -> EngineResponse: ...
```

- [ ] **Step 4: `ClaudeCodeCLIEngine`에 대한 실패하는 테스트 작성** (`tests/engine/test_claude_cli.py`)

```python
import json
import subprocess
from unittest.mock import patch

import pytest

from app.engine.base import EngineParseError, EngineProcessError, EngineTimeoutError
from app.engine.claude_cli import ClaudeCodeCLIEngine


def _completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_generate_returns_text_from_result_field():
    engine = ClaudeCodeCLIEngine()
    payload = {"type": "result", "result": "hello world", "session_id": "abc"}
    with patch("subprocess.run", return_value=_completed(stdout=json.dumps(payload))):
        response = engine.generate("hi", history=[])
    assert response["text"] == "hello world"
    assert response["raw"] == payload


def test_generate_raises_timeout_error():
    engine = ClaudeCodeCLIEngine(timeout_seconds=5)
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5)):
        with pytest.raises(EngineTimeoutError):
            engine.generate("hi", history=[])


def test_generate_raises_process_error_when_binary_missing():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(EngineProcessError):
            engine.generate("hi", history=[])


def test_generate_raises_process_error_on_nonzero_exit():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", return_value=_completed(stderr="boom", returncode=1)):
        with pytest.raises(EngineProcessError) as exc_info:
            engine.generate("hi", history=[])
    assert exc_info.value.stderr == "boom"


def test_generate_raises_parse_error_on_invalid_json():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", return_value=_completed(stdout="not json")):
        with pytest.raises(EngineParseError):
            engine.generate("hi", history=[])


def test_generate_raises_parse_error_when_result_field_missing():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", return_value=_completed(stdout=json.dumps({"type": "result"}))):
        with pytest.raises(EngineParseError):
            engine.generate("hi", history=[])
```

- [ ] **Step 5: 테스트 실행 → 실패 확인**

Run: `pytest tests/engine/test_claude_cli.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.engine.claude_cli'`)

- [ ] **Step 6: `ClaudeCodeCLIEngine` 구현** (`app/engine/claude_cli.py`)

```python
import json
import subprocess

from app.engine.base import (
    EngineParseError,
    EngineProcessError,
    EngineResponse,
    EngineTimeoutError,
    Message,
)


class ClaudeCodeCLIEngine:
    def __init__(self, timeout_seconds: int = 120, claude_bin: str = "claude"):
        self.timeout_seconds = timeout_seconds
        self.claude_bin = claude_bin

    def generate(self, prompt: str, history: list[Message]) -> EngineResponse:
        try:
            result = subprocess.run(
                [self.claude_bin, "-p", prompt, "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise EngineTimeoutError(
                f"claude CLI timed out after {self.timeout_seconds}s"
            ) from exc
        except FileNotFoundError as exc:
            raise EngineProcessError(
                f"'{self.claude_bin}' executable not found on PATH"
            ) from exc

        if result.returncode != 0:
            raise EngineProcessError(
                f"claude CLI exited with code {result.returncode}",
                stderr=result.stderr,
                returncode=result.returncode,
            )

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise EngineParseError(
                f"claude CLI returned non-JSON output: {exc}", raw_output=result.stdout
            ) from exc

        text = payload.get("result")
        if not text:
            raise EngineParseError(
                "claude CLI JSON output missing 'result' field", raw_output=result.stdout
            )

        return EngineResponse(text=text, raw=payload)
```

- [ ] **Step 7: 테스트 실행 → 통과 확인**

Run: `pytest tests/engine/test_claude_cli.py -v`
Expected: PASS (6 passed)

- [ ] **Step 8: 커밋**

```bash
git add requirements.txt .gitignore app/ tests/
git commit -m "feat: add Engine protocol and ClaudeCodeCLIEngine"
```

---

## Task 2: 세션 상태 저장소

**Files:**
- Create: `app/session/__init__.py`
- Create: `app/session/models.py`
- Create: `app/session/store.py`
- Test: `tests/session/__init__.py`, `tests/session/test_store.py`

**Interfaces:**
- Consumes: 없음 (독립 모듈)
- Produces: `SessionState` (Pydantic model: `id: str`, `idea: str`, `stage_index: int = 0`, `stage_outputs: dict[str, dict] = {}`, `created_at: datetime`, `updated_at: datetime`), `SessionStore(base_dir: Path)` with `.create(idea: str) -> SessionState`, `.save(session: SessionState) -> None`, `.load(session_id: str) -> SessionState` (raises `FileNotFoundError` if missing)

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/session/test_store.py`)

```python
import pytest

from app.session.store import SessionStore


@pytest.fixture
def store(tmp_path):
    return SessionStore(base_dir=tmp_path / "sessions")


def test_create_returns_session_with_generated_id(store):
    session = store.create(idea="반려동물 산책 매칭 앱")
    assert session.id
    assert session.idea == "반려동물 산책 매칭 앱"
    assert session.stage_index == 0
    assert session.stage_outputs == {}


def test_save_and_load_round_trip(store):
    session = store.create(idea="아이디어")
    session.stage_index = 2
    session.stage_outputs["market_research"] = {"summary": "요약"}
    store.save(session)

    loaded = store.load(session.id)
    assert loaded.id == session.id
    assert loaded.stage_index == 2
    assert loaded.stage_outputs == {"market_research": {"summary": "요약"}}


def test_load_missing_session_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load("does-not-exist")


def test_save_updates_updated_at(store):
    session = store.create(idea="아이디어")
    first_updated_at = session.updated_at
    store.save(session)
    assert session.updated_at >= first_updated_at
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/session/test_store.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.session'`)

- [ ] **Step 3: `SessionState` 모델 작성** (`app/session/models.py`)

```python
from datetime import datetime
from pydantic import BaseModel, Field


class SessionState(BaseModel):
    id: str
    idea: str
    stage_index: int = 0
    stage_outputs: dict[str, dict] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 4: `SessionStore` 구현** (`app/session/store.py`)

```python
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.session.models import SessionState


class SessionStore:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def create(self, idea: str) -> SessionState:
        now = datetime.now(timezone.utc)
        session = SessionState(id=str(uuid.uuid4()), idea=idea, created_at=now, updated_at=now)
        self.save(session)
        return session

    def save(self, session: SessionState) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self._path(session.id).write_text(session.model_dump_json(indent=2))

    def load(self, session_id: str) -> SessionState:
        path = self._path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"No session found with id {session_id}")
        return SessionState.model_validate_json(path.read_text())
```

- [ ] **Step 5: 테스트 실행 → 통과 확인**

Run: `pytest tests/session/test_store.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: 커밋**

```bash
git add app/session/ tests/session/
git commit -m "feat: add file-based session state store"
```

---

## Task 3: 자가검증 모듈 (출처 등급 라벨링)

**Files:**
- Create: `app/verification/__init__.py`
- Create: `app/verification/models.py`
- Create: `app/verification/checks.py`
- Test: `tests/verification/__init__.py`, `tests/verification/test_checks.py`

**Interfaces:**
- Consumes: 없음 (독립 모듈)
- Produces: `SourceTier` (str Enum: `PRIMARY`, `SECONDARY`, `ESTIMATE`, in `app/verification/models.py`), `Claim` (Pydantic model: `text: str`, `source_tier: SourceTier`, `source_url: str | None = None`), `validate_claims(claims: list[Claim]) -> list[str]` (in `app/verification/checks.py`, 위반사항 메시지 리스트 반환, 빈 리스트면 통과)

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/verification/test_checks.py`)

```python
from app.verification.checks import validate_claims
from app.verification.models import Claim, SourceTier


def test_primary_claim_without_url_is_invalid():
    claims = [Claim(text="시장규모 100억원", source_tier=SourceTier.PRIMARY, source_url=None)]
    errors = validate_claims(claims)
    assert len(errors) == 1
    assert "시장규모 100억원" in errors[0]


def test_secondary_claim_without_url_is_invalid():
    claims = [Claim(text="업계 뉴스", source_tier=SourceTier.SECONDARY, source_url=None)]
    errors = validate_claims(claims)
    assert len(errors) == 1


def test_estimate_claim_without_url_is_valid():
    claims = [Claim(text="추정치", source_tier=SourceTier.ESTIMATE, source_url=None)]
    errors = validate_claims(claims)
    assert errors == []


def test_primary_claim_with_url_is_valid():
    claims = [
        Claim(text="공식 통계", source_tier=SourceTier.PRIMARY, source_url="https://stats.example.com")
    ]
    errors = validate_claims(claims)
    assert errors == []
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/verification/test_checks.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.verification'`)

- [ ] **Step 3: `SourceTier`/`Claim` 작성** (`app/verification/models.py`)

```python
from enum import Enum

from pydantic import BaseModel


class SourceTier(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    ESTIMATE = "ESTIMATE"


class Claim(BaseModel):
    text: str
    source_tier: SourceTier
    source_url: str | None = None
```

- [ ] **Step 4: `validate_claims` 구현** (`app/verification/checks.py`)

```python
from app.verification.models import Claim, SourceTier


def validate_claims(claims: list[Claim]) -> list[str]:
    errors: list[str] = []
    for claim in claims:
        if claim.source_tier in (SourceTier.PRIMARY, SourceTier.SECONDARY) and not claim.source_url:
            errors.append(
                f"claim '{claim.text}' labeled {claim.source_tier.value} but missing source_url"
            )
    return errors
```

- [ ] **Step 5: 테스트 실행 → 통과 확인**

Run: `pytest tests/verification/test_checks.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: 커밋**

```bash
git add app/verification/ tests/verification/
git commit -m "feat: add source-tier claim verification"
```

---

## Task 4: Stage 실행 프레임워크 + 시장조사 단계

**Files:**
- Create: `app/stages/__init__.py`
- Create: `app/stages/base.py`
- Create: `app/stages/market_research.py`
- Test: `tests/stages/__init__.py`, `tests/stages/test_base.py`, `tests/stages/test_market_research.py`

**Interfaces:**
- Consumes: `Engine`, `EngineResponse` (Task 1), `Claim`, `SourceTier`, `validate_claims` (Task 3)
- Produces: `StageResult[T]` (dataclass: `output: T | None`, `warning: str | None = None`, `raw_text: str | None = None`), `StageDefinition[T]` (base class: attrs `name: str`, `output_model: Type[T]`; method `build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str`), `run_stage(engine: Engine, stage: StageDefinition[T], idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> StageResult[T]` (all in `app/stages/base.py`), `MarketResearchOutput`, `MarketResearchStage` (in `app/stages/market_research.py`, `name = "market_research"`)

- [ ] **Step 1: `app/stages/base.py`에 대한 실패하는 테스트 작성** (`tests/stages/test_base.py`)

```python
from dataclasses import dataclass
from typing import ClassVar

from pydantic import BaseModel

from app.stages.base import StageDefinition, run_stage


class DummyOutput(BaseModel):
    value: str


class DummyStage(StageDefinition[DummyOutput]):
    name = "dummy"
    output_model = DummyOutput

    def build_prompt(self, idea, prior_outputs, user_message=""):
        return f"idea={idea}"


class FakeEngine:
    def __init__(self, texts: list[str]):
        self.texts = list(texts)
        self.calls: list[str] = []

    def generate(self, prompt: str, history: list):
        self.calls.append(prompt)
        text = self.texts.pop(0)
        return {"text": text, "raw": {}}


def test_run_stage_success_on_first_try():
    engine = FakeEngine(['{"value": "ok"}'])
    result = run_stage(engine, DummyStage(), idea="x", prior_outputs={})
    assert result.output == DummyOutput(value="ok")
    assert result.warning is None
    assert len(engine.calls) == 1


def test_run_stage_retries_once_on_invalid_json_then_succeeds():
    engine = FakeEngine(["not json", '{"value": "ok"}'])
    result = run_stage(engine, DummyStage(), idea="x", prior_outputs={})
    assert result.output == DummyOutput(value="ok")
    assert len(engine.calls) == 2


def test_run_stage_falls_back_with_warning_after_two_failures():
    engine = FakeEngine(["not json", "still not json"])
    result = run_stage(engine, DummyStage(), idea="x", prior_outputs={})
    assert result.output is None
    assert result.warning is not None
    assert result.raw_text == "still not json"


def test_run_stage_falls_back_on_schema_validation_failure():
    engine = FakeEngine(['{"wrong_field": "x"}', '{"wrong_field": "x"}'])
    result = run_stage(engine, DummyStage(), idea="x", prior_outputs={})
    assert result.output is None
    assert result.warning is not None
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/stages/test_base.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.stages'`)

- [ ] **Step 3: `app/stages/base.py` 구현**

```python
import json
from dataclasses import dataclass
from typing import Generic, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.engine.base import Engine

T = TypeVar("T", bound=BaseModel)


@dataclass
class StageResult(Generic[T]):
    output: T | None
    warning: str | None = None
    raw_text: str | None = None


class StageDefinition(Generic[T]):
    name: str
    output_model: Type[T]

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        raise NotImplementedError


def _parse_and_validate(stage: StageDefinition[T], text: str) -> tuple[T | None, str | None]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"JSON 파싱 실패: {exc}"
    try:
        return stage.output_model.model_validate(data), None
    except ValidationError as exc:
        return None, f"스키마 검증 실패: {exc}"


def run_stage(
    engine: Engine,
    stage: StageDefinition[T],
    idea: str,
    prior_outputs: dict[str, dict],
    user_message: str = "",
) -> StageResult[T]:
    prompt = stage.build_prompt(idea, prior_outputs, user_message)
    response = engine.generate(prompt, history=[])
    output, warning = _parse_and_validate(stage, response["text"])

    if output is None:
        retry_prompt = (
            prompt
            + "\n\n이전 응답이 유효하지 않았습니다. 반드시 위에서 요구한 JSON 스키마와 "
            "정확히 일치하는, 유효한 JSON 객체 하나만 응답하세요. 다른 텍스트를 포함하지 마세요."
        )
        response = engine.generate(retry_prompt, history=[])
        output, warning = _parse_and_validate(stage, response["text"])

    if output is None:
        return StageResult(output=None, warning=warning, raw_text=response["text"])

    return StageResult(output=output, warning=None)
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/stages/test_base.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 시장조사 단계에 대한 실패하는 테스트 작성** (`tests/stages/test_market_research.py`)

```python
from app.stages.market_research import MarketResearchOutput, MarketResearchStage


def test_build_prompt_includes_idea():
    stage = MarketResearchStage()
    prompt = stage.build_prompt(idea="반려동물 산책 매칭 앱", prior_outputs={})
    assert "반려동물 산책 매칭 앱" in prompt
    assert "source_tier" in prompt


def test_build_prompt_includes_user_message_when_present():
    stage = MarketResearchStage()
    prompt = stage.build_prompt(idea="x", prior_outputs={}, user_message="한국 시장 위주로")
    assert "한국 시장 위주로" in prompt


def test_output_model_accepts_valid_estimate_claim():
    output = MarketResearchOutput(
        summary="요약",
        market_size_claims=[{"text": "추정치", "source_tier": "ESTIMATE", "source_url": None}],
        key_competitors=["A"],
    )
    assert output.summary == "요약"


def test_output_model_rejects_primary_claim_without_url():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        MarketResearchOutput(
            summary="요약",
            market_size_claims=[{"text": "주장", "source_tier": "PRIMARY", "source_url": None}],
            key_competitors=[],
        )
```

- [ ] **Step 6: 테스트 실행 → 실패 확인**

Run: `pytest tests/stages/test_market_research.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.stages.market_research'`)

- [ ] **Step 7: `app/stages/market_research.py` 구현**

```python
from pydantic import BaseModel, model_validator

from app.stages.base import StageDefinition
from app.verification.checks import validate_claims
from app.verification.models import Claim


class MarketResearchOutput(BaseModel):
    summary: str
    market_size_claims: list[Claim]
    key_competitors: list[str]

    @model_validator(mode="after")
    def _check_claims(self):
        errors = validate_claims(self.market_size_claims)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class MarketResearchStage(StageDefinition[MarketResearchOutput]):
    name = "market_research"
    output_model = MarketResearchOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 스타트업 아이디어의 시장을 조사하는 애널리스트입니다.

아이디어: {idea}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "summary": "시장 개요 요약 (string)",
  "market_size_claims": [
    {{"text": "주장 내용", "source_tier": "PRIMARY|SECONDARY|ESTIMATE", "source_url": "출처 URL 또는 null"}}
  ],
  "key_competitors": ["경쟁사 이름", "..."]
}}

규칙:
- market_size_claims의 각 항목은 반드시 source_tier를 PRIMARY(1차 공식 통계/학술자료), SECONDARY(2차 해석/뉴스기사), ESTIMATE(AI 추정치) 중 하나로 라벨링하세요.
- PRIMARY 또는 SECONDARY 라벨인 경우 source_url을 반드시 포함하세요.
- 확실하지 않은 수치는 ESTIMATE로 명확히 표시하세요."""
```

- [ ] **Step 8: 테스트 실행 → 통과 확인**

Run: `pytest tests/stages/test_market_research.py -v`
Expected: PASS (4 passed)

- [ ] **Step 9: 커밋**

```bash
git add app/stages/ tests/stages/
git commit -m "feat: add stage execution framework and market research stage"
```

---

## Task 5: 타겟층 설정 단계

**Files:**
- Create: `app/stages/target_segment.py`
- Test: `tests/stages/test_target_segment.py`

**Interfaces:**
- Consumes: `StageDefinition`, `Claim`, `validate_claims` (Task 3, 4)
- Produces: `TargetSegmentOutput`, `TargetSegmentStage` (`name = "target_segment"`, prior_outputs에서 `"market_research"` 키를 읽음)

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/stages/test_target_segment.py`)

```python
import pytest
from pydantic import ValidationError

from app.stages.target_segment import TargetSegmentOutput, TargetSegmentStage


def test_build_prompt_includes_prior_market_research():
    stage = TargetSegmentStage()
    prior = {"market_research": {"summary": "펫케어 시장은 성장 중"}}
    prompt = stage.build_prompt(idea="반려동물 산책 매칭 앱", prior_outputs=prior)
    assert "반려동물 산책 매칭 앱" in prompt
    assert "펫케어 시장은 성장 중" in prompt


def test_output_model_valid():
    output = TargetSegmentOutput(
        primary_segment="1인 가구 반려인",
        segment_description="설명",
        pain_points=["시간 부족"],
        claims=[{"text": "추정", "source_tier": "ESTIMATE", "source_url": None}],
    )
    assert output.primary_segment == "1인 가구 반려인"


def test_output_model_rejects_secondary_claim_without_url():
    with pytest.raises(ValidationError):
        TargetSegmentOutput(
            primary_segment="x",
            segment_description="x",
            pain_points=[],
            claims=[{"text": "뉴스 인용", "source_tier": "SECONDARY", "source_url": None}],
        )
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/stages/test_target_segment.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: `app/stages/target_segment.py` 구현**

```python
import json

from pydantic import BaseModel, model_validator

from app.stages.base import StageDefinition
from app.verification.checks import validate_claims
from app.verification.models import Claim


class TargetSegmentOutput(BaseModel):
    primary_segment: str
    segment_description: str
    pain_points: list[str]
    claims: list[Claim]

    @model_validator(mode="after")
    def _check_claims(self):
        errors = validate_claims(self.claims)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class TargetSegmentStage(StageDefinition[TargetSegmentOutput]):
    name = "target_segment"
    output_model = TargetSegmentOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        market_research = prior_outputs.get("market_research", {})
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 스타트업의 타겟 고객층을 분석하는 전략 컨설턴트입니다.

아이디어: {idea}

이전 단계(시장조사) 결과:
{json.dumps(market_research, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "primary_segment": "주 타겟 고객층 이름 (string)",
  "segment_description": "타겟층 설명 (string)",
  "pain_points": ["핵심 페인포인트", "..."],
  "claims": [
    {{"text": "주장 내용", "source_tier": "PRIMARY|SECONDARY|ESTIMATE", "source_url": "출처 URL 또는 null"}}
  ]
}}

규칙:
- claims의 각 항목은 반드시 source_tier를 PRIMARY, SECONDARY, ESTIMATE 중 하나로 라벨링하세요.
- PRIMARY 또는 SECONDARY 라벨인 경우 source_url을 반드시 포함하세요."""
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/stages/test_target_segment.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add app/stages/target_segment.py tests/stages/test_target_segment.py
git commit -m "feat: add target segment stage"
```

---

## Task 6: 가설 수립 단계

**Files:**
- Create: `app/stages/hypothesis.py`
- Test: `tests/stages/test_hypothesis.py`

**Interfaces:**
- Consumes: `StageDefinition` (Task 4)
- Produces: `AssumptionType` (str Enum: `desirability`, `viability`, `feasibility`), `Hypothesis` (Pydantic model), `HypothesisOutput`, `HypothesisStage` (`name = "hypothesis"`, prior_outputs에서 `"market_research"`, `"target_segment"` 키를 읽음)

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/stages/test_hypothesis.py`)

```python
from app.stages.hypothesis import HypothesisOutput, HypothesisStage


def test_build_prompt_includes_prior_context():
    stage = HypothesisStage()
    prior = {
        "market_research": {"summary": "요약"},
        "target_segment": {"primary_segment": "1인 가구"},
    }
    prompt = stage.build_prompt(idea="반려동물 산책 매칭 앱", prior_outputs=prior)
    assert "1인 가구" in prompt
    assert "desirability" in prompt


def test_output_model_valid():
    output = HypothesisOutput(
        hypotheses=[
            {
                "statement": "1인 가구는 산책 대행 서비스에 월 3만원을 지불할 것이다",
                "assumption_type": "desirability",
                "validation_method": "설문조사",
            }
        ]
    )
    assert len(output.hypotheses) == 1
    assert output.hypotheses[0].assumption_type == "desirability"
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/stages/test_hypothesis.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: `app/stages/hypothesis.py` 구현**

```python
import json
from enum import Enum

from pydantic import BaseModel

from app.stages.base import StageDefinition


class AssumptionType(str, Enum):
    DESIRABILITY = "desirability"
    VIABILITY = "viability"
    FEASIBILITY = "feasibility"


class Hypothesis(BaseModel):
    statement: str
    assumption_type: AssumptionType
    validation_method: str


class HypothesisOutput(BaseModel):
    hypotheses: list[Hypothesis]


class HypothesisStage(StageDefinition[HypothesisOutput]):
    name = "hypothesis"
    output_model = HypothesisOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        context = {
            "market_research": prior_outputs.get("market_research", {}),
            "target_segment": prior_outputs.get("target_segment", {}),
        }
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 린 캔버스 방식으로 검증 가능한 가설을 세우는 전문가입니다.

아이디어: {idea}

이전 단계 결과:
{json.dumps(context, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "hypotheses": [
    {{
      "statement": "검증 가능한 가설 문장 (string)",
      "assumption_type": "desirability|viability|feasibility",
      "validation_method": "이 가설을 검증하기 위해 필요한 구체적 방법 (설문/인터뷰/랜딩페이지 테스트 등)"
    }}
  ]
}}

규칙:
- 최소 3개, 최대 6개의 가설을 제시하세요.
- 각 가설은 반드시 desirability(고객이 원하는가), viability(사업으로 성립하는가), feasibility(만들 수 있는가) 중 하나로 분류하세요."""
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/stages/test_hypothesis.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add app/stages/hypothesis.py tests/stages/test_hypothesis.py
git commit -m "feat: add hypothesis stage"
```

---

## Task 7: 가설 검증 단계

**Files:**
- Create: `app/stages/hypothesis_validation.py`
- Test: `tests/stages/test_hypothesis_validation.py`

**Interfaces:**
- Consumes: `StageDefinition` (Task 4)
- Produces: `ConfidenceLevel` (str Enum: `low`, `medium`, `high`), `HypothesisValidationItem`, `HypothesisValidationOutput`, `HypothesisValidationStage` (`name = "hypothesis_validation"`, prior_outputs에서 `"hypothesis"` 키를 읽음)

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/stages/test_hypothesis_validation.py`)

```python
from app.stages.hypothesis_validation import HypothesisValidationOutput, HypothesisValidationStage


def test_build_prompt_includes_prior_hypotheses():
    stage = HypothesisValidationStage()
    prior = {"hypothesis": {"hypotheses": [{"statement": "월 3만원 지불 의향"}]}}
    prompt = stage.build_prompt(idea="x", prior_outputs=prior)
    assert "월 3만원 지불 의향" in prompt


def test_output_model_valid():
    output = HypothesisValidationOutput(
        validations=[
            {
                "hypothesis_statement": "월 3만원 지불 의향",
                "validation_plan": "랜딩페이지 스모크테스트",
                "required_evidence": "전환율 5% 이상",
                "confidence": "medium",
            }
        ]
    )
    assert output.validations[0].confidence == "medium"
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/stages/test_hypothesis_validation.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: `app/stages/hypothesis_validation.py` 구현**

```python
import json
from enum import Enum

from pydantic import BaseModel

from app.stages.base import StageDefinition


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HypothesisValidationItem(BaseModel):
    hypothesis_statement: str
    validation_plan: str
    required_evidence: str
    confidence: ConfidenceLevel


class HypothesisValidationOutput(BaseModel):
    validations: list[HypothesisValidationItem]


class HypothesisValidationStage(StageDefinition[HypothesisValidationOutput]):
    name = "hypothesis_validation"
    output_model = HypothesisValidationOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        hypothesis_output = prior_outputs.get("hypothesis", {})
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 가설 검증 계획을 구체화하는 전문가입니다.

아이디어: {idea}

이전 단계(가설 수립) 결과:
{json.dumps(hypothesis_output, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "validations": [
    {{
      "hypothesis_statement": "위 가설 문장을 그대로 복사",
      "validation_plan": "이 가설을 검증할 구체적 실행 계획",
      "required_evidence": "가설이 참이라고 판단하기 위해 필요한 증거/기준",
      "confidence": "low|medium|high"
    }}
  ]
}}

규칙:
- 이전 단계의 모든 가설에 대해 하나씩 검증 계획을 작성하세요.
- confidence는 현재 시점에서 이 가설이 참일 것이라는 확신도를 나타냅니다."""
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/stages/test_hypothesis_validation.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add app/stages/hypothesis_validation.py tests/stages/test_hypothesis_validation.py
git commit -m "feat: add hypothesis validation stage"
```

---

## Task 8: MVP/MLP 정의 단계

**Files:**
- Create: `app/stages/mvp_mlp.py`
- Test: `tests/stages/test_mvp_mlp.py`

**Interfaces:**
- Consumes: `StageDefinition` (Task 4)
- Produces: `MvpMlpOutput`, `MvpMlpStage` (`name = "mvp_mlp"`, prior_outputs에서 `"target_segment"`, `"hypothesis"`, `"hypothesis_validation"` 키를 읽음)

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/stages/test_mvp_mlp.py`)

```python
from app.stages.mvp_mlp import MvpMlpOutput, MvpMlpStage


def test_build_prompt_includes_prior_context():
    stage = MvpMlpStage()
    prior = {"hypothesis_validation": {"validations": [{"confidence": "high"}]}}
    prompt = stage.build_prompt(idea="x", prior_outputs=prior)
    assert "high" in prompt


def test_output_model_valid():
    output = MvpMlpOutput(
        mvp_scope=["매칭 알고리즘 없이 수동 매칭"],
        mlp_scope=["자동 매칭", "결제"],
        success_metrics=["첫 주 매칭 성사율 30%"],
    )
    assert len(output.mvp_scope) == 1
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/stages/test_mvp_mlp.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: `app/stages/mvp_mlp.py` 구현**

```python
import json

from pydantic import BaseModel

from app.stages.base import StageDefinition


class MvpMlpOutput(BaseModel):
    mvp_scope: list[str]
    mlp_scope: list[str]
    success_metrics: list[str]


class MvpMlpStage(StageDefinition[MvpMlpOutput]):
    name = "mvp_mlp"
    output_model = MvpMlpOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        context = {
            "target_segment": prior_outputs.get("target_segment", {}),
            "hypothesis": prior_outputs.get("hypothesis", {}),
            "hypothesis_validation": prior_outputs.get("hypothesis_validation", {}),
        }
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 MVP와 MLP 범위를 정의하는 프로덕트 전략가입니다.

아이디어: {idea}

이전 단계 결과:
{json.dumps(context, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "mvp_scope": ["MVP에 포함할 최소 기능", "..."],
  "mlp_scope": ["MLP(Minimum Lovable Product)에 포함할 기능", "..."],
  "success_metrics": ["이 단계 성공을 판단할 지표", "..."]
}}

규칙:
- mvp_scope는 가설 검증에 필요한 최소한의 기능만 포함하세요.
- success_metrics는 측정 가능한 형태로 작성하세요."""
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/stages/test_mvp_mlp.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add app/stages/mvp_mlp.py tests/stages/test_mvp_mlp.py
git commit -m "feat: add MVP/MLP definition stage"
```

---

## Task 9: 비즈니스모델 가정 단계

**Files:**
- Create: `app/stages/business_model.py`
- Test: `tests/stages/test_business_model.py`

**Interfaces:**
- Consumes: `StageDefinition`, `Claim`, `validate_claims` (Task 3, 4)
- Produces: `BusinessModelOutput`, `BusinessModelStage` (`name = "business_model"`, prior_outputs에서 `"target_segment"`, `"mvp_mlp"` 키를 읽음)

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/stages/test_business_model.py`)

```python
import pytest
from pydantic import ValidationError

from app.stages.business_model import BusinessModelOutput, BusinessModelStage


def test_build_prompt_includes_prior_context():
    stage = BusinessModelStage()
    prior = {"mvp_mlp": {"mvp_scope": ["수동 매칭"]}}
    prompt = stage.build_prompt(idea="x", prior_outputs=prior)
    assert "수동 매칭" in prompt


def test_output_model_valid():
    output = BusinessModelOutput(
        revenue_model="구독형",
        channels=["인스타그램 광고"],
        cost_structure=["매칭 알고리즘 개발", "고객지원"],
        claims=[{"text": "추정", "source_tier": "ESTIMATE", "source_url": None}],
    )
    assert output.revenue_model == "구독형"


def test_output_model_rejects_primary_claim_without_url():
    with pytest.raises(ValidationError):
        BusinessModelOutput(
            revenue_model="x",
            channels=[],
            cost_structure=[],
            claims=[{"text": "주장", "source_tier": "PRIMARY", "source_url": None}],
        )
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/stages/test_business_model.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: `app/stages/business_model.py` 구현**

```python
import json

from pydantic import BaseModel, model_validator

from app.stages.base import StageDefinition
from app.verification.checks import validate_claims
from app.verification.models import Claim


class BusinessModelOutput(BaseModel):
    revenue_model: str
    channels: list[str]
    cost_structure: list[str]
    claims: list[Claim]

    @model_validator(mode="after")
    def _check_claims(self):
        errors = validate_claims(self.claims)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class BusinessModelStage(StageDefinition[BusinessModelOutput]):
    name = "business_model"
    output_model = BusinessModelOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        context = {
            "target_segment": prior_outputs.get("target_segment", {}),
            "mvp_mlp": prior_outputs.get("mvp_mlp", {}),
        }
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 비즈니스 모델을 구조화하는 전략 컨설턴트입니다.

아이디어: {idea}

이전 단계 결과:
{json.dumps(context, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "revenue_model": "수익모델 설명 (string)",
  "channels": ["유통/마케팅 채널", "..."],
  "cost_structure": ["주요 비용 항목", "..."],
  "claims": [
    {{"text": "주장 내용", "source_tier": "PRIMARY|SECONDARY|ESTIMATE", "source_url": "출처 URL 또는 null"}}
  ]
}}

규칙:
- claims의 각 항목은 반드시 source_tier를 PRIMARY, SECONDARY, ESTIMATE 중 하나로 라벨링하세요.
- PRIMARY 또는 SECONDARY 라벨인 경우 source_url을 반드시 포함하세요."""
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/stages/test_business_model.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add app/stages/business_model.py tests/stages/test_business_model.py
git commit -m "feat: add business model assumptions stage"
```

---

## Task 10: 오케스트레이터

**Files:**
- Create: `app/orchestrator.py`
- Test: `tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `SessionState` (Task 2), `Engine` (Task 1), `StageDefinition`, `StageResult`, `run_stage` (Task 4), 6개 Stage 클래스 (Task 4~9)
- Produces: `PIPELINE: list[StageDefinition]` (6단계 순서: market_research, target_segment, hypothesis, hypothesis_validation, mvp_mlp, business_model), `Orchestrator(stages: list[StageDefinition])` with `.is_complete(session) -> bool`, `.current_stage_name(session) -> str`, `.advance(session, engine, user_message="") -> StageResult`

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/test_orchestrator.py`)

```python
from datetime import datetime, timezone

from app.orchestrator import Orchestrator
from app.session.models import SessionState
from app.stages.base import StageDefinition
from pydantic import BaseModel


class StubOutput(BaseModel):
    stage: str


def make_stage(stage_name: str, next_text: str):
    class StubStage(StageDefinition[StubOutput]):
        name = stage_name
        output_model = StubOutput

        def build_prompt(self, idea, prior_outputs, user_message=""):
            return f"prompt for {stage_name}"

    return StubStage(), next_text


class FakeEngine:
    def __init__(self, texts):
        self.texts = list(texts)

    def generate(self, prompt, history):
        return {"text": self.texts.pop(0), "raw": {}}


def make_session():
    now = datetime.now(timezone.utc)
    return SessionState(id="s1", idea="아이디어", created_at=now, updated_at=now)


def test_advance_runs_current_stage_and_increments_index():
    stage_a, _ = make_stage("stage_a", '{"stage": "a"}')
    stage_b, _ = make_stage("stage_b", '{"stage": "b"}')
    orchestrator = Orchestrator(stages=[stage_a, stage_b])
    engine = FakeEngine(['{"stage": "a"}'])
    session = make_session()

    result = orchestrator.advance(session, engine)

    assert result.output == StubOutput(stage="a")
    assert session.stage_index == 1
    assert session.stage_outputs["stage_a"] == {"stage": "a"}


def test_advance_does_not_increment_index_on_failure():
    stage_a, _ = make_stage("stage_a", "not json")
    orchestrator = Orchestrator(stages=[stage_a])
    engine = FakeEngine(["not json", "still not json"])
    session = make_session()

    result = orchestrator.advance(session, engine)

    assert result.output is None
    assert session.stage_index == 0
    assert session.stage_outputs == {}


def test_is_complete_after_all_stages_run():
    stage_a, _ = make_stage("stage_a", '{"stage": "a"}')
    orchestrator = Orchestrator(stages=[stage_a])
    engine = FakeEngine(['{"stage": "a"}'])
    session = make_session()

    assert orchestrator.is_complete(session) is False
    orchestrator.advance(session, engine)
    assert orchestrator.is_complete(session) is True


def test_current_stage_name_returns_expected_stage():
    stage_a, _ = make_stage("stage_a", "")
    stage_b, _ = make_stage("stage_b", "")
    orchestrator = Orchestrator(stages=[stage_a, stage_b])
    session = make_session()
    session.stage_index = 1

    assert orchestrator.current_stage_name(session) == "stage_b"
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.orchestrator'`)

- [ ] **Step 3: `app/orchestrator.py` 구현**

```python
from app.engine.base import Engine
from app.session.models import SessionState
from app.stages.base import StageDefinition, StageResult, run_stage
from app.stages.business_model import BusinessModelStage
from app.stages.hypothesis import HypothesisStage
from app.stages.hypothesis_validation import HypothesisValidationStage
from app.stages.market_research import MarketResearchStage
from app.stages.mvp_mlp import MvpMlpStage
from app.stages.target_segment import TargetSegmentStage

PIPELINE: list[StageDefinition] = [
    MarketResearchStage(),
    TargetSegmentStage(),
    HypothesisStage(),
    HypothesisValidationStage(),
    MvpMlpStage(),
    BusinessModelStage(),
]


class Orchestrator:
    def __init__(self, stages: list[StageDefinition]):
        self.stages = stages

    def is_complete(self, session: SessionState) -> bool:
        return session.stage_index >= len(self.stages)

    def current_stage_name(self, session: SessionState) -> str:
        return self.stages[session.stage_index].name

    def advance(self, session: SessionState, engine: Engine, user_message: str = "") -> StageResult:
        stage = self.stages[session.stage_index]
        result = run_stage(engine, stage, session.idea, session.stage_outputs, user_message)
        if result.output is not None:
            session.stage_outputs[stage.name] = result.output.model_dump(mode="json")
            session.stage_index += 1
        return result
```

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/test_orchestrator.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add app/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add pipeline orchestrator"
```

---

## Task 11: FastAPI 라우트

**Files:**
- Create: `app/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `ClaudeCodeCLIEngine` (Task 1), `SessionStore` (Task 2), `Orchestrator`, `PIPELINE` (Task 10)
- Produces: `app` (FastAPI 인스턴스, module-level `store`/`engine`/`orchestrator` in `app/api.py`), 라우트 `POST /session`, `POST /session/{session_id}/message`, `GET /session/{session_id}`

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/test_api.py`)

```python
import json

import pytest
from fastapi.testclient import TestClient

import app.api as api_module

VALID_MARKET_RESEARCH_JSON = json.dumps(
    {
        "summary": "요약",
        "market_size_claims": [{"text": "추정", "source_tier": "ESTIMATE", "source_url": None}],
        "key_competitors": ["A", "B"],
    }
)


class FakeEngine:
    def __init__(self, responses):
        self.responses = list(responses)

    def generate(self, prompt, history):
        text = self.responses.pop(0)
        return {"text": text, "raw": {}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app.session.store import SessionStore

    monkeypatch.setattr(api_module, "store", SessionStore(base_dir=tmp_path / "sessions"))
    return TestClient(api_module.app)


def test_create_session_returns_id(client):
    response = client.post("/session", json={"idea": "반려동물 산책 매칭 앱"})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["stage_index"] == 0


def test_message_advances_stage_on_valid_response(client, monkeypatch):
    monkeypatch.setattr(api_module, "engine", FakeEngine([VALID_MARKET_RESEARCH_JSON]))
    session_id = client.post("/session", json={"idea": "아이디어"}).json()["session_id"]

    response = client.post(f"/session/{session_id}/message", json={"message": ""})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["stage_name"] == "market_research"
    assert body["stage_index"] == 1
    assert body["complete"] is False


def test_message_returns_warning_on_invalid_response(client, monkeypatch):
    monkeypatch.setattr(api_module, "engine", FakeEngine(["not json", "still not json"]))
    session_id = client.post("/session", json={"idea": "아이디어"}).json()["session_id"]

    response = client.post(f"/session/{session_id}/message", json={"message": ""})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "warning"
    assert body["warning"] is not None


def test_message_for_unknown_session_returns_404(client):
    response = client.post("/session/does-not-exist/message", json={"message": ""})
    assert response.status_code == 404


def test_get_session_returns_state(client):
    session_id = client.post("/session", json={"idea": "아이디어"}).json()["session_id"]
    response = client.get(f"/session/{session_id}")
    assert response.status_code == 200
    assert response.json()["idea"] == "아이디어"
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run: `pytest tests/test_api.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.api'`)

- [ ] **Step 3: `app/api.py` 구현**

```python
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.engine.claude_cli import ClaudeCodeCLIEngine
from app.orchestrator import PIPELINE, Orchestrator
from app.session.store import SessionStore

app = FastAPI()
store = SessionStore(base_dir=Path("./data/sessions"))
engine = ClaudeCodeCLIEngine()
orchestrator = Orchestrator(PIPELINE)


class CreateSessionRequest(BaseModel):
    idea: str


class MessageRequest(BaseModel):
    message: str = ""


@app.post("/session")
def create_session(req: CreateSessionRequest):
    session = store.create(idea=req.idea)
    return {"session_id": session.id, "stage_index": session.stage_index}


@app.post("/session/{session_id}/message")
def send_message(session_id: str, req: MessageRequest):
    try:
        session = store.load(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session not found")

    if orchestrator.is_complete(session):
        raise HTTPException(status_code=400, detail="pipeline already complete")

    stage_name = orchestrator.current_stage_name(session)
    result = orchestrator.advance(session, engine, user_message=req.message)

    if result.output is None:
        return {
            "status": "warning",
            "warning": result.warning,
            "raw_text": result.raw_text,
            "stage_index": session.stage_index,
        }

    store.save(session)
    return {
        "status": "ok",
        "stage_name": stage_name,
        "output": result.output.model_dump(mode="json"),
        "stage_index": session.stage_index,
        "complete": orchestrator.is_complete(session),
    }


@app.get("/session/{session_id}")
def get_session(session_id: str):
    try:
        session = store.load(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session not found")
    return session.model_dump(mode="json")
```

**주의:** 테스트는 `monkeypatch.setattr(api_module, "engine", FakeEngine(...))`로 모듈 레벨
`engine`을 교체한다. `app/api.py` 내부의 라우트 함수가 `engine` 전역 변수를 참조하도록
유지해야 monkeypatch가 적용된다 (함수 인자 기본값으로 캡처하지 말 것).

- [ ] **Step 4: 테스트 실행 → 통과 확인**

Run: `pytest tests/test_api.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: 커밋**

```bash
git add app/api.py tests/test_api.py
git commit -m "feat: add FastAPI routes for session pipeline"
```

---

## Task 12: 최소 프론트엔드 + 수동 E2E 검증

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/app.js`
- Modify: `app/api.py` (정적 파일 마운트 추가)

**Interfaces:**
- Consumes: `POST /session`, `POST /session/{id}/message`, `GET /session/{id}` (Task 11)
- Produces: 없음 (이 태스크가 파이프라인의 마지막 단계)

- [ ] **Step 1: `frontend/index.html` 작성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>아이디어 검증 에이전트</title>
</head>
<body>
  <div id="app">
    <h1>아이디어 검증 에이전트</h1>
    <div id="idea-form">
      <textarea id="idea-input" placeholder="아이디어를 입력하세요" rows="4" cols="50"></textarea>
      <br />
      <button id="start-btn">시작</button>
    </div>
    <div id="pipeline" style="display:none">
      <h2 id="stage-name"></h2>
      <pre id="stage-output"></pre>
      <div id="warning" style="color:red; white-space: pre-wrap;"></div>
      <input id="message-input" placeholder="추가 입력 (선택)" size="50" />
      <button id="advance-btn">다음 단계</button>
    </div>
  </div>
  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: `frontend/app.js` 작성**

```javascript
let sessionId = null;

document.getElementById("start-btn").addEventListener("click", async () => {
  const idea = document.getElementById("idea-input").value;
  const res = await fetch("/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
  });
  const data = await res.json();
  sessionId = data.session_id;
  document.getElementById("idea-form").style.display = "none";
  document.getElementById("pipeline").style.display = "block";
  await advance();
});

document.getElementById("advance-btn").addEventListener("click", advance);

async function advance() {
  const message = document.getElementById("message-input").value;
  const res = await fetch(`/session/${sessionId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await res.json();
  document.getElementById("message-input").value = "";

  if (data.status === "warning") {
    document.getElementById("warning").textContent =
      data.warning + "\n\n" + data.raw_text;
    return;
  }

  document.getElementById("warning").textContent = "";
  document.getElementById("stage-name").textContent = data.stage_name;
  document.getElementById("stage-output").textContent = JSON.stringify(
    data.output,
    null,
    2
  );

  if (data.complete) {
    document.getElementById("advance-btn").disabled = true;
    document.getElementById("stage-name").textContent += " (전체 완료)";
  }
}
```

- [ ] **Step 3: `app/api.py`에 정적 파일 마운트 추가** (파일 맨 아래에 추가)

```python
from fastapi.staticfiles import StaticFiles

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
```

이 마운트는 `app/api.py`의 라우트 정의(Task 11) *다음에* 와야 한다. 그렇지 않으면
`/`가 API 라우트보다 먼저 매칭되어 `/session` 등이 가려질 수 있다.

- [ ] **Step 4: 전체 자동화 테스트 재실행 (회귀 확인)**

Run: `pytest -v`
Expected: 이전 태스크에서 작성한 모든 테스트 PASS (Task 1~11 테스트 전부)

- [ ] **Step 5: 수동 E2E 검증**

```bash
source .venv/bin/activate
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

브라우저에서 `http://127.0.0.1:8000` 접속 후:
1. 아이디어를 입력하고 "시작" 클릭 → 실제 `claude` CLI가 호출되어 시장조사 단계
   결과(summary, market_size_claims, key_competitors)가 화면에 표시되는지 확인
2. "다음 단계"를 6번 클릭해 전체 파이프라인(시장조사→타겟층→가설수립→가설검증→
   MVP/MLP정의→BM가정)이 끝까지 진행되고 "(전체 완료)"가 표시되는지 확인
3. 각 단계 산출물에서 `source_tier`가 있는 claim들이 PRIMARY/SECONDARY일 때
   `source_url`이 채워져 있는지 육안 확인
4. `./data/sessions/<id>.json`을 열어 세션 상태가 올바르게 누적 저장되는지 확인

이 단계는 로컬 `claude` CLI 인증이 필요하므로 자동화 테스트에 포함하지 않는다.
문제가 발견되면 해당 stage 파일의 프롬프트나 스키마를 수정하고 Step 4로 돌아가
회귀 테스트를 다시 통과시킨다.

- [ ] **Step 6: 커밋**

```bash
git add frontend/ app/api.py
git commit -m "feat: add minimal frontend and static file serving"
```

---

## Plan Self-Review 결과

- **스펙 커버리지**: 아키텍처(Task 1,11,12) / Engine 추상화(Task 1) / 세션 상태(Task 2) /
  자가검증(Task 3, 각 stage에 통합) / 6단계 파이프라인(Task 4~9) / 오케스트레이터(Task 10) /
  에러 처리(Task 1의 예외, Task 4의 재시도+폴백) / 테스트 전략(각 Task의 단위테스트 +
  Task 12의 수동 E2E) — 스펙의 모든 섹션이 최소 하나의 태스크에 매핑됨.
- **플레이스홀더 스캔**: 모든 스텝에 실제 코드/명령어 포함, "TBD"/"이후 구현" 없음.
- **타입 일관성 확인**: `Engine.generate(prompt, history) -> EngineResponse`,
  `StageDefinition.build_prompt(idea, prior_outputs, user_message="")`,
  `run_stage(engine, stage, idea, prior_outputs, user_message="")`,
  `Orchestrator.advance(session, engine, user_message="")` — 모든 태스크에서
  동일한 시그니처로 일관되게 사용됨을 확인.
