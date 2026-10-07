"""Per-camera detection pipeline: detect -> track -> associate -> helmet -> violation -> plate.

Owner: Marc (``feature/pipeline``). ``mock_runner.MockRunner`` drives mock mode;
``runner.PipelineRunner`` drives live mode once implemented.

Never import torch/ultralytics at module top level here; import inside constructors.
"""
