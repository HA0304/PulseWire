import pytest

from pulsewire.engine import SimulationEngine
from pulsewire.events import Event, EventKind
from pulsewire.metrics import calculate_metrics
from pulsewire.models import SimulationConfig


def test_event_order_is_monotonic():
    config = SimulationConfig(
        rate_packets_per_sec=100,
        simulation_horizon_seconds=1,
        random_seed=7,
    )
    result = SimulationEngine(config).run()
    keys = [(row["time"], row["sequence_number"]) for row in result.event_trace]
    assert keys == sorted(keys)
    assert len(set(keys)) == len(keys)


@pytest.mark.parametrize("loss", [0.0, 0.25, 1.0])
def test_seeded_replay_is_identical(loss):
    config = SimulationConfig(
        rate_packets_per_sec=25,
        simulation_horizon_seconds=2,
        loss_probability=loss,
        random_seed=123,
        max_event_history=256,
    )
    first = SimulationEngine(config).run()
    second = SimulationEngine(config).run()
    assert first.event_trace == second.event_trace
    assert [packet.status for packet in first.packets] == [packet.status for packet in second.packets]


def test_packet_conservation_across_stochastic_parameters():
    for seed in range(5):
        config = SimulationConfig(
            rate_packets_per_sec=40,
            simulation_horizon_seconds=2,
            buffer_size=3,
            loss_probability=0.3,
            random_seed=seed,
        )
        result = SimulationEngine(config).run()
        metrics = calculate_metrics(result, 2)
        assert metrics.generated == (
            metrics.delivered
            + metrics.queue_drops
            + metrics.random_losses
            + metrics.in_flight_or_queued
        )


def test_event_history_is_bounded():
    config = SimulationConfig(
        rate_packets_per_sec=100,
        simulation_horizon_seconds=10,
        random_seed=42,
        max_event_history=32,
    )
    result = SimulationEngine(config).run()
    assert len(result.event_trace) <= 32


def test_engine_cancel_interrupts_iteration():
    engine = SimulationEngine(SimulationConfig(
        rate_packets_per_sec=1000,
        simulation_horizon_seconds=10,
        max_event_history=4096,
    ))
    count = 0
    cancelled = False
    for _ in engine.iter_events(cancel_check=lambda: cancelled):
        count += 1
        if count == 10:
            cancelled = True
    assert count == 10
