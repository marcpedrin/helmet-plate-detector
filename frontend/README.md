# Frontend (skeleton)

Owner: **Harish**. Vite + React + TypeScript + Tailwind v4 + shadcn/ui (dark, neutral).

```bash
npm install && cp .env.example .env   # VITE_API_BASE=http://localhost:8000 (or empty to use the dev proxy)
npm run dev        # http://localhost:5173 (backend on :8000, APP_MODE=mock works)
npm run lint && npm run typecheck && npm test && npm run build
```

- `src/types/contracts.ts`: **contract**, mirrors `backend/app/core/schemas.py` (Marc only, via contracts PRs).
- `src/services/api.ts` (REST), `src/services/ws.ts` (/ws/events + backoff), `src/hooks/useLiveEvents.ts` (context).
- `src/pages/*`: deliberately plain placeholders. The real UI is Harish's job. Docs: `docs/modules/frontend.md`.
