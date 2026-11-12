from dataclasses import dataclass
from enum import Enum


class CongestionEventKind(str, Enum):
    ACK = "ack"
    TIMEOUT = "timeout"
    TRIPLE_DUPLICATE_ACK = "triple_duplicate_ack"


@dataclass(frozen=True)
class CongestionEvent:
    time: float
    kind: CongestionEventKind
    acknowledged_packets: int = 1


@dataclass
class SenderState:
    cwnd: float = 1.0
    ssthresh: float = 8.0
    duplicate_ack_count: int = 0
    acknowledged_packets: int = 0

    def validate(self) -> None:
        if self.cwnd <= 0:
            raise ValueError("cwnd must be positive")
        if self.ssthresh <= 0:
            raise ValueError("ssthresh must be positive")
        if self.duplicate_ack_count < 0:
            raise ValueError("duplicate_ack_count must be nonnegative")
        if self.acknowledged_packets < 0:
            raise ValueError("acknowledged_packets must be nonnegative")


class RenoCongestionControl:
    """Educational Reno-style policy boundary.

    The state transitions belong in ``update_cwnd``. That method is deliberately
    left for the human developer to implement.
    """

    def __init__(self, state: SenderState | None = None):
        self.state = state or SenderState()
        self.state.validate()

    def update_cwnd(self, event: CongestionEvent) -> None:
        # HUMAN IMPLEMENTATION REQUIRED: implement the Stage 2 Reno algorithm.
        raise NotImplementedError("Human implementation required: update_cwnd")

    def handle_event(self, event: CongestionEvent) -> None:
        self.update_cwnd(event)
