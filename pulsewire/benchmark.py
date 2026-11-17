import argparse
import statistics
import time
import tracemalloc

from .engine import SimulationEngine
from .models import SimulationConfig


def benchmark_event_volume(event_target: int, repeats: int = 3) -> dict[str, float | int]:
    durations = []
    peak_bytes = 0
    event_count = 0
    for _ in range(repeats):
        rate = float(event_target)
        horizon = 1.0
        config = SimulationConfig(
            bandwidth_mbps=10.0,
            latency_ms=10.0,
            buffer_size=max(1, event_target),
            packet_size_bytes=500,
            rate_packets_per_sec=rate,
            loss_probability=0.0,
            simulation_horizon_seconds=horizon,
            random_seed=42,
            max_event_history=4096,
        )
        tracemalloc.start()
        started = time.perf_counter()
        engine = SimulationEngine(config)
        event_count = sum(1 for _ in engine.iter_events())
        durations.append(time.perf_counter() - started)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_bytes = max(peak_bytes, peak)
    median_seconds = statistics.median(durations)
    return {
        "target": event_target,
        "event_count": event_count,
        "median_seconds": median_seconds,
        "events_per_second": event_count / median_seconds if median_seconds else 0.0,
        "peak_bytes": peak_bytes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark PulseWire event throughput")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    for target in (1000, 10000, 100000):
        print(benchmark_event_volume(target, args.repeats))


if __name__ == "__main__":
    main()
