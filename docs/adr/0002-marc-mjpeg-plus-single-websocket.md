# 0002. MJPEG for video, one WebSocket for events

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

The dashboard shows four live feeds with detection overlays and must receive violations, plate updates, camera
status and metrics in real time. Local network, single viewer, prototype.

## Decision

Video: one MJPEG stream per camera (`/api/cameras/{id}/stream.mjpg`), overlay drawn server-side, displayed with a
plain `<img>`. Events: a single WebSocket `/ws/events` carrying typed `WsEnvelope` messages (`hello`,
`camera_status`, `camera_metrics`, `violation_created`, `violation_updated`, `stats`). Threads publish through
`EventHub.publish` (thread-safe, drop-oldest per client).

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| WebRTC | Low bandwidth, low latency | Signalling, aiortc/encoders, NAT, complexity | Overkill on localhost |
| HLS / DASH | Standard | Seconds of latency, segmenting | Latency too high for a live demo |
| Frames over WebSocket | One channel | Base64/binary framing, canvas code, backpressure | MJPEG gives this for free |
| Client-side overlays from metrics | Smaller payloads | Box/frame sync is hard | Server-side drawing is always in sync |
| One WS per topic, or SSE | Simpler filtering | More connections; SSE is one-way only anyway | One socket is easy to reconnect |

## Consequences

Bandwidth ≈ 4 × (960 px JPEG q70 × 15 fps) ≈ 4-8 MB/s on localhost, which is fine. Browsers cap ~6 HTTP/1.1
connections per origin: 4 MJPEG + API calls fits, but a 5th open dashboard tab may stall. Use one tab, or serve
the built frontend from FastAPI.
