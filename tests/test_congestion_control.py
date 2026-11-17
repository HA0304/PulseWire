import pytest

from pulsewire.congestion import CongestionEvent, CongestionEventKind, RenoCongestionControl, SenderState
from pulsewire.sender import TCPSender
from pulsewire.trace import CongestionTraceRecorder
from tests.fixtures.reno_traces import SLOW_START_REFERENCE


def event(time, kind):
    return CongestionEvent(time, kind)


def test_sender_starts_with_reno_state():
    state = SenderState()
    assert state.cwnd == 1.0
    assert state.ssthresh == 8.0


@pytest.mark.xfail(strict=False, reason="Human-owned update_cwnd is intentionally unimplemented")
def test_slow_start_reference_trace():
    sender = TCPSender(RenoCongestionControl(SenderState(cwnd=1.0, ssthresh=8.0)))
    recorder = CongestionTraceRecorder()
    for reference in SLOW_START_REFERENCE:
        point = sender.process(event(reference["time"], CongestionEventKind.ACK))
        recorder.record(point)
    assert [point.cwnd for point in recorder.points] == [2.0, 3.0, 4.0]


@pytest.mark.xfail(strict=False, reason="Human-owned update_cwnd is intentionally unimplemented")
def test_timeout_updates_threshold_and_window():
    policy = RenoCongestionControl(SenderState(cwnd=8.0, ssthresh=8.0))
    policy.handle_event(event(3.0, CongestionEventKind.TIMEOUT))
    assert policy.state.cwnd == 1.0
    assert policy.state.ssthresh == 4.0


@pytest.mark.xfail(strict=False, reason="Human-owned update_cwnd is intentionally unimplemented")
def test_boundary_ack_at_ssthresh_enters_congestion_avoidance():
    policy = RenoCongestionControl(SenderState(cwnd=8.0, ssthresh=8.0))
    policy.handle_event(event(2.0, CongestionEventKind.ACK))
    assert policy.state.cwnd == pytest.approx(8.125)


@pytest.mark.xfail(strict=False, reason="Human-owned update_cwnd is intentionally unimplemented")
def test_triple_duplicate_ack_reference():
    policy = RenoCongestionControl(SenderState(cwnd=8.0, ssthresh=8.0))
    policy.handle_event(event(4.0, CongestionEventKind.TRIPLE_DUPLICATE_ACK))
    assert policy.state.cwnd == 4.0
    assert policy.state.ssthresh == 4.0


def test_trace_csv_has_stable_columns():
    csv_text = CongestionTraceRecorder().to_csv()
    assert csv_text == "time,event,cwnd,ssthresh,duplicate_ack_count\n"
