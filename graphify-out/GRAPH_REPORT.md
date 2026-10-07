# Graph Report - helmet-plate-detector  (2026-10-07)

## Corpus Check
- 119 files · ~29,497 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 15, .example 2, .css 1)

## Summary
- 1246 nodes · 2279 edges · 89 communities (69 shown, 20 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 225 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9e437aef`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- contracts.ts
- Realtime & API
- pipeline/test_smoke.py
- types.py
- main.py
- container.py
- Container
- HelmetResult
- <Module name>
- schemas.py
- check_docs.py
- cameras.py
- CameraConfig
- ModelState
- CameraManager
- package.json
- EvidenceStore
- components.json
- MockRunner
- compilerOptions
- interfaces.py
- PlateResult
- Rider
- violation_engine.py
- devDependencies
- PlateObservation
- compilerOptions
- EventHub
- ViolationRepositoryProtocol
- mock_runner.py
- Camera
- Frontend
- Storage
- dependencies
- Demo footage
- Helmet
- Pipeline
- Plates & OCR
- VideoFileSource
- CameraManagerProtocol
- MockPlateVoter
- InMemoryRepository
- SqliteViolationRepository
- violations.py
- _CameraWorker
- pathlib
- .publish
- RunnerProtocol
- repository.py
- classifier.py
- FramePacket
- database.py
- .observe
- indian_format.py
- Architecture
- draw_tracks
- eslint.config.js
- scripts
- wait_for
- ARCHITECTURE.md
- Demo guide
- Runbook
- manager.py
- .latest_frame
- .update_plate
- 0001. Modular monolith, threads per camera, SQLite
- 0003. Model choices
- MODELS.md
- tsconfig.json
- vite.config.ts
- EvidenceBundle
- run_backend.sh
- app/pipeline/__init__.py
- realtime/__init__.py
- TROUBLESHOOTING.md
- engines
- frontend/README.md
- cn
- @testing-library/jest-dom
- run_frontend.sh script
- helmet-plate-detector

## God Nodes (most connected - your core abstractions)
1. `ModelState` - 46 edges
2. `Container` - 39 edges
3. `Settings` - 32 edges
4. `Rider` - 32 edges
5. `MockRunner` - 30 edges
6. `PlateResult` - 27 edges
7. `ViolationOut` - 24 edges
8. `CameraManager` - 23 edges
9. `CameraManagerProtocol` - 23 edges
10. `ViolationRepositoryProtocol` - 23 edges

## Surprising Connections (you probably didn't know these)
- `1. Purpose & scope` --references--> `MockRunner`  [INFERRED]
  docs/modules/pipeline.md → backend/app/pipeline/mock_runner.py
- `Protocols (interfaces.py)` --references--> `CameraManager`  [INFERRED]
  docs/CONTRACTS.md → backend/app/camera/manager.py
- `Protocols (interfaces.py)` --references--> `CameraManagerProtocol`  [INFERRED]
  docs/CONTRACTS.md → backend/app/core/interfaces.py
- `Protocols (interfaces.py)` --references--> `ViolationRepositoryProtocol`  [INFERRED]
  docs/CONTRACTS.md → backend/app/core/interfaces.py
- `Protocols (interfaces.py)` --references--> `HelmetClassifierProtocol`  [INFERRED]
  docs/CONTRACTS.md → backend/app/core/interfaces.py

## Import Cycles
- None detected.

## Communities (89 total, 20 thin omitted)

### Community 0 - "contracts.ts"
Cohesion: 0.06
Nodes (74): App(), frontend_src_components_ui_badge, frontend_src_components_ui_badge_badge, frontend_src_components_ui_card, frontend_src_components_ui_card_card, frontend_src_components_ui_card_cardcontent, frontend_src_components_ui_card_cardheader, frontend_src_components_ui_card_cardtitle (+66 more)

### Community 1 - "Realtime & API"
Cohesion: 0.04
Nodes (42): Branches, Commits, Conflicts, Contract changes, Contributing, Documentation (Definition of Done), Hard rules, Keeping in sync (+34 more)

### Community 2 - "pipeline/test_smoke.py"
Cohesion: 0.07
Nodes (40): area(), center(), clip(), crop(), expand(), _intersection(), ioa(), iou() (+32 more)

### Community 3 - "types.py"
Cohesion: 0.09
Nodes (26): HeadDetection, PlateDetection, PlateRead, One head found by the helmet head-detector inside a rider crop (frame coords)., One number-plate box (frame coords) found inside a motorcycle region., One OCR read of a plate crop, after Indian-format correction., Core domain types shared by every backend module. These dataclasses are the in-…, PlateDetector (+18 more)

### Community 4 - "main.py"
Cohesion: 0.09
Nodes (25): health(), Depends, get, ``GET /api/health``. Owner: Marc., Return mode, model load states and overall status (``ok`` / ``degraded``)., get_container(), REST + WebSocket routers. Thin: all logic lives in the container's services.…, FastAPI dependency returning the app's ``Container`` (works for HTTP and… (+17 more)

### Community 5 - "container.py"
Cohesion: 0.11
Nodes (25): create_camera_manager(), Virtual cameras: config loading, frame sources, the camera manager and MJPEG…, Build the camera manager from ``settings.cameras_config``. Never raises: if the…, get_settings(), Path, Application settings, loaded from environment variables and the repo-root…, Return ``path`` as an absolute path, interpreting relative paths against…, All runtime configuration. Field names map to upper-case env vars (``APP_MODE``… (+17 more)

### Community 6 - "Container"
Cohesion: 0.08
Nodes (23): Container, Start cameras, then the runner., Stop the runner, then cameras (idempotent)., Return the load state of every model family., Return overall health. ``degraded`` when any camera is OFFLINE, or in live mode…, Return the runner's latest metrics for one camera., Return the wire representation of one camera (raises KeyError if unknown)., Return dashboard statistics (also published as ``stats`` WS messages). (+15 more)

### Community 7 - "HelmetResult"
Cohesion: 0.12
Nodes (25): HelmetClassifierProtocol, Classifies helmet status for every rider in a frame. Thread-safety: called from…, HelmetResult, HelmetStatus, Aggregated helmet verdict for one rider in one frame., Per-head (or per-rider) helmet classification., load_helmet_classifier(), Helmet classification on rider crops (head detector: HELMET / NO_HELMET per… (+17 more)

### Community 8 - "<Module name>"
Cohesion: 0.06
Nodes (27): Alternatives considered, Consequences, Context, Decision, NNNN. <Title>, Definition of Done (every PR), Documentation standard, Four layers (+19 more)

### Community 9 - "schemas.py"
Cohesion: 0.12
Nodes (26): CameraOut, EvidenceUrls, HealthOut, ModelsHealth, Envelope wrapping every message sent on ``/ws/events``., URLs (served under ``/evidence``) of the evidence JPEGs for one violation., Pydantic v2 wire schemas for REST responses and WebSocket messages. Mirrored…, One stored violation as returned by REST and ``violation_*`` WS messages. (+18 more)

### Community 10 - "check_docs.py"
Cohesion: 0.08
Nodes (17): argparse, importlib_util, json, re, check_file(), main(), Path, Validate module docs in docs/modules/ against the 14-section template. Usage:… (+9 more)

### Community 11 - "cameras.py"
Cohesion: 0.13
Nodes (24): asyncio, get_camera(), list_cameras(), get, Camera endpoints: list, detail, MJPEG stream and JPEG snapshot. Owner: Marc…, Return every enabled camera with runtime state and metrics., Return one camera (404 if unknown)., Stream the camera as MJPEG (``multipart/x-mixed-replace``) with the overlay… (+16 more)

### Community 12 - "CameraConfig"
Cohesion: 0.12
Nodes (18): load_cameras(), Path, Load ``config/cameras.yaml`` into ``CameraConfig`` objects. Owner: Marc (camera…, Parse the cameras YAML file. Args: path: Absolute path to a YAML file with a…, Frame sources: a synthetic test pattern and a looping video file. Owner: Marc…, Generates 1280x720 test frames: camera name, wall clock and a moving rectangle.…, Create a synthetic source for ``config`` (no I/O)., Return True; a synthetic source cannot fail to open. (+10 more)

### Community 13 - "ModelState"
Cohesion: 0.13
Nodes (19): ModelState, Enum, str, Load state of an ML model, reported by ``/api/health``., Create the mock reporting ``state`` (MOCK, NOT_LOADED or ERROR)., load_plate_service(), Number-plate detection, OCR, Indian-format correction and multi-frame voting.…, Load the plate detector + OCR for live mode. Args: settings: Uses… (+11 more)

### Community 14 - "CameraManager"
Cohesion: 0.09
Nodes (14): CameraManager, OverlayFn, Implements ``CameraManagerProtocol`` with one daemon thread per enabled camera.…, Start all camera threads., Stop all camera threads (idempotent)., Return enabled camera ids in config order., Return the config of ``camera_id`` (raises KeyError if unknown)., Return the runtime snapshot of ``camera_id`` (raises KeyError if unknown). (+6 more)

### Community 15 - "package.json"
Cohesion: 0.08
Nodes (23): name, private, type, version, class-variance-authority, eslint, @fontsource-variable/geist, jsdom (+15 more)

### Community 16 - "EvidenceStore"
Cohesion: 0.11
Nodes (16): EvidenceStore, ndarray, Path, Writes evidence JPEGs to ``EVIDENCE_DIR`` and maps them to ``/evidence/...``…, Stores evidence images at ``<root>/<camera_id>/<violation_id>/<kind>.jpg``.…, Create the store; ``root`` is created on first save. Args: root: Absolute…, Return the absolute file path for one evidence image (does not create it)., Return the public URL for one evidence image. (+8 more)

### Community 17 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 18 - "MockRunner"
Cohesion: 0.14
Nodes (13): CameraMetricsMsg, One tracked rider as drawn on the live stream overlay., Payload of ``camera_metrics`` WS messages., TrackOverlay, _CameraSim, _label(), MockRunner, ndarray (+5 more)

### Community 19 - "compilerOptions"
Cohesion: 0.10
Nodes (20): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+12 more)

### Community 20 - "interfaces.py"
Cohesion: 0.13
Nodes (13): EventPublisherProtocol, PlateServiceProtocol, Protocol, Detects and reads number plates inside a rider's motorcycle region., Return a fresh voter for one violation., Publishes realtime events to WebSocket clients., Publish one message. Callable from any thread; never blocks, never raises., Protocols every module implements; ``container.py`` wires implementations to… (+5 more)

### Community 21 - "PlateResult"
Cohesion: 0.18
Nodes (15): Return the current voted result (PENDING until anything was observed)., PlateResult, PlateStatus, Final (voted) plate outcome for one violation., Outcome of number-plate reading for one violation., Return the current voted result., make_event(), Shared fixtures. Tests never need ML packages, weights or videos. (+7 more)

### Community 22 - "Rider"
Cohesion: 0.12
Nodes (13): A motorcycle track associated with the person tracks riding it. ``rider_id``…, Rider, EvidenceSelector, Best-evidence-frame selection for confirmed violations. Owner: Marc. Signatures…, Keeps, per rider, the best frame seen so far while the rider is…, Create an empty selector holding at most ``max_riders`` candidates., Consider this frame as evidence for ``rider`` (copies the image only if it…, Release the stored frame for ``rider_id``. (+5 more)

### Community 23 - "violation_engine.py"
Cohesion: 0.12
Nodes (14): EngineDecision, Enum, str, Temporal violation confirmation per rider track. Owner: Marc. Signatures are…, Lifecycle phase of one rider track inside the engine., What the runner must do for one rider after an ``update``. Attributes:…, Per-camera state machine turning noisy per-frame helmet results into…, Create the engine with thresholds from settings (``VIOLATION_*``, ``DEDUP_*``). (+6 more)

### Community 24 - "devDependencies"
Cohesion: 0.11
Nodes (19): devDependencies, eslint, @eslint/js, eslint-plugin-jsdoc, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, jsdom (+11 more)

### Community 25 - "PlateObservation"
Cohesion: 0.14
Nodes (13): PlateVoterProtocol, Accumulates plate observations for one violation and votes on the final text., Add one observation (detections without reads still count as evidence)., PlateObservation, Plate detection + OCR result for one rider in one frame (any part may be None)., Return a fresh ``PlateVoter``., PlateVoter, ndarray (+5 more)

### Community 26 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 27 - "EventHub"
Cohesion: 0.13
Nodes (10): AbstractEventLoop, EventHub, Any, Implements ``EventPublisherProtocol`` for the single ``/ws/events`` WebSocket.…, Create a hub with per-client queues of ``queue_size`` messages., Bind the event loop that owns the client queues (called from the app lifespan)., Number of connected clients., Register ``ws`` and return its message queue (binds the loop if not yet bound). (+2 more)

### Community 28 - "ViolationRepositoryProtocol"
Cohesion: 0.13
Nodes (10): Return one violation, or None if it does not exist., Return violations newest-first, optionally filtered by camera., Return aggregate counters over all stored violations., Delete violations (and evidence files) older than ``days``; return how many., Persists violations and their evidence JPEGs. Thread-safety: every method may…, Persist a new violation and its evidence images; return the stored record., Set the final plate result (and optional crop) on an existing violation.…, ViolationRepositoryProtocol (+2 more)

### Community 29 - "mock_runner.py"
Cohesion: 0.18
Nodes (12): Mock-mode runner: fake tracks, fake violations and fake plates, no ML at all.…, OverlayState, Overlay drawing for MJPEG streams (rider boxes coloured by helmet status).…, Latest overlay tracks per camera; callable as an ``OverlayFn``. Thread-safety:…, Create an empty overlay state., Live-mode pipeline runner: one processing thread per camera. Owner: Marc.…, test_overlay_state_draws_boxes(), collections_abc (+4 more)

### Community 30 - "Camera"
Cohesion: 0.12
Nodes (15): 10. Testing, 11. Evaluation & verification results, 12. Troubleshooting / FAQ, 13. Known limitations & future work, 14. Changelog, 1. Purpose & scope, 2. Owner & files, 3. Architecture (+7 more)

### Community 31 - "Frontend"
Cohesion: 0.12
Nodes (15): 10. Testing, 11. Evaluation & verification results, 12. Troubleshooting / FAQ, 13. Known limitations & future work, 14. Changelog, 1. Purpose & scope, 2. Owner & files, 3. Architecture (+7 more)

### Community 32 - "Storage"
Cohesion: 0.12
Nodes (15): 10. Testing, 11. Evaluation & verification results, 12. Troubleshooting / FAQ, 13. Known limitations & future work, 14. Changelog, 1. Purpose & scope, 2. Owner & files, 3. Architecture (+7 more)

### Community 33 - "dependencies"
Cohesion: 0.12
Nodes (16): dependencies, class-variance-authority, cn, @fontsource-variable/geist, lucide-react, next-themes, radix-ui, react (+8 more)

### Community 34 - "Demo footage"
Cohesion: 0.13
Nodes (15): 10. Testing, 11. Evaluation & verification results, 12. Troubleshooting / FAQ, 13. Known limitations & future work, 14. Changelog, 1. Purpose & scope, 2. Owner & files, 3. Architecture (+7 more)

### Community 35 - "Helmet"
Cohesion: 0.13
Nodes (15): 10. Testing, 11. Evaluation & verification results, 12. Troubleshooting / FAQ, 13. Known limitations & future work, 14. Changelog, 1. Purpose & scope, 2. Owner & files, 3. Architecture (+7 more)

### Community 36 - "Pipeline"
Cohesion: 0.13
Nodes (15): 10. Testing, 11. Evaluation & verification results, 12. Troubleshooting / FAQ, 13. Known limitations & future work, 14. Changelog, 1. Purpose & scope, 2. Owner & files, 3. Architecture (+7 more)

### Community 37 - "Plates & OCR"
Cohesion: 0.13
Nodes (15): 10. Testing, 11. Evaluation & verification results, 12. Troubleshooting / FAQ, 13. Known limitations & future work, 14. Changelog, 1. Purpose & scope, 2. Owner & files, 3. Architecture (+7 more)

### Community 38 - "VideoFileSource"
Cohesion: 0.14
Nodes (9): ndarray, Path, Release the OpenCV capture., Return ``(ok, bgr_frame, video_pos_ms)`` for the next synthetic frame., Reads a video file with OpenCV and loops it when ``config.loop`` is True.…, Prepare a source for ``config.source`` resolved against ``repo_root`` (no I/O…, Open the file; return False if it is missing or cannot be decoded., Return ``(ok, bgr_frame, video_pos_ms)``; rewinds at end of file when looping. (+1 more)

### Community 39 - "CameraManagerProtocol"
Cohesion: 0.15
Nodes (8): CameraManagerProtocol, OverlayFn, Owns the virtual cameras and their latest-frame buffers. Thread-safety: every…, Start one reader thread per enabled camera. Never raises on a bad source., Stop all reader threads and release sources. Idempotent., Return the ids of all configured (enabled) cameras, in config order., Register the function used to draw overlays on streamed frames., Create the runner (no thread yet). Args: cameras: Source of frames and overlay…

### Community 40 - "MockPlateVoter"
Cohesion: 0.15
Nodes (8): MockPlateVoter, ndarray, Voter that never sees a plate: PENDING until the first ``add``, then…, Create an empty voter., Count the observation (contents ignored except for ``ocr_count``)., Return PENDING before any observation, NOT_DETECTED after., Return None (no crops)., Return a ``MockPlateVoter``.

### Community 41 - "InMemoryRepository"
Cohesion: 0.17
Nodes (7): InMemoryRepository, Return one violation or None., Return violations newest-first, optionally filtered by camera., Return totals by camera and plate outcome., Drop violations (and their evidence) older than ``days``; return the count., Working in-memory ``ViolationRepositoryProtocol``; evidence JPEGs still go to…, Create an empty repository writing evidence through ``evidence``.

### Community 42 - "SqliteViolationRepository"
Cohesion: 0.17
Nodes (7): SQLite-backed ``ViolationRepositoryProtocol`` (camera/storage stream implements…, See ``ViolationRepositoryProtocol.create``., See ``ViolationRepositoryProtocol.get``., See ``ViolationRepositoryProtocol.list``., See ``ViolationRepositoryProtocol.counts``., See ``ViolationRepositoryProtocol.purge_older_than``., SqliteViolationRepository

### Community 43 - "violations.py"
Cohesion: 0.22
Nodes (10): get_violation(), list_violations(), Depends, get, ``GET /api/violations`` and ``GET /api/violations/{id}``. Owner: Marc., Return violations newest-first, optionally filtered by ``camera_id``., Return one violation. Raises: HTTPException: 404 if it does not exist., ge (+2 more)

### Community 44 - "_CameraWorker"
Cohesion: 0.25
Nodes (4): _CameraWorker, Path, Create workers for every enabled camera in ``configs`` (threads start in…, Reader thread + latest-frame buffer for one camera (internal).

### Community 45 - "pathlib"
Cohesion: 0.18
Nodes (9): download(), Path, Download helmet weights from Hugging Face. Owner: Prajwal. See…, Download the helmet weights into ``dest_dir`` if missing. Args: dest_dir:…, download(), Path, Pre-fetch plate detector / OCR models. Owner: Malik. open-image-models and…, Download (or warm the cache of) the plate detector and OCR models. Args:… (+1 more)

### Community 46 - ".publish"
Cohesion: 0.18
Nodes (8): Serialise one message as a ``WsEnvelope`` JSON string (``ts`` = now, UTC)., Queue a message for every connected client. Never blocks, never raises. Args:…, 0002. MJPEG for video, one WebSocket for events, Alternatives considered, Consequences, Context, Decision, 3. Threading and data flow

### Community 47 - "RunnerProtocol"
Cohesion: 0.20
Nodes (6): Protocol, What the container needs from ``PipelineRunner`` and ``MockRunner``., Load state of the object detector., Stop processing (idempotent)., Latest metrics for one camera., RunnerProtocol

### Community 48 - "repository.py"
Cohesion: 0.24
Nodes (8): A confirmed violation, handed by the pipeline to the repository., ViolationEvent, Violation repositories: the SQLite one (pending) and a working in-memory one.…, Convert a pipeline ``ViolationEvent`` plus saved evidence URLs into the wire…, Save evidence images and store the violation; return the stored record., to_violation_out(), datetime, time

### Community 49 - "classifier.py"
Cohesion: 0.20
Nodes (7): ndarray, Path, YOLO head-detector based helmet classifier. Owner: Prajwal. Signatures are…, Runs a YOLO helmet/head detector on each rider's upper-body crop. Contract…, Load the model (import ultralytics here, not at module level). Args: weights:…, Return one ``HelmetResult`` per rider, same order as ``riders``., YoloHelmetClassifier

### Community 50 - "FramePacket"
Cohesion: 0.25
Nodes (8): Return the most recent frame, or None if no frame has been decoded yet., FramePacket, One decoded frame plus its provenance. ``image`` is a BGR ``uint8`` array…, Harish — frontend (`feature/frontend-dashboard`), Marc (Codex stream) — camera + storage (`feature/backend-camera`), Marc — core, pipeline, integration (`feature/pipeline`, `feature/integration`), Per-developer detail, Prajwal — helmet + demo footage (`feature/helmet-detection`)

### Community 51 - "database.py"
Cohesion: 0.25
Nodes (8): connect(), init_db(), Path, SQLite connection management and schema. Owner: Marc (camera/storage stream).…, Open (creating parent dirs) a SQLite connection usable from multiple threads.…, Create tables and indexes if missing and migrate to ``SCHEMA_VERSION``. Args:…, Connection, sqlite3

### Community 52 - ".observe"
Cohesion: 0.25
Nodes (5): BBox, ndarray, Return one ``HelmetResult`` per rider, in the same order. Never raises on bad…, Return the crop that best supports the current result, if any., Detect (and optionally OCR) the plate of ``rider`` in ``frame``. Args: frame:…

### Community 53 - "indian_format.py"
Cohesion: 0.25
Nodes (7): correct(), is_valid(), normalize(), Indian number-plate normalisation, OCR-confusion correction and validation.…, Upper-case and strip everything except ``A-Z0-9`` (``"ka-01 ab 1234"`` ->…, Fix position-dependent OCR confusions (``O<->0``, ``I<->1``, ``B<->8``,…, Return True if ``text`` (already normalised) matches an Indian plate pattern.

### Community 54 - "Architecture"
Cohesion: 0.25
Nodes (8): 1. Overview, 2. Detection pipeline, 4. Sequence: from rider to UI, 5. Violation lifecycle, 6. Modes, 7. Composition, 8. Graphify, Architecture

### Community 55 - "draw_tracks"
Cohesion: 0.33
Nodes (5): draw_tracks(), ndarray, Draw ``tracks`` onto ``image`` in place and return it. Args: image: Writable…, Return a copy of the tracks for ``camera_id``., Draw the current tracks of ``camera_id`` onto ``image`` (an ``OverlayFn``).

### Community 56 - "eslint.config.js"
Cohesion: 0.29
Nodes (6): @eslint/js, eslint-plugin-jsdoc, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, typescript-eslint

### Community 57 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, typecheck

### Community 58 - "wait_for"
Cohesion: 0.33
Nodes (5): test_snapshot_returns_jpeg(), Path, test_missing_video_falls_back_to_synthetic(), Poll ``predicate`` until it returns a truthy value or ``timeout`` elapses., wait_for()

### Community 60 - "Demo guide"
Cohesion: 0.33
Nodes (4): Demo guide, Demo script (≈ 4 minutes), Fallback plan, Footage guidance (owner: Prajwal)

### Community 61 - "Runbook"
Cohesion: 0.33
Nodes (6): Pre-demo checklist, Recover a dead camera, Reset database and evidence, Runbook, Start / stop, Switch mock / live

### Community 62 - "manager.py"
Cohesion: 0.40
Nodes (4): Camera manager: one reader thread per camera feeding a latest-frame buffer.…, # WHY: minimal pacing at target_fps; the camera stream adds source-time pacing…, CameraState, Lifecycle state of one virtual camera.

### Community 63 - ".latest_frame"
Cohesion: 0.40
Nodes (3): ndarray, Return the latest frame of ``camera_id`` or None (raises KeyError if unknown)., Return a writable copy of the latest frame with the overlay applied, or None.…

### Community 64 - ".update_plate"
Cohesion: 0.40
Nodes (3): ndarray, Set the plate result; raises KeyError if ``violation_id`` is unknown., See ``ViolationRepositoryProtocol.update_plate``.

### Community 65 - "0001. Modular monolith, threads per camera, SQLite"
Cohesion: 0.40
Nodes (5): 0001. Modular monolith, threads per camera, SQLite, Alternatives considered, Consequences, Context, Decision

### Community 66 - "0003. Model choices"
Cohesion: 0.40
Nodes (5): 0003. Model choices, Alternatives considered, Consequences, Context, Decision

### Community 68 - "tsconfig.json"
Cohesion: 0.40
Nodes (4): compilerOptions, paths, files, references

### Community 69 - "vite.config.ts"
Cohesion: 0.40
Nodes (4): ref_node_path, @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 70 - "EvidenceBundle"
Cohesion: 0.50
Nodes (3): EvidenceBundle, Images saved as evidence for one violation (BGR arrays)., Return the evidence bundle (full frame annotated + rider crop) or None if…

## Knowledge Gaps
- **324 isolated node(s):** `helmet-plate-detector`, `$schema`, `style`, `rsc`, `tsx` (+319 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 727 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Protocols (interfaces.py)` connect `PlateObservation` to `Realtime & API`, `types.py`, `HelmetResult`, `CameraManagerProtocol`, `InMemoryRepository`, `SqliteViolationRepository`, `CameraManager`, `classifier.py`, `interfaces.py`, `EventHub`, `ViolationRepositoryProtocol`, `mock_runner.py`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `Contracts` connect `Realtime & API` to `PlateObservation`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `MockRunner` connect `MockRunner` to `Pipeline`, `container.py`, `Container`, `CameraManagerProtocol`, `EvidenceBundle`, `schemas.py`, `HelmetResult`, `ModelState`, `repository.py`, `interfaces.py`, `PlateResult`, `Architecture`, `ViolationRepositoryProtocol`, `mock_runner.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `ModelState` (e.g. with `Container` and `RunnerProtocol`) actually correct?**
  _`ModelState` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `Container` (e.g. with `_require()` and `health()`) actually correct?**
  _`Container` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Settings` (e.g. with `create_camera_manager()` and `Container`) actually correct?**
  _`Settings` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Rider` (e.g. with `HelmetClassifierProtocol` and `PlateServiceProtocol`) actually correct?**
  _`Rider` has 11 INFERRED edges - model-reasoned connections that need verification._
## Notes (Marc, 2026-10-07)

- Generated with `graphify update .` (AST only, no LLM). Docs are indexed by structure only; run `/graphify . --update` in Claude Code for semantic doc extraction.
- Communities roughly match the owner modules (Camera, Storage, Helmet, Plates & OCR, Pipeline, Realtime & API, Frontend).
- Expected deviation: shared contract types (`types.py`, `schemas.py`, `interfaces.py`, `contracts.ts`, `HelmetResult`, `Rider`, ...) form their own hub communities because every module depends on them. That is the intended star topology around `core/`, not a boundary leak.
- Regenerate only on `main`, after merges (see CONTRIBUTING.md).
