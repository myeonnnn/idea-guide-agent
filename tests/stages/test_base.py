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


def test_run_stage_strips_markdown_code_fence_before_parsing():
    engine = FakeEngine(['```json\n{"value": "ok"}\n```'])
    result = run_stage(engine, DummyStage(), idea="x", prior_outputs={})
    assert result.output == DummyOutput(value="ok")
    assert result.warning is None
    assert len(engine.calls) == 1


def test_run_stage_strips_code_fence_without_language_tag():
    engine = FakeEngine(['```\n{"value": "ok"}\n```'])
    result = run_stage(engine, DummyStage(), idea="x", prior_outputs={})
    assert result.output == DummyOutput(value="ok")


def test_run_stage_extracts_fenced_json_with_surrounding_prose():
    engine = FakeEngine(
        ['```json\n{"value": "ok"}\n```\n\n**참고**: 이 항목은 추정치입니다.']
    )
    result = run_stage(engine, DummyStage(), idea="x", prior_outputs={})
    assert result.output == DummyOutput(value="ok")
