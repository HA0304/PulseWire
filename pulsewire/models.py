from dataclasses import dataclass
from typing import Optional


@dataclass
class Packet:
    packet_id: int
    source: str
    destination: str
    size_bytes: int
    creation_time: float
    transmission_start: Optional[float] = None
    transmission_complete: Optional[float] = None
    delivery_time: Optional[float] = None
    acknowledgment_time: Optional[float] = None
    status: str = "generated"

    @property
    def bit_size(self) -> int:
        return self.size_bytes * 8

    @property
    def one_way_latency(self) -> Optional[float]:
        if self.delivery_time is None:
            return None
        return self.delivery_time - self.creation_time

    @property
    def rtt(self) -> Optional[float]:
        if self.acknowledgment_time is None:
            return None
        return self.acknowledgment_time - self.creation_time


@dataclass(frozen=True)
class SimulationConfig:
    bandwidth_mbps: float = 10.0
    latency_ms: float = 10.0
    buffer_size: int = 10
    packet_size_bytes: int = 500
    rate_packets_per_sec: float = 1.0
    loss_probability: float = 0.0
    simulation_horizon_seconds: float = 10.0
    random_seed: int = 42

    def validate(self) -> None:
        if self.bandwidth_mbps <= 0:
            raise ValueError("bandwidth_mbps must be positive")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be nonnegative")
        if self.buffer_size < 0:
            raise ValueError("buffer_size must be nonnegative")
        if self.packet_size_bytes <= 0:
            raise ValueError("packet_size_bytes must be positive")
        if self.rate_packets_per_sec < 0:
            raise ValueError("rate_packets_per_sec must be nonnegative")
        if not 0 <= self.loss_probability <= 1:
            raise ValueError("loss_probability must be between 0 and 1")
        if self.simulation_horizon_seconds <= 0:
            raise ValueError("simulation_horizon_seconds must be positive")
        if not isinstance(self.random_seed, int):
            raise ValueError("random_seed must be an integer")
