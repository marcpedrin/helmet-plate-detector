# Troubleshooting

Symptom → cause → fix. Owners append rows for their module (keep the table sorted by area).

| Area | Symptom | Likely cause | Fix |
|---|---|---|---|
| setup | `pip install` fails on `opencv-python` | Python not 3.12 / 32-bit Python | Install 64-bit Python 3.12, recreate the venv |
| setup | `ModuleNotFoundError: app` | uvicorn/pytest run outside `backend/` | `cd backend` first (the scripts do this) |
| camera | Feed shows "SYNTHETIC" | `videos/camera_0N.mp4` missing | Add the file (see `videos/README.md`); restart |
| api | Browser console shows CORS errors | Frontend origin not in `CORS_ORIGINS` | Add it to `.env`, comma-separated; restart |
| frontend | Dashboard empty, network errors to `:5173/api` | `VITE_API_BASE` unset and no dev proxy | `cp frontend/.env.example frontend/.env` |
| realtime | WS connects then nothing arrives | Backend in live mode with pipeline not implemented | Use `APP_MODE=mock` until `feature/pipeline` lands |
| models | `/api/health` shows `NOT_LOADED` | Weights not downloaded / ML deps not installed | `pip install -r backend/requirements-ml.txt && python scripts/download_models.py` |
| helmet | _TBD (Prajwal)_ | | |
| plates | _TBD (Malik)_ | | |
| storage | _TBD (camera/storage stream)_ | | |
