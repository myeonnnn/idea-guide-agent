# frontend

Vite + React + TypeScript UI for the 아이디어 검증 에이전트. See the [project root README](../README.md) for what this tool does.

This is hosted completely separately from the FastAPI backend — they communicate over CORS, not through a shared process or a static-file mount.

## Development

```bash
npm install
npm run dev
```

Runs on `http://localhost:5173`. Talks to the backend at `http://127.0.0.1:8000` by default; override with a `VITE_API_BASE_URL` env var if the backend runs elsewhere. Run the backend separately (`.venv/bin/uvicorn app.api:app --port 8000` from the project root).

## Production build

```bash
npm run build
```

Outputs to `dist/`. Serve it with any static file host — the backend no longer mounts or serves this directory.
