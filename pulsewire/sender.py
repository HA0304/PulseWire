from dataclasses import dataclass

from .congestion import CongestionEvent, RenoCongestionControl, SenderState


@dataclass
class SenderTracePoint:
    time: float
    event: str
    cwnd: float
    ssthresh: float
    duplicate_ack_count: int


class TCPSender:
    """Thin event integration layer around the congestion-control policy."""

    def __init__(self, policy: RenoCongestionControl | None = None):
        self.policy = policy or RenoCongestionControl()

    @property
    def state(self) -> SenderState:
        return self.policy.state

    def process(self, event: CongestionEvent) -> SenderTracePoint:
        self.policy.handle_event(event)
        state = self.state
        return SenderTracePoint(
            time=event.time,
            event=event.kind.value,
            cwnd=state.cwnd,
            ssthresh=state.ssthresh,
            duplicate_ack_count=state.duplicate_ack_count,
        )
