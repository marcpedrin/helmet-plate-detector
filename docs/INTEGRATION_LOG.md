# Integration log

Owner: Marc. One row per merge into `main` that changes runtime behaviour. Record what broke during
integration and every threshold you tuned, so the demo configuration is reproducible.

| Date | PR | Merged by | Issues found during integration | Tuning (key: old → new, why) |
|---|---|---|---|---|
| 2026-10-07 | boilerplate (initial push) | Marc | — | — |
| 2026-10-07 | #2 feature/pipeline (draft, not merged) | — | live mode verified on 4 synthetic cameras; CPU perf below target (~2 FPS/camera at 416 px) | none yet: no demo clips |
