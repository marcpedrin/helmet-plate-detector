"""Export the detector and helmet models to ONNX (slightly faster on CPU-only machines).

Usage (repo root, after download_models.py):  python scripts/export_onnx.py
Then use .env.cpu.example (DETECTOR_WEIGHTS=yolo26n.onnx, HELMET_WEIGHTS=...onnx).
"""

from pathlib import Path

from ultralytics import YOLO

MODELS = Path(__file__).resolve().parents[1] / "backend" / "models"

if __name__ == "__main__":
    print(YOLO(str(MODELS / "yolo26n.pt")).export(format="onnx", imgsz=640, simplify=True))
    print(YOLO(str(MODELS / "helmet" / "helmet_yolo11s.pt")).export(format="onnx", imgsz=320, dynamic=True, simplify=True))
