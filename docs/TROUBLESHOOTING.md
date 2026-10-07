# Troubleshooting

Symptom → cause → fix. Owners append rows for their module (keep the table sorted by area).

| Area | Symptom | Likely cause | Fix |
|---|---|---|---|
| setup | `pip install` fails on `opencv-python` | Python not 3.12 / 32-bit Python | Install 64-bit Python 3.12, recreate the venv |
| setup | `ModuleNotFoundError: app` | uvicorn/pytest run outside `backend/` | `cd backend` first (the scripts do this) |
| camera | Feed shows "SYNTHETIC" | `videos/camera_0N.mp4` missing | Add the file (see `videos/README.md`); restart |
| api | Browser console shows CORS errors | Frontend origin not in `CORS_ORIGINS` | Add it to `.env`, comma-separated; restart |
| frontend | Dashboard empty, network errors to `:5173/api` | `VITE_API_BASE` unset and no dev proxy | `cp frontend/.env.example frontend/.env` |
| realtime | WS connects but no violations arrive (live) | helmet model NOT_LOADED, so riders are never NO_HELMET | check `/api/health`; use `APP_MODE=mock` for UI work |
| models | `/api/health` shows `NOT_LOADED` | Weights not downloaded / ML deps not installed | `pip install -r backend/requirements-ml.txt && python scripts/download_models.py` |
| pipeline | 4 cameras at ~2 FPS each on a laptop CPU | CPU saturates at ~7 YOLO inferences/s | GPU, or `DETECTOR_IMGSZ=512` + 2-3 cameras (pipeline.md §9) |
| pipeline | torch `not enough memory` / OpenCV `Insufficient memory` | Windows commit charge exhausted by other apps | close IDE language servers, browsers, chat apps; ~1.5 GB needed for 4 trackers |
| pipeline | Live mode: no violations ever | helmet `NOT_LOADED` → all riders UNKNOWN | download helmet weights (Prajwal's module) |
| api | `/violations/x` 404 on refresh | `frontend/dist` missing | `npm run build`; restart backend (SPA fallback serves index.html) |
| helmet | _TBD (Prajwal)_ | | |
| plates | _TBD (Malik)_ | | |
| storage | _TBD (camera/storage stream)_ | | |
