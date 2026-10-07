# Privacy & responsible use

> **Prototype for demonstration. Detections are probabilistic and require human review; not admissible enforcement evidence.**

* **Local only.** Video, detections, evidence and the database never leave the machine. No cloud services,
  telemetry or third-party APIs are called at runtime (model weights are downloaded once, beforehand).
* **Store only violations.** Frames are processed in memory and discarded. Only confirmed `NO_HELMET`
  violations are persisted: three JPEGs (full frame, rider crop, plate crop) and one database row.
* **Retention.** Evidence and rows older than `EVIDENCE_RETENTION_DAYS` (default 7) are purged by
  `repository.purge_older_than()` (run at startup and daily by the storage module).
* **Never in git.** `evidence/`, `data/`, `videos/*.mp4`, `.env` and weights are git-ignored. Do not paste
  evidence images or real plate numbers into issues, PRs or chat; use mock-mode screenshots instead.
* **Footage licensing.** Use footage we recorded ourselves (with permission where needed) or footage whose
  license allows this use; record the source and license of every clip in
  [docs/modules/footage.md](modules/footage.md). Do not use footage scraped from social media.
* **Faces and plates.** Real plates appear in evidence images by design. Do not publish them; blur them in
  any material shared outside the team (slides, videos, README screenshots).
* **Human in the loop.** The UI presents incidents for review; it never issues fines or takes action.
* **Mock mode** output is fake and labelled "MOCK" everywhere.
