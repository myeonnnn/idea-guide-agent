from pydantic import BaseModel, model_validator

from app.stages.base import StageDefinition
from app.verification.checks import validate_claims
from app.verification.models import Claim


class TargetSegmentOutput(BaseModel):
    primary_segment: str
    segment_description: str
    pain_points: list[str]
    claims: list[Claim]

    @model_validator(mode="after")
    def _check_claims(self):
        errors = validate_claims(self.claims)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class TargetSegmentStage(StageDefinition[TargetSegmentOutput]):
    name = "target_segment"
    output_model = TargetSegmentOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 스타트업의 타겟 고객층을 분석하는 전략 컨설턴트입니다. 시장 통계보다
먼저 "누가 어떤 문제를 겪고 있는가"를 명확히 하는 것이 목적입니다.

아이디어: {idea}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "primary_segment": "주 타겟 고객층 이름 (string)",
  "segment_description": "타겟층 설명 (string)",
  "pain_points": ["핵심 페인포인트", "..."],
  "claims": [
    {{"text": "주장 내용", "source_tier": "PRIMARY|SECONDARY|ESTIMATE", "source_url": "출처 URL 또는 null"}}
  ]
}}

규칙:
- claims의 각 항목은 반드시 source_tier를 PRIMARY, SECONDARY, ESTIMATE 중 하나로 라벨링하세요.
- PRIMARY 또는 SECONDARY 라벨인 경우 source_url을 반드시 포함하세요."""
