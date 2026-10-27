import heapq
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class EventKind(Enum):
    PACKET_ARRIVAL = auto()
    TRANSMISSION_COMPLETE = auto()
    PACKET_DELIVERED = auto()
    ACK_ARRIVAL = auto()


@dataclass
class Event:
    kind: EventKind
    time: float
    seq: int
    payload: Any = None

    def __lt__(self, other: "Event") -> bool:
        return (self.time, self.seq) < (other.time, other.seq)


def push_event(heap, event: Event):
    heapq.heappush(heap, event)


def pop_event(heap):
    return heapq.heappop(heap)