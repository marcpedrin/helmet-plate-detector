# 0003. Model choices

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

The demo must run in real time on one laptop (CPU fallback, GPU if available), on Indian traffic footage, with
models we can download today and legally use. Summary table: [MODELS.md](../MODELS.md).

## Decision

- **Detector + tracker**: Ultralytics **YOLO26n** (COCO person + motorcycle) with built-in **ByteTrack**.
  Small and fast, auto-downloads, good on two-wheelers. AGPL-3.0, so the repo is AGPL-3.0.
- **Helmet**: a YOLO11s **head-detector** (helmet / no-helmet heads) from HF `nnsohamnn/helmet-detection-yolo11`,
  run on rider crops only (fallback `iam-tsr/yolov8n-helmet-detection`). Classifying heads, not whole riders, handles
  pillion riders and is robust to bikes partly out of frame.
- **Plate detector**: open-image-models `yolo-v9-t-384-license-plate-end2end` (ONNX, MIT, auto-download); fallback
  `ANPR2.pt` (Indian plates, MIT).
- **OCR**: **RapidOCR 3.9** (PP-OCR, Apache-2.0) + our own Indian-format correction and multi-frame voting.
  **fast-plate-ocr was rejected because its released models exclude India**; PaddleOCR proper is a heavy install,
  and EasyOCR is slower and less accurate on plates.

## Alternatives considered

| Option | Why not |
|---|---|
| YOLOv8/11 detector | YOLO26n is newer/faster at the same size; same API |
| Whole-rider helmet classifier | Fails with pillion riders, confuses caps/scarves |
| fast-plate-ocr | Models exclude Indian plates |
| PaddleOCR (paddlepaddle) | Large, fragile install on Windows |
| EasyOCR | Slower on CPU, weaker on plates |
| Cloud ANPR APIs | Violates local-only ([PRIVACY.md](../PRIVACY.md)) |

## Consequences

Repo license AGPL-3.0. Three model families to download (`scripts/download_models.py`). Owners must validate on
**our** footage and record results in their module docs (section 11); swapping a model is a new ADR.
