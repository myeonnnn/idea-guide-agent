import json
import subprocess
from unittest.mock import patch

import pytest

from app.engine.base import EngineParseError, EngineProcessError, EngineTimeoutError
from app.engine.claude_cli import ClaudeCodeCLIEngine


def _completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_generate_returns_text_from_result_field():
    engine = ClaudeCodeCLIEngine()
    payload = {"type": "result", "result": "hello world", "session_id": "abc"}
    with patch("subprocess.run", return_value=_completed(stdout=json.dumps(payload))):
        response = engine.generate("hi", history=[])
    assert response["text"] == "hello world"
    assert response["raw"] == payload


def test_generate_raises_timeout_error():
    engine = ClaudeCodeCLIEngine(timeout_seconds=5)
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5)):
        with pytest.raises(EngineTimeoutError):
            engine.generate("hi", history=[])


def test_generate_raises_process_error_when_binary_missing():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(EngineProcessError):
            engine.generate("hi", history=[])


def test_generate_raises_process_error_on_nonzero_exit():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", return_value=_completed(stderr="boom", returncode=1)):
        with pytest.raises(EngineProcessError) as exc_info:
            engine.generate("hi", history=[])
    assert exc_info.value.stderr == "boom"


def test_generate_raises_parse_error_on_invalid_json():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", return_value=_completed(stdout="not json")):
        with pytest.raises(EngineParseError):
            engine.generate("hi", history=[])


def test_generate_raises_parse_error_when_result_field_missing():
    engine = ClaudeCodeCLIEngine()
    with patch("subprocess.run", return_value=_completed(stdout=json.dumps({"type": "result"}))):
        with pytest.raises(EngineParseError):
            engine.generate("hi", history=[])
