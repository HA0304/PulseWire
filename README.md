# PulseWire

PulseWire is a deterministic, discrete-event packet network simulator for a
single FIFO-buffered link. It models packet generation, drop-tail queueing,
link serialization, propagation, channel loss, and simplified acknowledgments.

## Requirements

- Python 3.12+
- `pytest`
- `streamlit`

Install dependencies in a virtual environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Run it

```bash
python -m pulsewire --help
python -m pulsewire
python -m streamlit run dashboard.py
python -m pytest -q
```

The CLI uses a reproducible demo configuration. The dashboard exposes the
same configuration controls and renders only data returned by the simulator,
including KPIs, queue occupancy, event timeline, packet outcomes, and CSV
export.

## Architecture

`SimulationEngine` owns a `heapq` event queue ordered by `(time,
sequence_number)`. Packet arrivals enter a finite FIFO queue. A single
transmission can be active at a time, and its duration is:

```text
packet_size_bytes * 8 / (bandwidth_mbps * 1_000_000)
```

Successful transmissions propagate to the destination and schedule an ACK
after one additional propagation delay. Thus, for a delivered packet:

```text
RTT = transmission delay + 2 * propagation delay
```

ACK serialization and reverse-link congestion are intentionally outside this
simplified model. Queue overflow and random channel loss remain separate
packet outcomes. A fixed seed makes loss decisions repeatable.

## CI/CD

GitHub Actions runs on pushes and pull requests. It installs Python 3.12,
installs `requirements.txt`, runs the complete test suite, and verifies CLI
startup. The workflow is validation-only; deployment and cloud infrastructure
are intentionally out of scope.

## Project map

```text
pulsewire/models.py   Packet and SimulationConfig
pulsewire/events.py   Event kinds and deterministic heap entries
pulsewire/engine.py   Discrete-event simulation
pulsewire/metrics.py  KPI calculation
dashboard.py          Streamlit UI
tests/                Deterministic acceptance and regression tests
```

## November backlog walkthrough

The dashboard includes three reproducible experiment presets:

1. **Queue overflow**: 1 Mbps, 1-packet buffer, 1,000 packets/second.
2. **High RTT**: 200 ms one-way propagation delay with low offered load.
3. **Packet loss**: 100% channel loss with seed `42`.

Run the dashboard and select a preset from the sidebar:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run dashboard.py
```

Use **Start live stream**, **Pause**, **Resume**, or **Stop** to inspect bounded
event batches. Live data is sampled in groups of 256 events and the UI retains
at most 4,096 rows.

The topology editor supports node creation and movement, directed link creation
and selection, removal, and validation of missing, duplicate, and self-linked
nodes or links. Coordinates are presentation data and are not simulation inputs.

The congestion-window chart is intentionally empty until
`RenoCongestionControl.update_cwnd()` is implemented; no cwnd values are
fabricated. Slow start and fast loss behavior remain the human-owned Stage 2
algorithm scope.

## Stage 2 congestion-control scaffolding

Stage 2 adds an independent sender policy boundary in
`pulsewire/congestion.py`, event integration in `pulsewire/sender.py`, and
trace/CSV support in `pulsewire/trace.py`. The `RenoCongestionControl` state
contains `cwnd`, `ssthresh`, duplicate-ACK count, and ACK count.

The educational model uses ACK, timeout, and triple-duplicate-ACK events.
It intentionally does not model delayed ACKs, receiver windows, retransmitted
segments, ACK loss, or a reverse-link queue. `cwnd` is measured in packets,
and congestion avoidance uses an additive-increase interpretation.

`RenoCongestionControl.update_cwnd()` is intentionally unimplemented. The
human developer must implement it before the Stage 2 reference tests pass.
The tests in `tests/test_congestion_control.py` are expected to fail at that
hook until then; the Stage 1 regression suite remains independently runnable.
