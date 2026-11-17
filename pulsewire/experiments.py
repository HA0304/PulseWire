from dataclasses import dataclass

from .engine import SimulationResult
from .models import SimulationConfig


@dataclass(frozen=True)
class ExperimentPreset:
    name: str
    description: str
    config: SimulationConfig


PRESETS: dict[str, ExperimentPreset] = {
    "Queue overflow": ExperimentPreset(
        "Queue overflow",
        "High offered load, small finite buffer, and a 1 Mbps link.",
        SimulationConfig(
            bandwidth_mbps=1.0,
            latency_ms=10.0,
            buffer_size=1,
            packet_size_bytes=1000,
            rate_packets_per_sec=1000.0,
            loss_probability=0.0,
            simulation_horizon_seconds=1.0,
            random_seed=42,
        ),
    ),
    "High RTT": ExperimentPreset(
        "High RTT",
        "Low offered load with 200 ms one-way propagation delay.",
        SimulationConfig(
            bandwidth_mbps=10.0,
            latency_ms=200.0,
            buffer_size=10,
            packet_size_bytes=500,
            rate_packets_per_sec=1.0,
            loss_probability=0.0,
            simulation_horizon_seconds=5.0,
            random_seed=42,
        ),
    ),
    "Packet loss": ExperimentPreset(
        "Packet loss",
        "Complete channel loss; every transmitted packet is dropped.",
        SimulationConfig(
            bandwidth_mbps=10.0,
            latency_ms=10.0,
            buffer_size=10,
            packet_size_bytes=500,
            rate_packets_per_sec=1.0,
            loss_probability=1.0,
            simulation_horizon_seconds=5.0,
            random_seed=42,
        ),
    ),
}


def throughput_over_time(result: SimulationResult) -> list[dict[str, float]]:
    delivered = sorted(
        (packet for packet in result.packets if packet.delivery_time is not None),
        key=lambda packet: packet.delivery_time or 0.0,
    )
    cumulative_bits = 0.0
    points = []
    for packet in delivered:
        cumulative_bits += packet.bit_size
        points.append({
            "time_s": packet.delivery_time or 0.0,
            "throughput_mbps": cumulative_bits / max(packet.delivery_time or 0.0, 1e-9) / 1_000_000,
        })
    return points


def latency_over_time(result: SimulationResult) -> list[dict[str, float]]:
    points = []
    for packet in result.packets:
        if packet.one_way_latency is not None:
            points.append({
                "time_s": packet.delivery_time or 0.0,
                "latency_ms": packet.one_way_latency * 1000,
            })
    return sorted(points, key=lambda point: point["time_s"])
