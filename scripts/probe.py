#!/usr/bin/env python3
"""Sonde de production : ./scripts/probe.py <url_de_base> [seuil_ms]

Vérifie /health et /version, mesure le temps de réponse.
Code de sortie 0 si tout va bien, 1 sinon (le pipeline ouvre alors une carte Trello).
"""

import json
import sys
import time
import urllib.request


def fetch(url: str) -> tuple[int, bytes, float]:
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310
        body = resp.read()
        return resp.status, body, (time.perf_counter() - start) * 1000


def main() -> int:
    base = sys.argv[1].rstrip("/")
    threshold_ms = float(sys.argv[2]) if len(sys.argv) > 2 else 500
    try:
        status, _, elapsed = fetch(f"{base}/health")
        _, version_body, _ = fetch(f"{base}/version")
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "raison": f"injoignable : {exc}"}, ensure_ascii=False))
        return 1

    version = json.loads(version_body)
    ok = status == 200 and elapsed <= threshold_ms
    print(
        json.dumps(
            {
                "ok": ok,
                "http": status,
                "temps_ms": round(elapsed, 1),
                "seuil_ms": threshold_ms,
                "version": version.get("version"),
            },
            ensure_ascii=False,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
