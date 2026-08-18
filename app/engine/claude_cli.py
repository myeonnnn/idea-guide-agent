import json
import subprocess

from app.engine.base import (
    EngineParseError,
    EngineProcessError,
    EngineResponse,
    EngineTimeoutError,
    Message,
)


class ClaudeCodeCLIEngine:
    def __init__(self, timeout_seconds: int = 120, claude_bin: str = "claude"):
        self.timeout_seconds = timeout_seconds
        self.claude_bin = claude_bin

    def generate(self, prompt: str, history: list[Message]) -> EngineResponse:
        try:
            result = subprocess.run(
                [self.claude_bin, "-p", prompt, "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise EngineTimeoutError(
                f"claude CLI timed out after {self.timeout_seconds}s"
            ) from exc
        except FileNotFoundError as exc:
            raise EngineProcessError(
                f"'{self.claude_bin}' executable not found on PATH"
            ) from exc

        if result.returncode != 0:
            raise EngineProcessError(
                f"claude CLI exited with code {result.returncode}",
                stderr=result.stderr,
                returncode=result.returncode,
            )

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise EngineParseError(
                f"claude CLI returned non-JSON output: {exc}", raw_output=result.stdout
            ) from exc

        text = payload.get("result")
        if not text:
            raise EngineParseError(
                "claude CLI JSON output missing 'result' field", raw_output=result.stdout
            )

        return EngineResponse(text=text, raw=payload)
