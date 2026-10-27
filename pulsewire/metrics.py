from dataclasses import dataclass

from .engine import SimulationResult


@dataclass(frozen=True)
class Metrics:
    generated: int
    delivered: int
    queue_drops: int
    random_losses: int
    in_flight_or_queued: int
    delivery_ratio: float
    throughput_mbps: float
    average_latency_ms: float
    average_rtt_ms: float


def calculate_metrics(result: SimulationResult, horizon_seconds: float) -> Metrics:
    packets = result.packets
    delivered = [p for p in packets if p.delivery_time is not None]
    queue_drops = sum(p.status == "queue_drop" for p in packets)
    random_losses = sum(p.status == "random_loss" for p in packets)
    in_flight = len(packets) - len(delivered) - queue_drops - random_losses
    latency = [p.one_way_latency for p in delivered if p.one_way_latency is not None]
    rtts = [p.rtt for p in delivered if p.rtt is not None]
    return Metrics(
        generated=len(packets),
        delivered=len(delivered),
        queue_drops=queue_drops,
        random_losses=random_losses,
        in_flight_or_queued=in_flight,
        delivery_ratio=len(delivered) / len(packets) if packets else 0.0,
        throughput_mbps=sum(p.bit_size for p in delivered) / horizon_seconds / 1_000_000,
        average_latency_ms=(sum(latency) / len(latency) * 1000) if latency else 0.0,
        average_rtt_ms=(sum(rtts) / len(rtts) * 1000) if rtts else 0.0,
    )
