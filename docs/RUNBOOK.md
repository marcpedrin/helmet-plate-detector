# Runbook

Owner: Marc. Skeleton: owners add entries as they learn how their module fails.

## Start / stop

| | Windows PowerShell | bash |
|---|---|---|
| Backend | `scripts\run_backend.ps1` | `scripts/run_backend.sh` |
| Frontend | `scripts\run_frontend.ps1` | `scripts/run_frontend.sh` |
| Smoke test | `python scripts/smoke_test.py` | same |

Stop with `Ctrl+C`. Shutdown stops runner threads, then camera threads.

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
3. `OFFLINE`: the file failed to decode; re-encode it with `scripts/prepare_videos.py`. _TBD (camera stream): runtime reconnect._

## Pre-demo checklist

- [ ] `git pull` on `main`; `pip install -r backend/requirements-ml.txt`; `npm ci` in `frontend/`
- [ ] `python scripts/download_models.py` succeeded with no network afterwards
- [ ] All 4 videos present; `/api/cameras` shows 4 × ONLINE and no `last_error`
- [ ] `/api/health` → `status: ok`, `mode: live`, all models `LOADED`
- [ ] Database and evidence reset (clean incident list)
- [ ] `python scripts/smoke_test.py` passes
- [ ] Backup screen recording on laptop + USB
- [ ] Laptop on power, sleep disabled, notifications off
