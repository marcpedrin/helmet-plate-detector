# backend/models/helmet/

Owner: **Prajwal**.

Expected file: `helmet_yolo11s.pt` (path set by `HELMET_WEIGHTS`).

* Source: Hugging Face `nnsohamnn/helmet-detection-yolo11`, file `yolov11s(80 epochs).pt`, saved here as `helmet_yolo11s.pt`.
* Fallback: `iam-tsr/yolov8n-helmet-detection`, file `best.pt`.
* Download: `python scripts/download_models.py` (calls `app.helmet.download.download`).

If the file is missing the app still starts; `/api/health` reports `helmet: NOT_LOADED`.
Details: [docs/modules/helmet.md](../../../docs/modules/helmet.md).
