import json

from pydantic import BaseModel, model_validator

from app.stages.base import StageDefinition
from app.verification.checks import validate_claims
from app.verification.models import Claim


class MarketResearchOutput(BaseModel):
    summary: str
    market_size_claims: list[Claim]
    key_competitors: list[str]

    @model_validator(mode="after")
    def _check_claims(self):
        errors = validate_claims(self.market_size_claims)
        if errors:
            raise ValueError("; ".join(errors))
        return self


class MarketResearchStage(StageDefinition[MarketResearchOutput]):
    name = "market_research"
    output_model = MarketResearchOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        target_segment = prior_outputs.get("target_segment", {})
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 스타트업 아이디어의 시장을 조사하는 애널리스트입니다. 아래 타겟층을
중심으로 시장 규모와 경쟁 구도를 조사하세요 (일반적인 전체 산업 통계가 아니라, 이
타겟층에 해당하는 부분에 집중).

아이디어: {idea}

이전 단계(타겟층 설정) 결과:
{json.dumps(target_segment, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "summary": "시장 개요 요약 (string)",
  "market_size_claims": [
    {{"text": "주장 내용", "source_tier": "PRIMARY|SECONDARY|ESTIMATE", "source_url": "출처 URL 또는 null"}}
  ],
  "key_competitors": ["경쟁사 이름", "..."]
}}

규칙:
- market_size_claims의 각 항목은 반드시 source_tier를 PRIMARY(1차 공식 통계/학술자료), SECONDARY(2차 해석/뉴스기사), ESTIMATE(AI 추정치) 중 하나로 라벨링하세요.
- PRIMARY 또는 SECONDARY 라벨인 경우 source_url을 반드시 포함하세요.
- 확실하지 않은 수치는 ESTIMATE로 명확히 표시하세요."""
