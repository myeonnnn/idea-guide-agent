import json

from pydantic import BaseModel

from app.stages.base import StageDefinition


class MvpMlpOutput(BaseModel):
    mvp_scope: list[str]
    mlp_scope: list[str]
    success_metrics: list[str]


class MvpMlpStage(StageDefinition[MvpMlpOutput]):
    name = "mvp_mlp"
    output_model = MvpMlpOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        context = {
            "target_segment": prior_outputs.get("target_segment", {}),
            "hypothesis": prior_outputs.get("hypothesis", {}),
            "hypothesis_validation": prior_outputs.get("hypothesis_validation", {}),
        }
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 MVP와 MLP 범위를 정의하는 프로덕트 전략가입니다.

아이디어: {idea}

이전 단계 결과:
{json.dumps(context, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "mvp_scope": ["MVP에 포함할 최소 기능", "..."],
  "mlp_scope": ["MLP(Minimum Lovable Product)에 포함할 기능", "..."],
  "success_metrics": ["이 단계 성공을 판단할 지표", "..."]
}}

규칙:
- mvp_scope는 가설 검증에 필요한 최소한의 기능만 포함하세요.
- success_metrics는 측정 가능한 형태로 작성하세요."""
