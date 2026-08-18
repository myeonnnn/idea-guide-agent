import json
from enum import Enum

from pydantic import BaseModel

from app.stages.base import StageDefinition


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HypothesisValidationItem(BaseModel):
    hypothesis_statement: str
    validation_plan: str
    required_evidence: str
    confidence: ConfidenceLevel
    risk_rank: int


class HypothesisValidationOutput(BaseModel):
    validations: list[HypothesisValidationItem]
    riskiest_assumption: str
    riskiest_assumption_reasoning: str


class HypothesisValidationStage(StageDefinition[HypothesisValidationOutput]):
    name = "hypothesis_validation"
    output_model = HypothesisValidationOutput

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        hypothesis_output = prior_outputs.get("hypothesis", {})
        extra = f"\n\n사용자 추가 입력: {user_message}" if user_message.strip() else ""
        return f"""당신은 가설 검증 계획을 구체화하고, 가장 먼저 검증해야 할 리스크를
가려내는 전문가입니다 (Riskiest Assumption Test 방식 — 모든 가설을 동등하게
다루지 말고, 이게 틀리면 사업 전체가 무너지는 가정을 우선순위로 삼으세요).

아이디어: {idea}

이전 단계(가설 수립) 결과:
{json.dumps(hypothesis_output, ensure_ascii=False, indent=2)}
{extra}

다음 JSON 스키마와 정확히 일치하는 JSON 객체 하나만 응답하세요. 다른 설명 텍스트는 포함하지 마세요.

{{
  "validations": [
    {{
      "hypothesis_statement": "위 가설 문장을 그대로 복사",
      "validation_plan": "이 가설을 검증할 구체적 실행 계획",
      "required_evidence": "가설이 참이라고 판단하기 위해 필요한 증거/기준",
      "confidence": "low|medium|high",
      "risk_rank": "1이 가장 위험/시급, 숫자가 클수록 덜 시급 (정수)"
    }}
  ],
  "riskiest_assumption": "risk_rank가 1인 가설 문장을 그대로 복사",
  "riskiest_assumption_reasoning": "왜 이 가설이 가장 먼저 검증해야 할 리스크인지"
}}

규칙:
- 이전 단계의 모든 가설에 대해 하나씩 검증 계획을 작성하세요.
- confidence는 현재 시점에서 이 가설이 참일 것이라는 확신도를 나타냅니다.
- risk_rank는 1부터 시작해 가설 개수만큼 중복 없이 매기세요. 1번이 가장 위험한(틀리면 사업이 무너지는) 가정입니다."""
