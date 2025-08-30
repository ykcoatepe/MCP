from __future__ import annotations
from typing import Dict
from collections import defaultdict
import threading

_lock = threading.Lock()
_counters: Dict[str, int] = defaultdict(int)
_lat_ms: Dict[str, list[int]] = defaultdict(list)


def inc(name: str) -> None:
    with _lock:
        _counters[name] += 1


def obs_latency(tool: str, ms: int) -> None:
    with _lock:
        _lat_ms[tool].append(ms)
        if len(_lat_ms[tool]) > 1000:
            _lat_ms[tool] = _lat_ms[tool][-500:]


def snapshot() -> dict:
    with _lock:
        out = {"counters": dict(_counters), "latency": {}}
        for k, arr in _lat_ms.items():
            if arr:
                arr_sorted = sorted(arr)
                out["latency"][k] = {
                    "count": len(arr_sorted),
                    "p50": arr_sorted[len(arr_sorted) // 2],
                    "p95": arr_sorted[max(0, int(len(arr_sorted) * 0.95) - 1)],
                    "max": arr_sorted[-1],
                }
            else:
                out["latency"][k] = {"count": 0}
        return out

