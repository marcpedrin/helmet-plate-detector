# backend/models/

Model weights live here and are **never committed** (`*.pt`, `*.onnx` are git-ignored).

```bash
python scripts/download_models.py   # from the repo root, inside the venv with requirements-ml.txt
```

| Folder | Owner | Contents |
|---|---|---|
| `helmet/` | Prajwal | `helmet_yolo11s.pt` (see [helmet/README.md](helmet/README.md)) |
| `plates/` | Malik | optional explicit plate files; open-image-models / RapidOCR cache their own (see [plates/README.md](plates/README.md)) |

YOLO26n (`yolo26n.pt`) is auto-downloaded by Ultralytics into its own cache on first use.
Full model table and licenses: [docs/MODELS.md](../../docs/MODELS.md).
