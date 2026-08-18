# frontend

Vite + React + TypeScript UI for the 아이디어 검증 에이전트. See the [project root README](../README.md) for what this tool does.

## Development

```bash
npm install
npm run dev
```

Requests to `/session*` are proxied to the FastAPI backend at `http://127.0.0.1:8000` (see `vite.config.ts`) — run the backend separately (`.venv/bin/uvicorn app.api:app --port 8000` from the project root).

## Production build

```bash
npm run build
```

Outputs to `dist/`, which the FastAPI backend serves directly (`app/api.py` mounts `frontend/dist`).
