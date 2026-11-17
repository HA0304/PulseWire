from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from itertools import count
from typing import Callable, Iterable, Iterator


class StreamStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


@dataclass(frozen=True)
class EventBatch:
    protocol: str = "pulsewire.events"
    version: int = 1
    sequence: int = 0
    events: tuple[dict[str, object], ...] = ()
    dropped: int = 0


class BoundedEventBuffer:
    def __init__(self, limit: int = 4096):
        if limit <= 0:
            raise ValueError("stream buffer limit must be positive")
        self.limit = limit
        self._buffer: deque[dict[str, object]] = deque(maxlen=limit)
        self.dropped = 0

    def append(self, event: dict[str, object]) -> None:
        if len(self._buffer) == self.limit:
            self.dropped += 1
        self._buffer.append(event)

    def extend(self, events: Iterable[dict[str, object]]) -> int:
        dropped_before = self.dropped
        for event in events:
            self.append(event)
        return self.dropped - dropped_before

    def drain(self) -> tuple[dict[str, object], ...]:
        events = tuple(self._buffer)
        self._buffer.clear()
        return events

    def __len__(self) -> int:
        return len(self._buffer)


@dataclass
class StreamSession:
    batch_size: int = 256
    buffer_limit: int = 4096
    status: StreamStatus = StreamStatus.STOPPED
    sequence: int = 0
    buffer: BoundedEventBuffer = field(default_factory=lambda: BoundedEventBuffer(4096))

    def __post_init__(self):
        if not 1 <= self.batch_size <= 4096:
            raise ValueError("batch_size must be between 1 and 4096")
        if not 1 <= self.buffer_limit <= 100000:
            raise ValueError("buffer_limit must be between 1 and 100000")
        self.buffer = BoundedEventBuffer(self.buffer_limit)

    def start(self) -> None:
        self.status = StreamStatus.RUNNING

    def pause(self) -> None:
        if self.status is StreamStatus.RUNNING:
            self.status = StreamStatus.PAUSED

    def resume(self) -> None:
        if self.status is StreamStatus.PAUSED:
            self.status = StreamStatus.RUNNING

    def stop(self) -> None:
        self.status = StreamStatus.STOPPED
        self.buffer._buffer.clear()

    def next_batch(self, events: Iterable[dict[str, object]]) -> EventBatch:
        dropped = self.buffer.extend(events)
        selected = self.buffer.drain()[:self.batch_size]
        batch = EventBatch(
            sequence=self.sequence,
            events=selected,
            dropped=dropped,
        )
        self.sequence += 1
        return batch


def batch_events(
    events: Iterable[dict[str, object]],
    batch_size: int = 256,
) -> Iterator[EventBatch]:
    if not 1 <= batch_size <= 4096:
        raise ValueError("batch_size must be between 1 and 4096")
    iterator = iter(events)
    sequence = 0
    while True:
        batch = []
        for _ in range(batch_size):
            try:
                batch.append(next(iterator))
            except StopIteration:
                if batch:
                    yield EventBatch(sequence=sequence, events=tuple(batch))
                return
        yield EventBatch(sequence=sequence, events=tuple(batch))
        sequence += 1
