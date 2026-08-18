import json

from pydantic import BaseModel, model_validator

from app.stages.base import StageDefinition
from app.verification.checks import validate_claims
from app.verification.models import Claim


class ValuePropositionOutput(BaseModel):
    statement: str
    differentiators: list[str]
    unfair_advantage: str
    claims: list[Claim]

    @model_validator(mode="after")
    def _check_claims(self):
        errors = validate_claims(self.claims)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class ValuePropositionStage(StageDefinition[ValuePropositionOutput]):
    name = "value_proposition"
    output_model = ValuePropositionOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        context = {
            "target_segment": prior_outputs.get("target_segment", {}),
            "market_research": prior_outputs.get("market_research", {}),
        }
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 가치제안과 차별화 우위를 정의하는 전략 컨설턴트입니다.

아이디어: {idea}

이전 단계 결과:
{json.dumps(context, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "statement": "타겟 고객에게 왜 이 제품을 써야 하는지 한두 문장으로 (string)",
  "differentiators": ["기존 대안 대비 구체적으로 다른 점", "..."],
  "unfair_advantage": "경쟁자가 쉽게 베끼지 못하는 진입장벽. 뚜렷한 게 없다면 솔직하게 '없음'과 그 이유를 적으세요 (string)",
  "claims": [
    {{"text": "주장 내용", "source_tier": "PRIMARY|SECONDARY|ESTIMATE", "source_url": "출처 URL 또는 null"}}
  ]
}}

규칙:
- unfair_advantage는 미화하지 마세요. 브랜드, 네트워크 효과, 독점 데이터, 규제 라이선스처럼 진짜 진입장벽이 없다면 없다고 명시하세요.
- claims의 각 항목은 반드시 source_tier를 PRIMARY, SECONDARY, ESTIMATE 중 하나로 라벨링하세요.
- PRIMARY 또는 SECONDARY 라벨인 경우 source_url을 반드시 포함하세요."""
