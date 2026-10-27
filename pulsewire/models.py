from dataclasses import dataclass
from typing import Optional


@dataclass
class Packet:
    seq: int
    size_bytes: int
    generation_time: float = 0.0
    arrival_time: float = 0.0
    transmission_start: Optional[float] = None
    transmission_finish: Optional[float] = None
    delivery_time: Optional[float] = None
    ack_time: Optional[float] = None
    dropped: bool = False
    randomly_lost: bool = False
    delivered: bool = False
    acked: bool = False
    enqueued: bool = False

    @property
    def bit_size(self) -> int:
        return self.size_bytes * 8

    @property
    def latency(self) -> float:
        if self.delivery_time is not None and self.arrival_time is not None:
            return self.delivery_time - self.arrival_time
        return 0.0

    @property
    def rtt(self) -> float:
        if self.ack_time is not None and self.generation_time is not None:
            return self.ack_time - self.generation_time
        return 0.0


@dataclass(frozen=True)
class SimulationConfig:
    bandwidth_mbps: float
    latency_ms: float
    buffer_size: int
    packet_size_bytes: int
    rate_packets_per_sec: float
    loss_probability: float
    simulation_horizon_seconds: float
    random_seed: int

    def validate(self):
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
        if not (0.0 <= self.loss_probability <= 1.0):
            raise ValueError("loss_probability must be in [0, 1]")
        if self.simulation_horizon_seconds <= 0:
            raise ValueError("simulation_horizon_seconds must be positive")
        if not isinstance(self.random_seed, int):
            raise ValueError("random_seed must be an int")
        return self