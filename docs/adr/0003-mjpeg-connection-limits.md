# 0003: MJPEG Connection Limits and Fallbacks

Date: 2026-10-07
Author: Harish (@harish-gh)
Status: Accepted

## Context

The backend streams live camera footage using Motion JPEG (MJPEG) served directly over HTTP (`multipart/x-mixed-replace`).
We initially considered building a canvas-based frame player over WebSockets or WebRTC, but MJPEG via `<img>` tags requires zero JavaScript and has near-zero latency, which is ideal for a control room prototype.

However, browsers enforce a strict HTTP/1.1 connection limit (typically 6 concurrent connections per host). Because MJPEG requests never complete (the server continually pushes frames), having 6 or more `<img>` streams on a single page will starve all other REST and WebSocket requests, breaking the app.

## Decision

- **Hard limit**: The `CameraGrid` enforces a hard slice of `cameras.slice(0, 4)`. Even if 10 cameras are configured, the frontend dashboard will only ever render 4 live streams.
- **Cleanup**: The `CameraCard` explicitly clears its image `src` on unmount (`img.src = ''`) to ensure the browser drops the TCP connection. Without this, navigating away from the dashboard would leak connections.
- **Retry Logic**: When a camera goes `OFFLINE`, we set a 3-second `setInterval` to cache-bust the image `src` (`?t=timestamp`) to automatically resume the stream when it comes back.

## Consequences

**Positive:**
- Reliable network behavior: WebSocket and REST calls never queue or time out due to stream starvation.
- Lightweight: No complex client-side decoding libraries.

**Negative:**
- The frontend cannot display more than 4 cameras simultaneously. For a future multi-monitor control room viewing 16+ cameras, a true video proxy (e.g., WebRTC) will be required.
