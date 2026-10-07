# Models

Owner: **Marc** (summary only). Owners document details, evaluation and tuning in their module docs;
**owners never edit this file** (send Marc the one-line change instead).

| Role | Model | Source / file | License | Download | Details |
|---|---|---|---|---|---|
| Person + motorcycle detector | **YOLO26n** (Ultralytics) + ByteTrack | `yolo26n.pt` (`DETECTOR_WEIGHTS`), saved to `backend/models/yolo26n.pt`; ultralytics 8.4.174 tested | AGPL-3.0 | auto on first load / `download_models.py` | [pipeline.md](modules/pipeline.md) |
| Helmet head-detector | YOLO11s helmet | HF `nnsohamnn/helmet-detection-yolo11`, file `yolov11s(80 epochs).pt` → `backend/models/helmet/helmet_yolo11s.pt` | card: MIT; Ultralytics-derived ⇒ AGPL obligations | `scripts/download_models.py` | [helmet.md](modules/helmet.md) |
| Helmet (fallback) | YOLOv8n helmet | HF `iam-tsr/yolov8n-helmet-detection`, `best.pt` | see card; Ultralytics-derived ⇒ AGPL | manual | [helmet.md](modules/helmet.md) |
| Plate detector | open-image-models `yolo-v9-t-384-license-plate-end2end` (ONNX) | `PLATE_DETECTOR_MODEL` | MIT | auto (open-image-models) | [plates.md](modules/plates.md) |
| Plate detector (fallback) | `ANPR2.pt` | GitHub `PranavUikey/ANPR-Indian-License-Plate-Detection` | MIT | manual | [plates.md](modules/plates.md) |
| OCR | RapidOCR 3.9 (PP-OCR) | `OCR_ENGINE=rapidocr` | Apache-2.0 | auto (RapidOCR) | [plates.md](modules/plates.md) |

Why these: [ADR 0003](adr/0003-marc-model-choices.md). The repository is AGPL-3.0 because Ultralytics is.

Weights are never committed. If any model is missing the app still starts and `/api/health` shows
`NOT_LOADED` for that model.
