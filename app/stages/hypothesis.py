import json
from enum import Enum

from pydantic import BaseModel

from app.stages.base import StageDefinition


class AssumptionType(str, Enum):
    DESIRABILITY = "desirability"
    VIABILITY = "viability"
    FEASIBILITY = "feasibility"


class Hypothesis(BaseModel):
    statement: str
    assumption_type: AssumptionType
    validation_method: str


class HypothesisOutput(BaseModel):
    hypotheses: list[Hypothesis]


class HypothesisStage(StageDefinition[HypothesisOutput]):
    name = "hypothesis"
    output_model = HypothesisOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        context = {
            "market_research": prior_outputs.get("market_research", {}),
            "target_segment": prior_outputs.get("target_segment", {}),
        }
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 린 캔버스 방식으로 검증 가능한 가설을 세우는 전문가입니다.

아이디어: {idea}

이전 단계 결과:
{json.dumps(context, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "hypotheses": [
    {{
      "statement": "검증 가능한 가설 문장 (string)",
      "assumption_type": "desirability|viability|feasibility",
      "validation_method": "이 가설을 검증하기 위해 필요한 구체적 방법 (설문/인터뷰/랜딩페이지 테스트 등)"
    }}
  ]
}}

규칙:
- 최소 3개, 최대 6개의 가설을 제시하세요.
- 각 가설은 반드시 desirability(고객이 원하는가), viability(사업으로 성립하는가), feasibility(만들 수 있는가) 중 하나로 분류하세요."""
