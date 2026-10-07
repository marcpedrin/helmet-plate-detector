# 0002: Frontend Live State Merging

Date: 2026-10-07
Author: Harish (@harish-gh)
Status: Accepted

## Context

The backend provides two primary mechanisms for retrieving data: a REST API (used for bootstrap and paginated queries) and a WebSocket stream (`/ws/events`) that pushes `violation_created`, `violation_updated`, `camera_status`, and `camera_metrics` live.
The dashboard requires real-time display of violations, especially the 2-stage lifecycle of a violation (where a violation is created immediately upon detection, but its plate is populated later).

## Decision

We manage all live WebSocket state in a single global Context `useLiveEvents`.
- **In-place merging**: The reducer matches incoming `violation_updated` messages by `id` and overwrites the existing entry in `recent` array.
- **REST fallback**: Detail pages (like `/violations/:id`) first fetch the snapshot via REST, but immediately overlay any matching live data from the context.
- **Bounding**: The `recent` array is strictly bounded to the latest 200 items to prevent memory leaks and React render thrashing.

## Consequences

**Positive:**
- Zero latency for plate OCR updates. A judge watching a detail page will see the PENDING plate flip to the actual text seamlessly without a page reload.
- Simplified component trees: Any component can grab `const { recent } = useLiveEvents()` and get the guaranteed latest data.

**Negative:**
- Large, rapid spikes in violations could cause frequent root re-renders. We mitigated this by avoiding deep-tree updates where possible and keeping the event rate throttled by the backend architecture.
