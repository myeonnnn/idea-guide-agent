import pytest
from pydantic import ValidationError

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
    with pytest.raises(ValidationError):
        MarketResearchOutput(
            summary="요약",
            market_size_claims=[{"text": "주장", "source_tier": "PRIMARY", "source_url": None}],
            key_competitors=[],
        )
