from app.stages.mvp_mlp import MvpMlpOutput, MvpMlpStage


def test_build_prompt_includes_prior_context():
    stage = MvpMlpStage()
    prior = {"hypothesis_validation": {"validations": [{"confidence": "high"}]}}
    prompt = stage.build_prompt(idea="x", prior_outputs=prior)
    assert "high" in prompt


def test_output_model_valid():
    output = MvpMlpOutput(
        mvp_scope=["매칭 알고리즘 없이 수동 매칭"],
        mlp_scope=["자동 매칭", "결제"],
        success_metrics=["첫 주 매칭 성사율 30%"],
    )
    assert len(output.mvp_scope) == 1
