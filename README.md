# PulseWire: Discrete-Event Packet Network Simulator

## Architecture

PulseWire simulates a single FIFO-buffered wired link with drop-tail congestion behavior. The core data flow:

1. **Packet generation**: Packets are generated at a configurable rate (packets/second) with a fixed payload size
2. **Queueing**: Packets enter a finite FIFO queue (drop-tail when full)
3. **Serialization**: One link, bandwidth-limited. Transmission delay = packet_bits / bandwidth_bits_per_second
4. **Propagation**: Fixed latency after serialization completes
5. **ACK reverse path**: Simplified reverse propagation with ACK frames typically much smaller than data packets
6. **Random loss**: Configurable per-packet loss probability independent of queue behavior
7. **Metrics**: Delivery ratio, throughput, latency, RTT, queue overflow, random losses

## Event Kinds

| Kind | Description |
|------|-------------|
| `PACKET_ARRIVAL` | A new packet arrives at the network input |
| `TRANSMISSION_COMPLETE` | Finished serializing a packet onto the link |
| `PACKET_DELIVERED` | Packet propagates to receiver after propagation delay |
| `ACK_ARRIVAL` | ACK received back at the sender |

## Core Classes

- `Packet`: data model with payload, timestamps, sequence number
- `Event`: heap entry ordered by `(time, sequence_number)` for deterministic tie-breaking
- `SimulationEngine`: discrete-event engine using `heapq`
- `SimulationMetrics`: KPI calculation and conservation invariants

## CLI

```
python -m pulsewire --help
```

See reproducible demo below.

## Dashboard

Streamlit app with sliders for all configuration parameters, a Run button, KPI display, and charts for packet delivery and queue occupancy.

## Citation / Reference

Built as a minimal, deterministic, educational packet network simulator using only Python standard library + streamlit + pytest.

---

## Example Output

```
$ python -m pulsewire --scenario demo
PulseWire Discrete-Event Packet Network Simulator
================================================
Configuration: bandwidth=10Mbps, latency=10ms, buffer=10, packet_size=500, rate=0.5pkt/s, loss=0.0
Simulation: 100.0s horizon, seed=42

Packets generated: 50
Packets delivered: 50
Queue drops: 0
Random losses: 0
Delivery ratio: 1.000
Throughput: 5.00 Mbps
Average one-way latency: 10.50 ms
Average RTT: 21.00 ms
Packets in flight or queued: 0

Conservation check: generated(50) = delivered(50) + dropped(0) + lost(0) + in_flight(0)
```