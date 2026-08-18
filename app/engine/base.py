from typing import Literal, Protocol, TypedDict


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class EngineResponse(TypedDict):
    text: str
    raw: dict


class EngineError(Exception):
    """Base class for all engine failures."""


class EngineTimeoutError(EngineError):
    pass


class EngineProcessError(EngineError):
    def __init__(self, message: str, stderr: str = "", returncode: int | None = None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


class EngineParseError(EngineError):
    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


class Engine(Protocol):
    def generate(self, prompt: str, history: list[Message]) -> EngineResponse: ...
