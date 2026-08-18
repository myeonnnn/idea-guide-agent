import json
from enum import Enum

from pydantic import BaseModel

from app.stages.base import StageDefinition


class VerdictType(str, Enum):
    PROCEED = "proceed"
    PIVOT = "pivot"
    KILL = "kill"


class FinalVerdictOutput(BaseModel):
    verdict: VerdictType
    reasoning: str
    key_unvalidated_assumptions: list[str]
    evidence_quality_summary: str


class FinalVerdictStage(StageDefinition[FinalVerdictOutput]):
    name = "final_verdict"
    output_model = FinalVerdictOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 지금까지의 검증 결과를 종합해 냉정하게 판단하는 심사역입니다.
"모르는 것보다 잘못된 정보를 주는 것이 더 나쁘다"는 원칙에 따라, 근거가 부족하면
솔직하게 지적하세요. 응원하는 게 아니라 판단하는 게 당신의 역할입니다.

아이디어: {idea}

지금까지의 전체 검증 결과:
{json.dumps(prior_outputs, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "verdict": "proceed|pivot|kill",
  "reasoning": "이 판단을 내린 구체적인 근거 (string)",
  "key_unvalidated_assumptions": ["이 판단이 의존하고 있는, 아직 검증되지 않은 핵심 가정", "..."],
  "evidence_quality_summary": "전체 근거 중 PRIMARY/SECONDARY/ESTIMATE 비율과 그 의미를 요약 (string)"
}}

규칙:
- proceed: 핵심 리스크(riskiest_assumption)에 대한 근거가 충분하고 진행해도 좋은 경우.
- pivot: 현재 방향의 핵심 가정 중 일부가 흔들리지만, 방향을 바꾸면 가능성이 있는 경우.
- kill: 여러 핵심 가정이 동시에 근거 부족이거나 서로 모순되어 이 형태로는 진행하기 어려운 경우.
- 근거 대부분이 ESTIMATE(AI 추정)라면 proceed를 함부로 주지 마세요."""
