import json

from pydantic import BaseModel, model_validator

from app.stages.base import StageDefinition
from app.verification.checks import validate_claims
from app.verification.models import Claim


class BusinessModelOutput(BaseModel):
    revenue_model: str
    channels: list[str]
    cost_structure: list[str]
    claims: list[Claim]

    @model_validator(mode="after")
    def _check_claims(self):
        errors = validate_claims(self.claims)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class BusinessModelStage(StageDefinition[BusinessModelOutput]):
    name = "business_model"
    output_model = BusinessModelOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        context = {
            "target_segment": prior_outputs.get("target_segment", {}),
            "mvp_mlp": prior_outputs.get("mvp_mlp", {}),
        }
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 비즈니스 모델을 구조화하는 전략 컨설턴트입니다.

아이디어: {idea}

이전 단계 결과:
{json.dumps(context, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "revenue_model": "수익모델 설명 (string)",
  "channels": ["유통/마케팅 채널", "..."],
  "cost_structure": ["주요 비용 항목", "..."],
  "claims": [
    {{"text": "주장 내용", "source_tier": "PRIMARY|SECONDARY|ESTIMATE", "source_url": "출처 URL 또는 null"}}
  ]
}}

규칙:
- claims의 각 항목은 반드시 source_tier를 PRIMARY, SECONDARY, ESTIMATE 중 하나로 라벨링하세요.
- PRIMARY 또는 SECONDARY 라벨인 경우 source_url을 반드시 포함하세요."""
