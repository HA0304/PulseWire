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
