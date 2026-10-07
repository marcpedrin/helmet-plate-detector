# backend/models/plates/

Owner: **Malik**.

* Plate detector: open-image-models `yolo-v9-t-384-license-plate-end2end` (auto-downloads to its own cache;
  `PLATE_DETECTOR_MODEL`).
* Fallback detector: `ANPR2.pt` from `PranavUikey/ANPR-Indian-License-Plate-Detection` (would be stored here).
* OCR: RapidOCR 3.9 (PP-OCR models, auto-downloaded).
* Warm caches: `python scripts/download_models.py` (calls `app.plates.download.download`).

If models are unavailable the app still starts; `/api/health` reports `plate_detector/ocr: NOT_LOADED`.
Details: [docs/modules/plates.md](../../../docs/modules/plates.md).
