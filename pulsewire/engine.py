import heapq
import random
from collections import deque
from pulsewire.models import Packet, SimulationConfig
from pulsewire.events import Event, EventKind


class SimulationEngine:
    """Discrete-event simulation engine for the PulseWire packet network."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.bandwidth_bps = config.bandwidth_mbps * 1_000_000
        self.latency_s = config.latency_ms / 1000.0
        self.reverse_latency_s = self.latency_s  # Simplified: reverse ACK propagation = forward latency
        self.bit_size = config.packet_size_bytes * 8
        self.transmission_delay_s = self.bit_size / self.bandwidth_bps
        self.rng = random.Random(config.random_seed)
        
        # Event heap for discrete-event engine
        self._event_heap = []
        
        # State
        self.queue = deque()  # FIFO queue of Packet objects
        self.current_transmission = None  # Packet currently being transmitted
        self.next_seq = 0
        
        # Metrics counters
        self.packets_generated = 0
        self.packets_delivered = 0
        self.queue_dropped = 0
        self.random_losses = 0
        self.in_flight_or_queued = 0  # packets still in system (not delivered, not dropped, not lost)
        
        # Event log for CSV export
        self._event_log = []

    def _reset(self):
        """Reset engine state for a new simulation."""
        self.queue.clear()
        self.current_transmission = None
        self.next_seq = 0
        self.packets_generated = 0
        self.packets_delivered = 0
        self.queue_dropped = 0
        self.random_losses = 0
        self.in_flight_or_queued = 0
        self._event_log.clear()
        self._event_heap.clear()

    def _schedule_initial_arrivals(self, horizon_s: float):
        """Generate initial packet arrivals up to simulation horizon."""
        num_packets = int(round(self.config.rate_packets_per_sec * horizon_s))
        for i in range(num_packets):
            arrival_time = i / self.config.rate_packets_per_sec
            packet = Packet(
                seq=self.next_seq,
                size_bytes=self.config.packet_size_bytes,
                generation_time=arrival_time,
                arrival_time=arrival_time
            )
            self.queue.append(packet)
            self.next_seq += 1
            self.packets_generated += 1
            self.in_flight_or_queued += 1
            self._event_log.append((arrival_time, packet.seq, "PACKET_ARRIVAL"))

    def _apply_random_loss(self) -> bool:
        """Apply random channel loss to a packet starting transmission. Returns True if lost."""
        lost = self.rng.random() < self.config.loss_probability
        if lost:
            self.random_losses += 1
            self.in_flight_or_queued -= 1
        return lost

    def _enqueue_or_drop(self, packet: Packet):
        """Enqueue packet or drop due to buffer overflow."""
        if len(self.queue) < self.config.buffer_size:
            self.queue.append(packet)
            # Packet is already marked as enqueued implicitly via being in queue
        else:
            # Drop packet (overflow)
            packet.dropped = True
            self.queue_dropped += 1
            self.in_flight_or_queued -= 1

    def _start_transmission(self, packet: Packet, current_time: float):
        """Start transmitting a packet on the link."""
        packet.transmission_start = current_time
        packet.transmission_finish = current_time + self.transmission_delay_s
        packet.enqueued = True

    def _process_packet_arrival(self, packet: Packet):
        """Handle PACKET_ARRIVAL event."""
        self._enqueue_or_drop(packet)
        # If packet wasn't dropped, schedule transmission if link is idle
        # and there are packets in queue
        if packet not in self.queue and not packet.dropped:
            # Packet was enqueued, check if we can start transmission
            self._try_start_transmission()

    def _try_start_transmission(self):
        """Attempt to start transmitting the next packet from the queue."""
        if self.current_transmission is not None or not self.queue:
            return
        
        # Take head of queue
        next_packet = self.queue.popleft()
        self._start_transmission(next_packet, event_time=self._current_time)
        
        # Mark as starting transmission
        # Transmission will complete at transmission_finish time
        # Schedule TRANSMISSION_COMPLETE event
        heapq.heappush(self._event_heap, Event(
            kind=EventKind.TRANSMISSION_COMPLETE,
            time=next_packet.transmission_finish,
            seq=next_packet.seq
        ))
        
        # Also apply random loss at transmission start
        if self._apply_random_loss():
            # Packet randomly lost - it won't be delivered
            pass  # already decremented in_flight_or_queued via apply_random_loss
        else:
            # Mark that this packet is now in flight
            pass  # tracked via in_flight_or_queued

    def _process_transmission_complete(self, packet: Packet):
        """Handle TRANSMISSION_COMPLETE event - schedule delivery and ACK."""
        if self.current_transmission is None:
            # This packet was the one being transmitted; mark it complete
            self.current_transmission = None
        
        # Schedule PACKET_DELIVERED after propagation delay
        delivery_time = packet.transmission_finish + self.latency_s
        heapq.heappush(self._event_heap, Event(
            kind=EventKind.PACKET_DELIVERED,
            time=delivery_time,
            seq=packet.seq
        ))
        self._event_log.append((delivery_time, packet.seq, "PACKET_DELIVERED"))
        
        # Schedule ACK arrival after reverse propagation
        ack_time = delivery_time + self.reverse_latency_s
        heapq.heappush(self._event_heap, Event(
            kind=EventKind.ACK_ARRIVAL,
            time=ack_time,
            seq=packet.seq
        ))
        self._event_log.append((ack_time, packet.seq, "ACK_ARRIVAL"))
        
        # Mark packet as delivered in flight count
        # (already handled when we process PACKET_DELIVERED event)
        self.current_transmission = None
        
        # Try to start next packet from queue
        self._try_start_transmission()

    def _process_packet_delivered(self, packet: Packet):
        """Handle PACKET_DELIVERED event."""
        self.packets_delivered += 1
        self.in_flight_or_queued -= 1
        packet.delivery_time = packet.transmission_finish + self.latency_s
        packet.delivered = True

    def _process_ack_arrival(self, packet: Packet):
        """Handle ACK_ARRIVAL event."""
        packet.acked = True

    def _process_event(self, event: Event):
        """Process a single event from the heap."""
        packet = event.payload if hasattr(event, 'payload') else None
        
        if event.kind == EventKind.PACKET_ARRIVAL:
            # Create packet reference for event payload
            if packet is None:
                packet = Packet(seq=event.seq, size_bytes=self.config.packet_size_bytes)
            self._process_packet_arrival(packet)
        
        elif event.kind == EventKind.TRANSMISSION_COMPLETE:
            if packet is None:
                # Look up by seq in queue or current_transmission
                packet = self._find_packet_by_seq(event.seq)
            self._process_transmission_complete(packet)
        
        elif event.kind == EventKind.PACKET_DELIVERED:
            if packet is None:
                packet = self._find_packet_by_seq(event.seq)
            self._process_packet_delivered(packet)
        
        elif event.kind == EventKind.ACK_ARRIVAL:
            if packet is None:
                packet = self._find_packet_by_seq(event.seq)
            self._process_ack_arrival(packet)
        
        else:
            raise ValueError(f"Unknown event kind: {event.kind}")

    def _find_packet_by_seq(self, seq: int) -> Packet:
        """Find packet by sequence number."""
        for p in self.queue:
            if p.seq == seq:
                return p
        # Also check currently transmitting
        if self.current_transmission and self.current_transmission.seq == seq:
            return self.current_transmission
        # Check delivered packets (we need to track delivered too)
        # For now, return None or raise
        raise ValueError(f"Packet with seq={seq} not found")

    def run(self, horizon_s: float = None) -> 'SimulationMetrics':
        """Run the simulation for the given horizon (defaults to config)."""
        if horizon_s is None:
            horizon_s = self.config.simulation_horizon_seconds
        
        self._reset()
        self._schedule_initial_arrivals(horizon_s)
        
        # Initialize event heap with all generated events
        # Already have events in _event_heap from initial arrivals scheduling
        # But we also need TRANSMISSION_COMPLETE, PACKET_DELIVERED, ACK_ARRIVAL
        # Let's rethink: initial arrivals create queue packets, but transmission starts
        # need to be triggered from the arrival or from when link is idle
        
        # Re-init event heap and push all events properly
        self._event_heap.clear()
        
        # The initial queue packets need arrival events scheduled
        for i in range(len(self._event_log)):
            # We need to properly schedule events
            pass
        
        # Better approach: schedule all events properly on startup
        # First, schedule initial packet arrivals
        self._schedule_initial_arrivals(horizon_s)
        
        # Now, schedule transmissions based on queue state
        # and process events until horizon exceeded
        
        # Actually, let's restructure: The event heap starts with PACKET_ARRIVAL events
        # But we already added packets to queue manually. We need to trigger processing.
        # Let me use a different approach: schedule all arrivals as events first.
        
        # Reset and redo
        self._reset()
        
        # Schedule arrivals at regular intervals
        num_packets = int(round(self.config.rate_packets_per_sec * horizon_s))
        for i in range(num_packets):
            arrival_time = i / self.config.rate_packets_per_sec
            heapq.heappush(self._event_heap, Event(
                kind=EventKind.PACKET_ARRIVAL,
                time=arrival_time,
                seq=self.next_seq + i,
                payload=None  # We'll create packet at arrival time
            ))
        
        # Process events until horizon
        while self._event_heap and self._event_heap[0].time <= horizon_s:
            event = heapq.heappop(self._event_heap)
            
            # Track event for logging
            self._event_log.append((event.time, event.seq, event.kind.name))
            
            # Dispatch to handler
            if event.kind == EventKind.PACKET_ARRIVAL:
                packet = Packet(seq=event.seq, size_bytes=self.config.packet_size_bytes,
                               generation_time=event.time, arrival_time=event.time)
                self._process_packet_arrival(packet)
            elif event.kind == EventKind.TRANSMISSION_COMPLETE:
                packet = self._find_packet_by_seq(event.seq)
                self._process_transmission_complete(packet)
            elif event.kind == EventKind.PACKET_DELIVERED:
                packet = self._find_packet_by_seq(event.seq)
                self._process_packet_delivered(packet)
            elif event.kind == EventKind.ACK_ARRIVAL:
                packet = self._find_packet_by_seq(event.seq)
                self._process_ack_arrival(packet)
        
        # Compute and return metrics
        return self._compute_metrics()

    def _compute_metrics(self) -> 'SimulationMetrics':
        """Compute final metrics after simulation run."""
        generated = self.packets_generated
        delivered = self.packets_delivered
        dropped = self.queue_dropped
        lost = self.random_losses
        in_flight = self.in_flight_or_queued
        
        # Conservation check
        if generated != (delivered + dropped + lost + in_flight):
            print(f"WARNING: Conservation check failed: "
                  f"generated={generated} != delivered={delivered}+dropped={dropped}+lost={lost}+in_flight={in_flight}")
        
        # Average one-way latency in ms (over delivered packets)
        avg_latency = 0.0
        if delivered > 0:
            # Collect latencies from delivered packets
            latencies = []
            for p in self.queue:
                if p.delivery_time is not None and p.arrival_time is not None:
                    latencies.append((p.delivery_time - p.arrival_time) * 1000)
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        
        # Average RTT in ms (over delivered packets)
        avg_rtt = 0.0
        if delivered > 0:
            # Collect RTTs - measured from generation to ACK arrival
            rtts = []
            for p in self.queue:
                if p.delivery_time is not None and p.ack_time is not None:
                    rtts.append((p.ack_time - p.generation_time) * 1000)
            avg_rtt = sum(rtts) / len(rtts) if rtts else 0.0
        
        # Throughput in Mbps
        avg_bits_per_packet = float(self.config.packet_size_bytes * 8)
        if horizon_s > 0 and delivered > 0:
            total_delivered_bits = delivered * avg_bits_per_packet
            throughput_mbps = (total_delivered_bits / horizon_s) / 1_000_000
        else:
            throughput_mbps = 0.0
        
        # Store metrics
        self.metrics = SimulationMetrics(
            generated=generated,
            delivered=delivered,
            dropped=dropped,
            random_losses=lost,
            in_flight=in_flight,
            avg_one_way_latency_ms=avg_latency,
            avg_rtt_ms=avg_rtt,
            throughput_mbps=throughput_mbps
        )
        
        return self.metrics

    def get_event_log(self) -> list:
        """Return event log for CSV export."""
        return self._event_log


class SimulationMetrics:
    """Container for simulation metrics."""
    
    def __init__(self, generated, delivered, dropped, random_losses, in_flight, 
                 avg_one_way_latency_ms, avg_rtt_ms, throughput_mbps):
        self.generated = generated
        self.delivered = delivered
        self.dropped = dropped
        self.random_losses = random_losses
        self.in_flight = in_flight
        self.avg_one_way_latency_ms = avg_one_way_latency_ms
        self.avg_rtt_ms = avg_rtt_ms
        self.throughput_mbps = throughput_mbps
    
    def __repr__(self):
        return (f"SimulationMetrics(generated={self.generated}, delivered={self.delivered}, "
                f"dropped={self.dropped}, random_losses={self.random_losses}, "
                f"in_flight={self.in_flight}, avg_latency_ms={self.avg_one_way_latency_ms:.2f}, "
                f"avg_rtt_ms={self.avg_rtt_ms:.2f}, throughput_mbps={self.throughput_mbps:.2f})")