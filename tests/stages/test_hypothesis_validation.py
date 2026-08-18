from app.stages.hypothesis_validation import HypothesisValidationOutput, HypothesisValidationStage


def test_build_prompt_includes_prior_hypotheses():
    stage = HypothesisValidationStage()
    prior = {"hypothesis": {"hypotheses": [{"statement": "월 3만원 지불 의향"}]}}
    prompt = stage.build_prompt(idea="x", prior_outputs=prior)
    assert "월 3만원 지불 의향" in prompt
    assert "risk_rank" in prompt
    assert "riskiest_assumption" in prompt


def test_output_model_valid():
    output = HypothesisValidationOutput(
        validations=[
            {
                "hypothesis_statement": "월 3만원 지불 의향",
                "validation_plan": "랜딩페이지 스모크테스트",
                "required_evidence": "전환율 5% 이상",
                "confidence": "medium",
                "risk_rank": 1,
            }
        ],
        riskiest_assumption="월 3만원 지불 의향",
        riskiest_assumption_reasoning="이게 틀리면 사업 전체가 성립하지 않음",
    )
    assert output.validations[0].confidence == "medium"
    assert output.validations[0].risk_rank == 1
    assert output.riskiest_assumption == "월 3만원 지불 의향"
