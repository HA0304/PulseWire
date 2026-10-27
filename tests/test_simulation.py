import pytest

from pulsewire.engine import SimulationEngine
from pulsewire.events import Event, EventKind
from pulsewire.metrics import calculate_metrics
from pulsewire.models import SimulationConfig


def config(**overrides):
    values = dict(simulation_horizon_seconds=2.0)
    values.update(overrides)
    return SimulationConfig(**values)


def test_event_tie_breaking():
    events = [Event(1.0, 2, EventKind.PACKET_ARRIVAL), Event(1.0, 1, EventKind.ACK_ARRIVAL)]
    assert sorted(events)[0].sequence_number == 1


def test_transmission_delay_is_analytical():
    engine = SimulationEngine(config(packet_size_bytes=1000, bandwidth_mbps=8))
    assert engine.transmission_delay_seconds == pytest.approx(0.001)


def test_serialization_and_deterministic_rtt():
    result = SimulationEngine(config(rate_packets_per_sec=1, packet_size_bytes=1000, bandwidth_mbps=8, latency_ms=10)).run()
    assert [p.transmission_start for p in result.packets] == [0.0, 1.0]
    assert result.packets[0].rtt == pytest.approx(0.021)


def test_low_traffic_delivers_all():
    result = SimulationEngine(config(rate_packets_per_sec=1, simulation_horizon_seconds=3)).run()
    metrics = calculate_metrics(result, 3)
    assert metrics.delivered == metrics.generated == 3


def test_queue_overflow_and_conservation():
    result = SimulationEngine(config(
        rate_packets_per_sec=1000,
        simulation_horizon_seconds=1,
        buffer_size=1,
        bandwidth_mbps=1,
        packet_size_bytes=1000,
    )).run()
    metrics = calculate_metrics(result, 1)
    assert metrics.queue_drops > 0
    assert metrics.generated == metrics.delivered + metrics.queue_drops + metrics.random_losses + metrics.in_flight_or_queued


def test_total_channel_loss():
    result = SimulationEngine(SimulationConfig(loss_probability=1.0)).run()
    metrics = calculate_metrics(result, 10)
    assert metrics.delivered == 0
    assert metrics.random_losses == metrics.generated


def test_seed_reproducibility():
    cfg = config(loss_probability=0.4, rate_packets_per_sec=5)
    assert SimulationEngine(cfg).run().event_trace == SimulationEngine(cfg).run().event_trace


def test_zero_rate_has_no_packets():
    result = SimulationEngine(config(rate_packets_per_sec=0)).run()
    assert result.packets == []
    assert result.event_trace == []


def test_zero_capacity_buffer_drops_packets():
    result = SimulationEngine(config(rate_packets_per_sec=2, buffer_size=0)).run()
    metrics = calculate_metrics(result, 2)
    assert metrics.generated == metrics.queue_drops == 4
    assert metrics.delivered == 0


@pytest.mark.parametrize("field,value", [("bandwidth_mbps", 0), ("packet_size_bytes", 0), ("loss_probability", 2)])
def test_invalid_configuration_rejected(field, value):
    with pytest.raises(ValueError):
        SimulationEngine(config(**{field: value}))


def test_non_finite_configuration_rejected():
    with pytest.raises(ValueError, match="finite"):
        SimulationEngine(config(rate_packets_per_sec=float("nan")))
