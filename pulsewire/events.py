from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class EventKind(Enum):
    PACKET_ARRIVAL = auto()
    TRANSMISSION_COMPLETE = auto()
    PACKET_DELIVERED = auto()
    ACK_ARRIVAL = auto()


@dataclass(order=True)
class Event:
    time: float
    sequence_number: int
    kind: EventKind = field(compare=False)
    packet_id: int | None = field(default=None, compare=False)
    payload: Any = field(default=None, compare=False)
