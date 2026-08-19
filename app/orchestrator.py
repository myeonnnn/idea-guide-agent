from app.engine.base import Engine
from app.session.models import SessionState
from app.stages.base import StageDefinition, StageResult, run_stage
from app.stages.business_model import BusinessModelStage
from app.stages.hypothesis import HypothesisStage
from app.stages.hypothesis_validation import HypothesisValidationStage
from app.stages.market_research import MarketResearchStage
from app.stages.mvp_mlp import MvpMlpStage
from app.stages.roadmap_summary import RoadmapSummaryStage
from app.stages.target_segment import TargetSegmentStage
from app.stages.value_proposition import ValuePropositionStage

PIPELINE: list[StageDefinition] = [
    TargetSegmentStage(),
    MarketResearchStage(),
    ValuePropositionStage(),
    HypothesisStage(),
    HypothesisValidationStage(),
    MvpMlpStage(),
    BusinessModelStage(),
    RoadmapSummaryStage(),
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
