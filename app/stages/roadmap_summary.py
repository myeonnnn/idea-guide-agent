import json

from pydantic import BaseModel

from app.stages.base import StageDefinition


class RoadmapSummaryOutput(BaseModel):
    summary: str
    key_next_actions: list[str]
    still_unverified: list[str]
    evidence_quality_summary: str


class RoadmapSummaryStage(StageDefinition[RoadmapSummaryOutput]):
    name = "roadmap_summary"
    output_model = RoadmapSummaryOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 지금까지의 검증 결과 7단계를 하나의 로드맵으로 정리하는
전략 컨설턴트입니다. 이 아이디어를 만들지 말지 판단하는 것이 아니라, 지금까지
나온 내용을 종합해 다음에 무엇을 하면 되는지 정리하는 것이 목표입니다.

아이디어: {idea}

지금까지의 전체 단계 결과:
{json.dumps(prior_outputs, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "summary": "타겟층, 시장, 가치제안, 가설, MVP, 비즈니스모델을 하나로 엮은 로드맵 요약 (string)",
  "key_next_actions": ["우선순위 순으로 정리한 다음 실행 항목", "..."],
  "still_unverified": ["아직 검증되지 않은 핵심 가정", "..."],
  "evidence_quality_summary": "전체 근거 중 PRIMARY/SECONDARY/ESTIMATE 비율과 그 의미를 요약 (string)"
}}

규칙:
- "진행해야 한다/하지 말아야 한다" 같은 판단이나 권고는 하지 마세요. 있는 그대로 요약하고 정리하세요.
- key_next_actions는 riskiest_assumption(가장 위험한 가정)을 검증하는 항목을 최우선으로 배치하세요.
- still_unverified는 hypothesis_validation과 각 단계의 claims 중 ESTIMATE로 남아있는 것들을 반영하세요."""
