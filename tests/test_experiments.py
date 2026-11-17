import pytest

from pulsewire.engine import SimulationEngine
from pulsewire.experiments import PRESETS, latency_over_time, throughput_over_time
from pulsewire.metrics import calculate_metrics


def test_three_reproducible_presets():
    assert set(PRESETS) == {"Queue overflow", "High RTT", "Packet loss"}
    for preset in PRESETS.values():
        first = SimulationEngine(preset.config).run()
        second = SimulationEngine(preset.config).run()
        assert first.event_trace == second.event_trace


def test_queue_overflow_known_outcome():
    preset = PRESETS["Queue overflow"]
    result = SimulationEngine(preset.config).run()
    metrics = calculate_metrics(result, preset.config.simulation_horizon_seconds)
    assert metrics.queue_drops > 0


def test_high_rtt_known_outcome():
    preset = PRESETS["High RTT"]
    result = SimulationEngine(preset.config).run()
    metrics = calculate_metrics(result, preset.config.simulation_horizon_seconds)
    assert metrics.delivered == metrics.generated
    assert metrics.average_latency_ms == pytest.approx(200.4, abs=0.1)


def test_packet_loss_known_outcome():
    preset = PRESETS["Packet loss"]
    result = SimulationEngine(preset.config).run()
    metrics = calculate_metrics(result, preset.config.simulation_horizon_seconds)
    assert metrics.delivered == 0
    assert metrics.random_losses == metrics.generated


def test_preset_chart_series_have_actual_units():
    preset = PRESETS["High RTT"]
    result = SimulationEngine(preset.config).run()
    throughput = throughput_over_time(result)
    latency = latency_over_time(result)
    assert throughput and max(point["throughput_mbps"] for point in throughput) >= 0
    assert latency and set(latency[0]) == {"time_s", "latency_ms"}
