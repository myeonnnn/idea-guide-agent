import pytest
from pydantic import ValidationError

from app.stages.value_proposition import ValuePropositionOutput, ValuePropositionStage


def test_build_prompt_includes_prior_context():
    stage = ValuePropositionStage()
    prior = {
        "target_segment": {"pain_points": ["시간 부족"]},
        "market_research": {"key_competitors": ["도그메이트"]},
    }
    prompt = stage.build_prompt(idea="반려동물 산책 매칭 앱", prior_outputs=prior)
    assert "반려동물 산책 매칭 앱" in prompt
    assert "시간 부족" in prompt
    assert "도그메이트" in prompt
    assert "unfair_advantage" in prompt


def test_output_model_valid():
    output = ValuePropositionOutput(
        statement="가장 빠르게 신뢰할 수 있는 산책 대행자를 매칭",
        differentiators=["실시간 GPS 공유", "신원 인증"],
        unfair_advantage="뚜렷한 진입장벽 없음 — 실행 속도로 승부해야 함",
        claims=[{"text": "추정", "source_tier": "ESTIMATE", "source_url": None}],
    )
    assert output.statement.startswith("가장 빠르게")


def test_output_model_rejects_primary_claim_without_url():
    with pytest.raises(ValidationError):
        ValuePropositionOutput(
            statement="x",
            differentiators=[],
            unfair_advantage="x",
            claims=[{"text": "주장", "source_tier": "PRIMARY", "source_url": None}],
        )
