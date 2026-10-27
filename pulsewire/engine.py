import heapq
import random
from collections import deque
from dataclasses import dataclass

from .events import Event, EventKind
from .models import Packet, SimulationConfig


@dataclass
class SimulationResult:
    packets: list[Packet]
    event_trace: list[dict[str, object]]
    queue_occupancy: list[tuple[float, int]]


class SimulationEngine:
    def __init__(self, config: SimulationConfig):
        config.validate()
        self.config = config
        self._events: list[Event] = []
        self._sequence = 0
        self._clock = 0.0
        self._queue: deque[Packet] = deque()
        self._packets: dict[int, Packet] = {}
        self._transmitting: Packet | None = None
        self._rng = random.Random(config.random_seed)
        self._trace: list[dict[str, object]] = []
        self._occupancy: list[tuple[float, int]] = []

    @property
    def transmission_delay_seconds(self) -> float:
        return self.config.packet_size_bytes * 8 / (self.config.bandwidth_mbps * 1_000_000)

    def schedule(self, kind: EventKind, time: float, packet_id: int | None = None) -> None:
        event = Event(time, self._sequence, kind, packet_id)
        self._sequence += 1
        heapq.heappush(self._events, event)

    def _record(self, event: Event) -> None:
        self._trace.append({
            "time": event.time,
            "sequence_number": event.sequence_number,
            "event": event.kind.name,
            "packet_id": event.packet_id,
        })

    def _record_occupancy(self) -> None:
        self._occupancy.append((self._clock, len(self._queue)))

    def _start_next_transmission(self) -> None:
        if self._transmitting is not None or not self._queue:
            return
        packet = self._queue.popleft()
        self._transmitting = packet
        packet.transmission_start = self._clock
        packet.status = "transmitting"
        if self._rng.random() < self.config.loss_probability:
            packet.status = "random_loss"
            self._transmitting = None
            self._record_occupancy()
            self._start_next_transmission()
            return
        self.schedule(
            EventKind.TRANSMISSION_COMPLETE,
            self._clock + self.transmission_delay_seconds,
            packet.packet_id,
        )
        self._record_occupancy()

    def _handle(self, event: Event) -> None:
        packet = self._packets.get(event.packet_id) if event.packet_id is not None else None
        if event.kind is EventKind.PACKET_ARRIVAL:
            assert packet is not None
            packet.status = "queued"
            if len(self._queue) >= self.config.buffer_size:
                packet.status = "queue_drop"
            else:
                self._queue.append(packet)
                self._start_next_transmission()
            self._record_occupancy()
        elif event.kind is EventKind.TRANSMISSION_COMPLETE:
            assert packet is not None
            packet.transmission_complete = self._clock
            self._transmitting = None
            packet.status = "in_flight"
            self.schedule(EventKind.PACKET_DELIVERED, self._clock + self.config.latency_ms / 1000, packet.packet_id)
            self._start_next_transmission()
        elif event.kind is EventKind.PACKET_DELIVERED:
            assert packet is not None
            packet.delivery_time = self._clock
            packet.status = "delivered"
            self.schedule(EventKind.ACK_ARRIVAL, self._clock + self.config.latency_ms / 1000, packet.packet_id)
        elif event.kind is EventKind.ACK_ARRIVAL:
            assert packet is not None
            packet.acknowledgment_time = self._clock
            packet.status = "acknowledged"

    def run(self) -> SimulationResult:
        self._events.clear()
        self._sequence = 0
        self._clock = 0.0
        self._queue.clear()
        self._packets.clear()
        self._transmitting = None
        self._rng = random.Random(self.config.random_seed)
        self._trace.clear()
        self._occupancy.clear()
        if self.config.rate_packets_per_sec:
            count = int(self.config.rate_packets_per_sec * self.config.simulation_horizon_seconds)
            for packet_id in range(count):
                creation_time = packet_id / self.config.rate_packets_per_sec
                packet = Packet(packet_id, "source", "destination", self.config.packet_size_bytes, creation_time)
                self._packets[packet_id] = packet
                self.schedule(EventKind.PACKET_ARRIVAL, creation_time, packet_id)
        while self._events:
            event = heapq.heappop(self._events)
            self._clock = event.time
            self._record(event)
            self._handle(event)
        return SimulationResult(list(self._packets.values()), list(self._trace), list(self._occupancy))
