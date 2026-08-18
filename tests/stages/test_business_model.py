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
