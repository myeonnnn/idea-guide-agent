from datetime import datetime, timezone

from pydantic import BaseModel

from app.orchestrator import PIPELINE, Orchestrator
from app.session.models import SessionState
from app.stages.base import StageDefinition


class StubOutput(BaseModel):
    stage: str


def make_stage(stage_name: str):
    class StubStage(StageDefinition[StubOutput]):
        name = stage_name
        output_model = StubOutput

        def build_prompt(self, idea, prior_outputs, user_message=""):
            return f"prompt for {stage_name}"

    return StubStage()


class FakeEngine:
    def __init__(self, texts):
        self.texts = list(texts)

    def generate(self, prompt, history):
        return {"text": self.texts.pop(0), "raw": {}}


def make_session():
    now = datetime.now(timezone.utc)
    return SessionState(id="s1", idea="아이디어", created_at=now, updated_at=now)


def test_advance_runs_current_stage_and_increments_index():
    stage_a = make_stage("stage_a")
    stage_b = make_stage("stage_b")
    orchestrator = Orchestrator(stages=[stage_a, stage_b])
    engine = FakeEngine(['{"stage": "a"}'])
    session = make_session()

    result = orchestrator.advance(session, engine)

    assert result.output == StubOutput(stage="a")
    assert session.stage_index == 1
    assert session.stage_outputs["stage_a"] == {"stage": "a"}


def test_advance_does_not_increment_index_on_failure():
    stage_a = make_stage("stage_a")
    orchestrator = Orchestrator(stages=[stage_a])
    engine = FakeEngine(["not json", "still not json"])
    session = make_session()

    result = orchestrator.advance(session, engine)

    assert result.output is None
    assert session.stage_index == 0
    assert session.stage_outputs == {}


def test_is_complete_after_all_stages_run():
    stage_a = make_stage("stage_a")
    orchestrator = Orchestrator(stages=[stage_a])
    engine = FakeEngine(['{"stage": "a"}'])
    session = make_session()

    assert orchestrator.is_complete(session) is False
    orchestrator.advance(session, engine)
    assert orchestrator.is_complete(session) is True


def test_current_stage_name_returns_expected_stage():
    stage_a = make_stage("stage_a")
    stage_b = make_stage("stage_b")
    orchestrator = Orchestrator(stages=[stage_a, stage_b])
    session = make_session()
    session.stage_index = 1

    assert orchestrator.current_stage_name(session) == "stage_b"


def test_pipeline_has_expected_stage_order():
    assert [stage.name for stage in PIPELINE] == [
        "target_segment",
        "market_research",
        "value_proposition",
        "hypothesis",
        "hypothesis_validation",
        "mvp_mlp",
        "business_model",
        "final_verdict",
    ]
