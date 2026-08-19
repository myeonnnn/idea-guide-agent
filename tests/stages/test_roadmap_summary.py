from app.stages.roadmap_summary import RoadmapSummaryOutput, RoadmapSummaryStage


def test_build_prompt_includes_all_prior_stages():
    stage = RoadmapSummaryStage()
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
    assert "verdict" not in prompt
    assert "심사역" not in prompt
    assert "proceed" not in prompt and "pivot" not in prompt and "kill" not in prompt


def test_output_model_valid():
    output = RoadmapSummaryOutput(
        summary="1인 가구 반려인을 위한 신뢰 기반 산책 대행 서비스 로드맵",
        key_next_actions=["타겟 세그먼트 대상 심층 인터뷰 10~15명 진행"],
        still_unverified=["월 3만원 지불 의향"],
        evidence_quality_summary="전체 12개 근거 중 9개가 AI 추정치",
    )
    assert output.summary.startswith("1인 가구")
    assert len(output.key_next_actions) == 1
