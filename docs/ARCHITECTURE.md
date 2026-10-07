# Architecture

> **Live code map (Graphify): repository structure, module dependencies and ownership communities** →
> [graphify-out/graph.html](../graphify-out/graph.html) (open locally in a browser) ·
> report: [graphify-out/GRAPH_REPORT.md](../graphify-out/GRAPH_REPORT.md).
> The Mermaid diagrams below are the *designed* views (they describe code that does not exist yet);
> the Graphify map is the *generated* view of the code as it is. Marc regenerates it on `main` after merges.

## 1. Overview

A **modular monolith** ([ADR 0001](adr/0001-marc-modular-monolith.md)): one FastAPI process, one thread per
camera for decoding, one thread per camera for processing, SQLite + local filesystem for storage, and a React
dashboard. No Docker, Redis, Kafka, microservices or cloud.

Four prerecorded videos (`videos/camera_01.mp4` … `camera_04.mp4`) act as live "virtual cameras". The
browser receives video as **MJPEG** and every event over **one WebSocket**
([ADR 0002](adr/0002-marc-mjpeg-plus-single-websocket.md)). Model choices: [ADR 0003](adr/0003-marc-model-choices.md),
[MODELS.md](MODELS.md).

Modules (backend/app/) and owners:

| Module | Owner | Responsibility |
|---|---|---|
| `core/` | Marc | Contracts: `types.py`, `schemas.py`, `interfaces.py`, `geometry.py` |
| `camera/` | Marc (Codex stream) | Video sources, latest-frame buffers, MJPEG |
| `storage/` | Marc (Codex stream) | SQLite repository, evidence JPEGs |
| `helmet/` | Prajwal | Helmet head-detector on rider crops |
| `plates/` | Malik | Plate detector, RapidOCR, Indian-format correction, voting |
| `pipeline/` | Marc | Detector + tracker, rider association, violation engine, evidence, runners |
| `realtime/`, `api/` | Marc | EventHub, REST, WebSocket |
| `container.py` | Marc | Composition root: the only file importing every module |

## 2. Detection pipeline

```mermaid
flowchart LR
    VC["Virtual Camera<br/>(camera/)"] --> FP["Frame Processor<br/>(pipeline/runner.py)"]
    FP --> DET["Detector<br/>YOLO26n person+motorcycle"]
    DET --> TRK["Tracker<br/>ByteTrack"]
    TRK --> ASSOC["Rider association<br/>(association.py)"]
    ASSOC --> HEL["Helmet Classifier<br/>(helmet/)"]
    HEL --> VE["Violation Engine<br/>(violation_engine.py)"]
    VE --> PD["Plate Detector<br/>(plates/detector.py)"]
    PD --> OCR["OCR<br/>RapidOCR + Indian format + voting"]
    VE --> EV["Evidence<br/>(evidence.py)"]
    OCR --> EV
    EV --> DB[("Database<br/>SQLite + evidence/*.jpg")]
    DB --> API["FastAPI REST"]
    VE --> WS["WebSocket /ws/events"]
    API --> UI["React dashboard"]
    WS --> UI
```

## 3. Threading and data flow

```mermaid
flowchart TB
    subgraph CamThreads["Camera threads (1 per camera)"]
        C1["camera-CAM_01<br/>decode + pace"] --> B1[("latest-frame buffer<br/>lock-protected")]
        C2["camera-CAM_0N"] --> B2[("latest-frame buffer")]
    end
    subgraph PipeThreads["Pipeline threads (1 per camera, PIPELINE_FPS)"]
        P1["detect → track → associate → helmet → engine → plates"]
    end
    B1 --> P1
    B2 --> P1
    P1 -->|"repository.create / update_plate"| REPO[("SQLite + evidence/")]
    P1 -->|"overlay.set(tracks)"| OV["OverlayState"]
    P1 -->|"hub.publish(type, data)<br/>any thread"| HUB["EventHub<br/>call_soon_threadsafe"]
    HUB --> Q["per-client asyncio.Queue(100)<br/>drop-oldest"]
    Q --> WSC["/ws/events handler<br/>(asyncio loop)"]
    B1 -->|"latest frame"| MJ["MJPEG generator<br/>(asyncio + to_thread encode)"]
    OV -->|"draw boxes"| MJ
    MJ --> BR["Browser &lt;img&gt;"]
    WSC --> BR
```

Rules that keep this safe:

* Frames are immutable (`FramePacket.image` is read-only); whoever draws, copies.
* Only `EventHub.publish` crosses from threads into asyncio; it never blocks.
* Slow WebSocket clients lose the oldest messages, never stall the pipeline.
* MJPEG pulls the *latest* frame; there is no frame queue to grow unboundedly.

## 4. Sequence: from rider to UI

```mermaid
sequenceDiagram
    autonumber
    participant Cam as Camera thread
    participant Pipe as Pipeline thread
    participant Hel as HelmetClassifier
    participant Eng as ViolationEngine
    participant Pl as PlateService/Voter
    participant Repo as Repository
    participant Hub as EventHub
    participant UI as React UI
    Cam->>Pipe: latest FramePacket
    Pipe->>Pipe: track + associate → Rider (track_id)
    loop every processed frame
        Pipe->>Hel: classify_batch(frame, riders)
        Hel-->>Pipe: HelmetResult (NO_HELMET votes)
        Pipe->>Eng: update(packet, riders, helmets)
    end
    Eng-->>Pipe: SUSPECTED (≥3 NO_HELMET) → collect plates
    Pipe->>Pl: observe(frame, rider) → voter.add(obs)
    Eng-->>Pipe: CONFIRMED (≥6/10, mean conf ≥0.5, ≤2 HELMET)
    Pipe->>Repo: create(ViolationEvent, best evidence)
    Pipe->>Hub: publish("violation_created")
    Hub-->>UI: violation_created (plate_status=PENDING)
    loop until voter final or PLATE_WINDOW_S
        Pipe->>Pl: observe(...) (OCR ≤ PLATE_MAX_OCR_PER_TRACK)
    end
    Pipe->>Repo: update_plate(id, PlateResult, best_crop)
    Pipe->>Hub: publish("violation_updated")
    Hub-->>UI: violation_updated (READ / UNREADABLE / NOT_DETECTED)
```

## 5. Violation lifecycle (as built)

```mermaid
stateDiagram-v2
    [*] --> TRACKING: new rider track
    TRACKING --> SUSPECTED: ≥ ceil(MIN_HITS/2) = 3 NO_HELMET looks<br/>(plate collection starts)
    SUSPECTED --> CONFIRMED: ≥ 6 of last 10 NO_HELMET, mean conf ≥ 0.5,<br/>≤ 2 HELMET, age ≥ 5 looks → violation_created
    SUSPECTED --> SUPPRESSED: rule met but duplicate (same track,<br/>ID switch IoU ≥ 0.3 within 5 s,<br/>or same loop position ±1.5 s)
    CONFIRMED --> FINALIZED: PLATE_WINDOW_S elapsed, track lost > 1 s,<br/>or video restarted → violation_updated
    TRACKING --> [*]: lost > 2 s
    SUSPECTED --> [*]: lost > 2 s
    SUPPRESSED --> [*]: lost > 2 s
    FINALIZED --> [*]: lost > 30 s
```

Changes from the original plan: there is no separate PLATE_PENDING state (CONFIRMED *is* the plate-pending phase:
the stored violation has `plate_status: PENDING` until FINALIZED), and dedup happens *before* anything is emitted
(SUSPECTED → SUPPRESSED), so a duplicate never reaches the database. Full rules, config keys and examples:
[docs/modules/pipeline.md §7](modules/pipeline.md#7-algorithms--design-decisions); ADRs
[0005](adr/0005-marc-confirmation-rule.md), [0006](adr/0006-marc-dedup-and-loop-guard.md).
The "same loop position" rule exists because the virtual cameras loop: the same rider reappears every loop
and must not create a new violation each time.

**Performance (measured, CPU i5-8350U, no GPU):** YOLO26n tracking 98-260 ms/frame for imgsz 416-640; the CPU tops
out at ~7 detector inferences/s in total, so 4 cameras run at ~2 FPS each. Use a GPU for 4 cameras at ≥ 4 FPS, or
2-3 cameras on CPU. Details: [pipeline.md §9](modules/pipeline.md#9-performance).

## 6. Modes

| `APP_MODE` | Runner | Models | Use |
|---|---|---|---|
| `mock` | `MockRunner` | none (all `MOCK`) | develop API/UI without ML; clearly-labelled UI walkthrough |
| `live` | `PipelineRunner` | loaded by factories; missing ones report `NOT_LOADED` | the real demo |

Factories never raise: a missing weight file or package yields a fallback with `state=NOT_LOADED|ERROR`
and `/api/health` reports `degraded`. Missing videos fall back to a synthetic pattern.

## 7. Composition

`container.py` builds everything in this order and is the only place that knows concrete classes:

```
Settings → create_camera_manager → create_repository → EventHub
        → live:  load_helmet_classifier, load_plate_service, PipelineRunner
        → mock:  MockRunner
```

## 8. Graphify

`graphify-out/` is generated by running `graphify .` (or `/graphify .` in Claude Code) at the repo root.
Only `graph.html`, `graph.json` and `GRAPH_REPORT.md` are committed, only by Marc, only on `main`.
Ignored inputs are listed in [`.graphifyignore`](../.graphifyignore).
