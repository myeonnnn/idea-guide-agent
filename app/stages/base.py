import json
import re
from dataclasses import dataclass
from typing import Generic, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.engine.base import Engine

T = TypeVar("T", bound=BaseModel)

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*)\n```\s*$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text


@dataclass
class StageResult(Generic[T]):
    output: T | None
    warning: str | None = None
    raw_text: str | None = None


class StageDefinition(Generic[T]):
    name: str
    output_model: Type[T]

    def build_prompt(self, idea: str, prior_outputs: dict[str, dict], user_message: str = "") -> str:
        raise NotImplementedError


def _parse_and_validate(stage: StageDefinition[T], text: str) -> tuple[T | None, str | None]:
    try:
        data = json.loads(_strip_code_fence(text))
    except json.JSONDecodeError as exc:
        return None, f"JSON 파싱 실패: {exc}"
    try:
        return stage.output_model.model_validate(data), None
    except ValidationError as exc:
        return None, f"스키마 검증 실패: {exc}"


def run_stage(
    engine: Engine,
    stage: StageDefinition[T],
    idea: str,
    prior_outputs: dict[str, dict],
    user_message: str = "",
) -> StageResult[T]:
    prompt = stage.build_prompt(idea, prior_outputs, user_message)
    response = engine.generate(prompt, history=[])
    output, warning = _parse_and_validate(stage, response["text"])

    if output is None:
        retry_prompt = (
            prompt
            + "\n\n이전 응답이 유효하지 않았습니다. 반드시 위에서 요구한 JSON 스키마와 "
            "정확히 일치하는, 유효한 JSON 객체 하나만 응답하세요. 다른 텍스트를 포함하지 마세요."
        )
        response = engine.generate(retry_prompt, history=[])
        output, warning = _parse_and_validate(stage, response["text"])

    if output is None:
        return StageResult(output=None, warning=warning, raw_text=response["text"])

    return StageResult(output=output, warning=None)
