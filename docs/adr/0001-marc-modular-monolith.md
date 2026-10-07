# 0001. Modular monolith, threads per camera, SQLite

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

Four developers, a hackathon deadline, one demo laptop, four virtual cameras. Everything must run locally and
offline. The team needs to work in parallel with minimal merge conflicts.

## Decision

One FastAPI process. One decode thread and one processing thread per camera, latest-frame buffers between them,
SQLite + local filesystem for storage. Modules talk only through the Protocols in `core/interfaces.py`;
`container.py` is the only file that imports every module. Each module has one owner and its own folder.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| Microservices (camera/inference/API) + Redis/Kafka | Independent scaling | Ops overhead, serialisation of frames, more failure modes | Nothing to scale; costs days |
| Docker Compose | Reproducible env | GPU passthrough on Windows, slow iteration | Venv + npm is enough for 4 devs |
| multiprocessing per camera | Avoids the GIL | Frame sharing via shared memory, harder debugging | OpenCV/torch release the GIL; threads suffice at 5 FPS |
| PostgreSQL | Concurrency | Install + service on the demo laptop | Write rate is a few rows per minute |

## Consequences

Simple deploy (two commands), easy debugging, one log. Module boundaries are enforced by convention, CODEOWNERS
and review, not by process isolation. A crash in one thread must never kill the process: every loop catches and
logs exceptions, and factories never raise.
