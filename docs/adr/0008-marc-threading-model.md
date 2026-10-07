# 0008. Threading model: thread per camera + latest-frame buffer

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

Four cameras decode at 15-30 FPS but inference runs at 2-8 FPS. FastAPI's event loop must stay responsive for
MJPEG and WebSocket clients. The process must survive any per-frame exception.

## Decision

- One decode thread per camera writes only the **latest** frame into a lock-protected buffer (no queues, so
  slow inference never builds latency).
- One pipeline thread per camera pulls the latest frame at `PIPELINE_FPS`, skips frames it has already seen, and
  owns its tracker and engine (thread-confined, no locks needed inside them).
- One broadcast thread publishes `camera_metrics` (2 Hz) and `stats` (5 s).
- Threads talk to asyncio only through `EventHub.publish` (`call_soon_threadsafe`, drop-oldest queues).
- Every loop iteration is wrapped in try/except; errors are counted and rate-limit logged.

## Alternatives considered

| Option | Why not |
|---|---|
| asyncio + `to_thread` per frame | same GIL behaviour, harder state ownership |
| multiprocessing per camera | frame sharing via shared memory, 4 model copies in 4 processes, harder debugging |
| Single pipeline thread round-robin | one slow camera stalls all; no parallelism while torch releases the GIL |
| Frame queues | latency grows without bound when inference is slower than decode |

## Consequences

Torch releases the GIL during inference, so threads parallelise, but on a 4-core CPU four trackers oversubscribe
the cores (measured: ~7 inferences/s total). Capping torch threads per tracker is the next experiment.
