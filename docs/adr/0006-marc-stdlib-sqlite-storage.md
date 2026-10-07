# 0006. Standard-library SQLite storage

- Status: accepted
- Date: 2026-10-07
- Owner: Marc

## Context

The local modular monolith needs durable violation history without a service or migration framework.

## Decision

Use one lock-serialized `sqlite3` connection with WAL and local atomic JPEG files.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| ORM | Rich migrations | Extra dependency and abstraction | Unnecessary schema size |
| Server database | Multi-process scale | Operations overhead | Violates local-first scope |

## Consequences

The design is robust for one process and simple to inspect, but is not a distributed write solution.
