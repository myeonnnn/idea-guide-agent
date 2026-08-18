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
