import pytest
from pydantic import ValidationError

from app.stages.target_segment import TargetSegmentOutput, TargetSegmentStage


def test_build_prompt_includes_idea():
    stage = TargetSegmentStage()
    prompt = stage.build_prompt(idea="반려동물 산책 매칭 앱", prior_outputs={})
    assert "반려동물 산책 매칭 앱" in prompt
    assert "source_tier" in prompt


def test_build_prompt_includes_user_message_when_present():
    stage = TargetSegmentStage()
    prompt = stage.build_prompt(idea="x", prior_outputs={}, user_message="20대 위주로")
    assert "20대 위주로" in prompt


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
