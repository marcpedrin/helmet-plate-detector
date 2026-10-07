"""End-to-end smoke test against a running backend (mock or live).

Usage:  python scripts/smoke_test.py [--base http://127.0.0.1:8000] [--timeout 20]
Exit code 0 when every check passes, 1 otherwise. Needs httpx; the WebSocket check
needs ``websockets`` (installed with uvicorn[standard]) and is reported as skipped otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    try:
        import httpx
    except ImportError:
        print("SKIP: httpx not installed (pip install -r backend/requirements-dev.txt)")
        return 1

    ok = True

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        ok &= bool(cond)
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")

    with httpx.Client(base_url=args.base, timeout=10) as c:
        try:
            health = c.get("/api/health").json()
        except httpx.HTTPError as exc:
            print(f"[FAIL] backend not reachable at {args.base}: {exc}")
            return 1
        check("GET /api/health", health.get("status") in ("ok", "degraded"), json.dumps(health))
        cams = c.get("/api/cameras").json()
        check("GET /api/cameras", isinstance(cams, list) and len(cams) > 0, f"{len(cams)} cameras")
        if cams:
            r = None
            for _ in range(20):
                r = c.get(cams[0]["snapshot_url"])
                if r.status_code == 200:
                    break
                time.sleep(0.25)
            check("GET snapshot.jpg", r is not None and r.content[:2] == b"\xff\xd8", f"{len(r.content)} bytes")
        page = c.get("/api/violations").json()
        check("GET /api/violations", "items" in page and "total" in page, f"total={page.get('total')}")
        stats = c.get("/api/stats").json()
        check("GET /api/stats", "total_violations" in stats, json.dumps(stats))

    try:
        from websockets.sync.client import connect
    except ImportError:
        print("[SKIP] /ws/events: websockets not installed")
        return 0 if ok else 1

    ws_url = args.base.replace("http", "ws", 1) + "/ws/events"
    seen: list[str] = []
    deadline = time.monotonic() + args.timeout
    try:
        with connect(ws_url, open_timeout=5) as ws:
            while time.monotonic() < deadline:
                try:
                    msg = json.loads(ws.recv(timeout=max(0.1, deadline - time.monotonic())))
                except TimeoutError:
                    break
                seen.append(msg["type"])
                if msg["type"] == "violation_created":
                    break
    except Exception as exc:
        check("WS /ws/events", False, str(exc))
        return 1
    check("WS hello first", bool(seen) and seen[0] == "hello")
    if health.get("mode") == "mock" or health.get("models", {}).get("helmet") == "LOADED":
        check(f"WS violation_created within {args.timeout:.0f}s", "violation_created" in seen,
              f"types seen: {sorted(set(seen))}")
    else:  # live mode without a helmet model cannot confirm violations
        print(f"[SKIP] WS violation_created (live mode, helmet {health['models']['helmet']}); "
              f"types seen: {sorted(set(seen))}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
