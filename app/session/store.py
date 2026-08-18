import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.session.models import SessionState


class SessionStore:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def create(self, idea: str) -> SessionState:
        now = datetime.now(timezone.utc)
        session = SessionState(id=str(uuid.uuid4()), idea=idea, created_at=now, updated_at=now)
        self.save(session)
        return session

    def save(self, session: SessionState) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self._path(session.id).write_text(session.model_dump_json(indent=2))

    def load(self, session_id: str) -> SessionState:
        path = self._path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"No session found with id {session_id}")
        return SessionState.model_validate_json(path.read_text())
