import pytest
from pydantic import ValidationError

from app.stages.final_verdict import FinalVerdictOutput, FinalVerdictStage


def test_build_prompt_includes_all_prior_stages():
    stage = FinalVerdictStage()
    prior = {
        "target_segment": {"primary_segment": "1인 가구"},
        "market_research": {"summary": "성장 중"},
        "value_proposition": {"statement": "빠른 매칭"},
        "hypothesis": {"hypotheses": []},
        "hypothesis_validation": {"riskiest_assumption": "지불 의향"},
        "mvp_mlp": {"mvp_scope": ["수동 매칭"]},
        "business_model": {"revenue_model": "구독형"},
    }
    prompt = stage.build_prompt(idea="반려동물 산책 매칭 앱", prior_outputs=prior)
    assert "반려동물 산책 매칭 앱" in prompt
    assert "1인 가구" in prompt
    assert "지불 의향" in prompt
    assert "구독형" in prompt
    assert "proceed" in prompt and "pivot" in prompt and "kill" in prompt


def test_output_model_valid():
    output = FinalVerdictOutput(
        verdict="pivot",
        reasoning="지불 의향 가설이 미검증 상태이고 근거 대부분이 추정치임",
        key_unvalidated_assumptions=["월 3만원 지불 의향"],
        evidence_quality_summary="전체 12개 근거 중 9개가 AI 추정치",
    )
    assert output.verdict == "pivot"


def test_output_model_rejects_invalid_verdict():
    with pytest.raises(ValidationError):
        FinalVerdictOutput(
            verdict="maybe",
            reasoning="x",
            key_unvalidated_assumptions=[],
            evidence_quality_summary="x",
        )
