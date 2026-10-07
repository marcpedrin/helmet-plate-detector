# HANDOFF — what's done / what's next

Running log so any agent (Claude Code, Codex) can pick up. **Update this file after every step.**
Goal: `http://127.0.0.1:8000` shows 4 virtual cameras with REAL helmet + number-plate detection (`APP_MODE=live`).

## Status (newest last)

| # | Step | Status | Notes |
|---|---|---|---|
| 1 | Pull merged PRs #1–#5 onto `main` (pipeline, helmet classifier, camera/storage, frontend) | DONE | |
| 2 | Install `backend/requirements-ml.txt` into `backend/.venv` | DONE | dev box has **no GPU** (CPU only) |
| 3 | Helmet weights `backend/models/helmet/helmet_yolo11s.pt` (HF `nnsohamnn/helmet-detection-yolo11`) | DONE | classes `With Helmet` / `Without Helmet`; sha256 511e40f7… |
| 4 | Plate module `backend/app/plates/*` (detector, RapidOCR, Indian format, voter, service, download) | DONE | tests: `pytest tests/plates` 15 pass |
| 5 | 4 demo videos in `videos/camera_01..04.mp4` | DONE | Pexels (free license) clips, transcoded to 720p25 with `scripts/prepare_videos.py`. Raw 4K in `data/raw_videos/`, 720p in `data/clips720/` (git-ignored). CAM_01=pexels 34394881, CAM_02=34394431, CAM_03=38617712, CAM_04=15328413 (first 30 s). Re-create on any machine with `python scripts/fetch_demo_videos.py` |
| 6 | `.env` → `APP_MODE=live`, run end-to-end, tune | DONE (CPU profile) | live server runs, all 4 models LOADED. Offline check (`scripts/run_pipeline_offline.py`) on CAM_01 clip: 4 correct NO_HELMET violations, plate `MP04YE5981` read correctly; CAM_02 clip: 1 violation, plate `MP04MP0569` correct. CPU-only box: ~1-2 FPS/camera |
| 7 | Build frontend, served by FastAPI at :8000 | DONE | `cd frontend && npm run build`; open http://127.0.0.1:8000 |
| 8 | GPU laptop (RTX 3050 6 GB) setup notes | DONE | `.env.gpu.example`, section below |
| 9 | CPU profile | DONE | `.env.cpu.example`: ONNX models (`scripts/export_onnx.py`), 3-of-6 rule because CPU gives only ~1-2 FPS/camera. Checked: no false positives on demo clips |
| 10 | Vercel | IN PROGRESS | Only the dashboard (frontend) can run on Vercel; it talks to the backend at http://127.0.0.1:8000 on the viewing laptop. Backend allows `https://*.vercel.app` + Chrome Private-Network-Access header |

## How to run (live)

```bash
cd backend
.venv/Scripts/python -m pip install -r requirements-ml.txt
python ../scripts/download_models.py
# .env at repo root: APP_MODE=live
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## GPU laptop (RTX 3050 6 GB) - full setup (Windows, PowerShell)

```powershell
git clone https://github.com/marcpedrin/helmet-plate-detector.git; cd helmet-plate-detector
cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128   # NVIDIA driver >= 570
pip install -r requirements-ml.txt
python -c "import torch; print(torch.cuda.is_available())"    # must print True
cd ..
python scripts/download_models.py        # yolo26n.pt, helmet weights, plate detector, OCR
python scripts/fetch_demo_videos.py      # 4 clips -> videos/ (git-ignored, ~300 MB download)
copy .env.gpu.example .env               # DEVICE=cuda:0, 8 FPS, strict 6-of-10 rule
cd frontend; npm install; npm run build; cd ..
cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000 (or the Vercel URL on the same laptop).

CPU-only machine: same steps but skip the CUDA torch line, then `python scripts/export_onnx.py` and `copy .env.cpu.example .env`.

## Known issues / decisions

- Fixed 2 API tests that assumed no weights on disk / non-hex violation ids (now 80 pass).

- Plate OCR = RapidOCR (PP-OCR) because fast-plate-ocr's models exclude India.
- Single-digit district codes (e.g. `DL3CAB1234`) are only accepted for `DL`.
