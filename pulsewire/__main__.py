import argparse

from .engine import SimulationEngine
from .metrics import calculate_metrics
from .models import SimulationConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PulseWire packet network simulator.")
    parser.add_argument("--scenario", choices=["demo"], default="demo")
    parser.add_argument("--horizon", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    config = SimulationConfig(simulation_horizon_seconds=args.horizon, random_seed=args.seed)
    result = SimulationEngine(config).run()
    metrics = calculate_metrics(result, config.simulation_horizon_seconds)
    print("PulseWire Discrete-Event Packet Network Simulator")
    print("=" * 48)
    print(f"Packets generated: {metrics.generated}")
    print(f"Packets delivered: {metrics.delivered}")
    print(f"Queue drops: {metrics.queue_drops}")
    print(f"Random losses: {metrics.random_losses}")
    print(f"Delivery ratio: {metrics.delivery_ratio:.3f}")
    print(f"Throughput: {metrics.throughput_mbps:.3f} Mbps")
    print(f"Average one-way latency: {metrics.average_latency_ms:.3f} ms")
    print(f"Average RTT: {metrics.average_rtt_ms:.3f} ms")
    print(f"Packets in flight or queued: {metrics.in_flight_or_queued}")


if __name__ == "__main__":
    main()
