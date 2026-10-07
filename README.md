# Helmet & Plate Detector

Local, real-time **helmet-violation + number-plate detection** on four virtual cameras (prerecorded road videos).
Hackathon prototype by a 4-person team.

```
4 × MP4 ─▶ YOLO26n + ByteTrack ─▶ rider association ─▶ helmet head-detector ─▶ temporal confirmation
        ─▶ best evidence frame ─▶ plate detector ─▶ RapidOCR + Indian format + voting
        ─▶ SQLite + JPEG evidence ─▶ FastAPI (REST + MJPEG + 1 WebSocket) ─▶ React dashboard
```

> Prototype for demonstration. Detections are probabilistic and require human review; not admissible enforcement evidence.

- Architecture & diagrams: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Live code map (Graphify): repository structure, module dependencies and ownership communities** →
  [graphify-out/graph.html](graphify-out/graph.html) (download/open locally) · [GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md)
- Contracts (types, REST, WebSocket): [docs/CONTRACTS.md](docs/CONTRACTS.md)
- Who owns what: [docs/OWNERSHIP.md](docs/OWNERSHIP.md) · How we work: [CONTRIBUTING.md](CONTRIBUTING.md)

## Quickstart

Requirements: Python 3.12 (64-bit), Node 22 LTS, git. Run from the repo root.

### Windows PowerShell

```powershell
cd backend
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements-core.txt -r requirements-dev.txt   # mock mode (no ML)
# pip install -r requirements-ml.txt                            # live mode (see GPU note in the file)
cd ..; Copy-Item .env.example .env                               # APP_MODE=mock by default
# python scripts/download_models.py                              # live mode only
scripts\run_backend.ps1                                          # http://127.0.0.1:8000/docs
# new terminal:
cd frontend; npm install; Copy-Item .env.example .env; cd ..
scripts\run_frontend.ps1                                         # http://localhost:5173
```

### bash (Linux / macOS / Git Bash)

```bash
cd backend && python -m venv .venv && source .venv/bin/activate   # Git Bash: .venv/Scripts/activate
pip install -r requirements-core.txt -r requirements-dev.txt      # or requirements-ml.txt for live
cd .. && cp .env.example .env
# python scripts/download_models.py                               # live mode only
scripts/run_backend.sh
# new terminal:
cd frontend && npm install && cp .env.example .env && cd .. && scripts/run_frontend.sh
```

Check it: `python scripts/smoke_test.py` (exits 0 when REST, snapshot and WebSocket all work).

Tests: `cd backend && ruff check . && pytest -m "not model"` · `cd frontend && npm run lint && npm run typecheck && npm test && npm run build`.

## Modes

`APP_MODE=mock` runs everything with **no ML**: synthetic camera feeds when videos are missing, fake tracks,
fake violations every 8-15 s per camera, fake plates 2 s later. Everything is stamped **MOCK**.
`APP_MODE=live` loads the models; anything missing shows as `NOT_LOADED` in `/api/health` instead of crashing.

## Configuration (`.env`)

| Key | Default | Meaning |
|---|---|---|
| `APP_MODE` | `mock` | `mock` or `live` |
| `LOG_LEVEL` | `INFO` | Python log level |
| `CAMERAS_CONFIG` | `backend/config/cameras.yaml` | Camera list |
| `EVIDENCE_DIR` / `DB_PATH` | `evidence` / `data/violations.db` | Storage (git-ignored) |
| `EVIDENCE_RETENTION_DAYS` | `7` | Purge older violations |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated |
| `DEVICE` | `auto` | `auto`, `cpu`, `cuda`, `cuda:N` |
| `DETECTOR_WEIGHTS` / `_IMGSZ` / `_CONF` | `yolo26n.pt` / `640` / `0.30` | Person+motorcycle detector |
| `PIPELINE_FPS` | `5` | Processing rate per camera |
| `MIN_RIDER_HEIGHT_PX` | `80` | Ignore tiny riders |
| `HELMET_WEIGHTS` / `_IMGSZ` / `_CONF` | `backend/models/helmet/helmet_yolo11s.pt` / `320` / `0.35` | Helmet head-detector |
| `PLATE_DETECTOR_MODEL` / `_CONF` | `yolo-v9-t-384-license-plate-end2end` / `0.40` | Plate detector |
| `PLATE_MIN_WIDTH_PX` | `50` | Ignore tiny plates |
| `OCR_ENGINE` | `rapidocr` | OCR engine |
| `VIOLATION_WINDOW` / `_MIN_HITS` / `_MIN_CONF` / `_MAX_HELMET_HITS` | `10` / `6` / `0.50` / `2` | Confirmation rule |
| `PLATE_WINDOW_S` / `PLATE_MAX_OCR_PER_TRACK` | `3.0` / `8` | Plate reading budget |
| `DEDUP_IOU` / `DEDUP_WINDOW_S` | `0.3` / `5.0` | Duplicate suppression |
| `STREAM_FPS` / `STREAM_WIDTH` / `STREAM_JPEG_QUALITY` | `15` / `960` / `70` | MJPEG output |

Frontend: `frontend/.env` → `VITE_API_BASE=http://localhost:8000`.

## Team & ownership

| Who | Area | Branch |
|---|---|---|
| Marc `@marcpedrin` | core, pipeline, realtime/API, integration, CI, docs | `feature/pipeline` |
| Marc (Codex stream) | camera + storage | `feature/backend-camera` |
| Prajwal `@prajwal-gh` (**TODO** handle) | helmet model + demo footage | `feature/helmet-detection` |
| Malik `@malik-gh` (**TODO** handle) | plates + OCR | `feature/plate-ocr` |
| Harish `@harish-gh` (**TODO** handle) | frontend | `feature/frontend-dashboard` |

Details: [docs/OWNERSHIP.md](docs/OWNERSHIP.md).

## Privacy

Local only; only confirmed violations are stored; evidence is purged after `EVIDENCE_RETENTION_DAYS`; evidence,
data, videos and weights are never committed. See [docs/PRIVACY.md](docs/PRIVACY.md).

## License

[AGPL-3.0](LICENSE) (Ultralytics YOLO is AGPL-3.0). Model licenses: [docs/MODELS.md](docs/MODELS.md).
