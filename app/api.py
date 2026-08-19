from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.engine.base import EngineError
from app.engine.claude_cli import ClaudeCodeCLIEngine
from app.orchestrator import PIPELINE, Orchestrator
from app.session.store import SessionStore

# Frontend is hosted separately (Vite dev server on localhost during
# development); this API only ever runs on 127.0.0.1, so a fixed
# localhost allowlist is fine rather than a wildcard origin.
DEV_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = SessionStore(base_dir=Path("./data/sessions"))
engine = ClaudeCodeCLIEngine()
orchestrator = Orchestrator(PIPELINE)


class CreateSessionRequest(BaseModel):
    idea: str


class MessageRequest(BaseModel):
    message: str = ""


@app.post("/session")
def create_session(req: CreateSessionRequest):
    session = store.create(idea=req.idea)
    return {"session_id": session.id, "stage_index": session.stage_index}


@app.post("/session/{session_id}/message")
def send_message(session_id: str, req: MessageRequest):
    try:
        session = store.load(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session not found")

    if orchestrator.is_complete(session):
        raise HTTPException(status_code=400, detail="pipeline already complete")

    stage_name = orchestrator.current_stage_name(session)
    try:
        result = orchestrator.advance(session, engine, user_message=req.message)
    except EngineError as exc:
        return {
            "status": "warning",
            "warning": str(exc),
            "raw_text": getattr(exc, "raw_output", "") or getattr(exc, "stderr", ""),
            "stage_index": session.stage_index,
        }

    if result.output is None:
        return {
            "status": "warning",
            "warning": result.warning,
            "raw_text": result.raw_text,
            "stage_index": session.stage_index,
        }

    store.save(session)
    return {
        "status": "ok",
        "stage_name": stage_name,
        "output": result.output.model_dump(mode="json"),
        "stage_index": session.stage_index,
        "complete": orchestrator.is_complete(session),
    }


@app.get("/session/{session_id}")
def get_session(session_id: str):
    try:
        session = store.load(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session not found")
    return session.model_dump(mode="json")
