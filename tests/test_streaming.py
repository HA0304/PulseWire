import pytest

from pulsewire.engine import SimulationEngine
from pulsewire.models import SimulationConfig
from pulsewire.streaming import BoundedEventBuffer, EventBatch, StreamSession, StreamStatus, batch_events


def test_bounded_event_buffer_drops_oldest():
    buffer = BoundedEventBuffer(limit=2)
    buffer.append({"id": 1})
    buffer.append({"id": 2})
    buffer.append({"id": 3})
    assert len(buffer) == 2
    assert buffer.dropped == 1
    assert buffer.drain() == ({"id": 2}, {"id": 3})


def test_event_batching_is_bounded():
    batches = list(batch_events(({"id": i} for i in range(7)), batch_size=3))
    assert [len(batch.events) for batch in batches] == [3, 3, 1]
    assert [batch.sequence for batch in batches] == [0, 1, 2]


def test_stream_session_pause_resume_stop():
    session = StreamSession(batch_size=2, buffer_limit=4)
    session.start()
    assert session.status is StreamStatus.RUNNING
    session.pause()
    assert session.status is StreamStatus.PAUSED
    session.resume()
    assert session.status is StreamStatus.RUNNING
    session.stop()
    assert session.status is StreamStatus.STOPPED


def test_stream_batch_is_versioned():
    batch = EventBatch(sequence=4, events=({"event": "ACK"},))
    assert batch.protocol == "pulsewire.events"
    assert batch.version == 1
    assert batch.sequence == 4


def test_engine_streams_at_least_one_thousand_events():
    config = SimulationConfig(
        rate_packets_per_sec=1000,
        simulation_horizon_seconds=1,
        bandwidth_mbps=10,
        latency_ms=1,
        max_event_history=4096,
    )
    engine = SimulationEngine(config)
    count = sum(1 for _ in engine.iter_events())
    assert count >= 1000


@pytest.mark.parametrize("batch_size", [0, 4097])
def test_invalid_batch_size(batch_size):
    with pytest.raises(ValueError):
        list(batch_events([{"id": 1}], batch_size=batch_size))
