#!/usr/bin/env python3
"""
ReliefChain AI — Non-Destructive API Performance & Latency Benchmark Utility
Measures response latency, status codes, and throughput across critical health,
readiness, metrics, geographic intelligence, and AI endpoints.
"""

import time
import urllib.request
import urllib.error
import json
import statistics
from typing import List, Dict, Any


TEST_TARGETS = [
    {"name": "Health Root", "path": "/health", "expected_status": 200},
    {"name": "Liveness Probe", "path": "/health/live", "expected_status": 200},
    {"name": "Readiness Probe", "path": "/health/ready", "expected_status": 200},
    {"name": "Telemetry Metrics", "path": "/metrics", "expected_status": 200},
    {"name": "AI Model Info", "path": "/api/v1/ai/model-info", "expected_status": 200},
    {"name": "Disaster Hotspots", "path": "/api/v1/geo/disaster-hotspots", "expected_status": 200},
]


def run_benchmark(base_url: str = "http://127.0.0.1:8000", iterations: int = 15) -> Dict[str, Any]:
    print(f"==================================================")
    print(f" ReliefChain AI — API Latency Benchmark Utility")
    print(f" Target Host: {base_url}")
    print(f" Iterations per target: {iterations}")
    print(f"==================================================")

    results: List[Dict[str, Any]] = []
    all_latencies: List[float] = []
    total_success = 0
    total_failed = 0

    for target in TEST_TARGETS:
        url = f"{base_url}{target['path']}"
        target_latencies: List[float] = []
        target_success = 0
        target_failed = 0

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ReliefChain-Benchmark/1.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    status_code = response.getcode()
                    _ = response.read()
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    target_latencies.append(elapsed_ms)
                    all_latencies.append(elapsed_ms)
                    if status_code == target["expected_status"]:
                        target_success += 1
                        total_success += 1
                    else:
                        target_failed += 1
                        total_failed += 1
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                target_failed += 1
                total_failed += 1

        avg_lat = statistics.mean(target_latencies) if target_latencies else 0.0
        min_lat = min(target_latencies) if target_latencies else 0.0
        max_lat = max(target_latencies) if target_latencies else 0.0
        p95_lat = sorted(target_latencies)[int(len(target_latencies) * 0.95)] if target_latencies else 0.0

        print(f"[{target['name']:<20}] Success: {target_success}/{iterations} | Avg: {avg_lat:6.2f}ms | Min: {min_lat:5.2f}ms | P95: {p95_lat:6.2f}ms | Max: {max_lat:6.2f}ms")

        results.append({
            "target": target["name"],
            "path": target["path"],
            "success": target_success,
            "failed": target_failed,
            "avg_ms": round(avg_lat, 2),
            "min_ms": round(min_lat, 2),
            "max_ms": round(max_lat, 2),
            "p95_ms": round(p95_lat, 2),
        })

    overall_avg = statistics.mean(all_latencies) if all_latencies else 0.0
    print(f"--------------------------------------------------")
    print(f"Overall Total Requests: {total_success + total_failed}")
    print(f"Total Success: {total_success}")
    print(f"Total Failed:  {total_failed}")
    print(f"Overall Average Response Time: {overall_avg:.2f}ms")
    print(f"==================================================")

    return {
        "total_requests": total_success + total_failed,
        "success_count": total_success,
        "failed_count": total_failed,
        "overall_avg_ms": round(overall_avg, 2),
        "results": results,
    }


if __name__ == "__main__":
    run_benchmark()
