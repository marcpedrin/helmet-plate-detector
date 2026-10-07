# Runbook

Owner: Marc. Skeleton: owners add entries as they learn how their module fails.

## Start / stop

| | Windows PowerShell | bash |
|---|---|---|
| Backend | `scripts\run_backend.ps1` | `scripts/run_backend.sh` |
| Frontend | `scripts\run_frontend.ps1` | `scripts/run_frontend.sh` |
| Smoke test | `python scripts/smoke_test.py` | same |

Stop with `Ctrl+C`. Shutdown stops runner threads, then camera threads.

## Demo-day commands

```powershell
cd D:\Helmet-Plate-Detector\helmet-plate-detector
git checkout demo-v1                               # code freeze tag (after Phase 3)
cd frontend; npm ci; npm run build; cd ..          # FastAPI then serves the UI at :8000
# .env: APP_MODE=live; on CPU also PIPELINE_FPS=3, DETECTOR_IMGSZ=512, STREAM_FPS=10
backend\.venv\Scripts\python scripts\download_models.py
scripts\run_backend.ps1                            # no --reload for the demo
python scripts\smoke_test.py                      # must exit 0
start http://127.0.0.1:8000
```

## Switch mock / live

Edit `APP_MODE` in the repo-root `.env` (`mock` or `live`) and restart the backend. Live needs
`pip install -r backend/requirements-ml.txt` and `python scripts/download_models.py`.
Check `GET /api/health`: `mode` and every model's state.

## Reset database and evidence

Stop the backend, then delete the contents (keep the `.gitkeep` files):

```powershell
Remove-Item data\* -Exclude .gitkeep; Remove-Item -Recurse evidence\* -Exclude .gitkeep
```

```bash
find data evidence -mindepth 1 ! -name .gitkeep -delete
```

## Recover a dead camera

1. `GET /api/cameras`: look at `state` and `last_error`.
2. `last_error` mentions "using synthetic": the video file is missing; check `videos/` and `backend/config/cameras.yaml`.
3. `OFFLINE`: the file failed to decode; re-encode it with `scripts/prepare_videos.py`. Runtime reconnect is owned by the camera stream.

## Recovery per failure

| Failure | Recovery |
|---|---|
| Health `detector: NOT_LOADED/ERROR` | `pip install -r backend/requirements-ml.txt`; check `backend/models/yolo26n.pt`; restart |
| `helmet` or `plates` NOT_LOADED | run `python scripts/download_models.py`; the demo still streams (no violations / NOT_DETECTED plates) |
| Camera OFFLINE / SYNTHETIC | check the file in `videos/`; restart the backend |
| `processing_fps` < 3 | lower `DETECTOR_IMGSZ` to 512, disable a camera in `cameras.yaml`, close other apps |
| Dashboard `ws: closed` | backend crashed or restarted: check its console; the UI reconnects by itself |
| Duplicate / missing violations | see pipeline.md §12; switch to the backup recording during the demo |

## Pre-demo checklist

- [ ] `git pull` on `main`; `pip install -r backend/requirements-ml.txt`; `npm ci` in `frontend/`
- [ ] `python scripts/download_models.py` succeeded with no network afterwards
- [ ] All 4 videos present; `/api/cameras` shows 4 × ONLINE and no `last_error`
- [ ] `/api/health` → `status: ok`, `mode: live`, all models `LOADED`
- [ ] Database and evidence reset (clean incident list)
- [ ] `python scripts/smoke_test.py` passes
- [ ] Backup screen recording on laptop + USB
- [ ] Laptop on power, sleep disabled, notifications off
