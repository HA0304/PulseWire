# November 19 test handoff

## Simulation trace checks

- Run: `.venv/bin/python -m pytest -q tests/test_simulation.py`
- Verify event sequence keys are ordered by `(time, sequence_number)`.
- Verify deterministic replay for identical seed/configuration.
- Verify packet conservation:
  `generated = delivered + queue drops + random losses + in flight/queued`.

## RTT and cwnd correctness

- Stage 1 RTT is validated by the deterministic single-packet test.
- RTT uses transmission delay plus forward and reverse propagation delay.
- `RenoCongestionControl.update_cwnd()` remains human-owned and is deliberately
  unimplemented. Its trace/cwnd correctness cannot be marked complete until
  that method is implemented and `tests/test_congestion_control.py` passes.
- The dashboard leaves the cwnd chart empty to avoid fabricated values.

## Packet-loss behavior

- Run: `.venv/bin/python -m pytest -q tests/test_experiments.py`
- The Packet loss preset is 100% loss and should produce no deliveries.
- Queue overflow and random channel loss are separate outcomes.
- Verify seeded replay with loss probabilities `0`, `0.25`, and `1.0`.

## Event-stream interruption/reconnect

- Start the dashboard, select the live stream, then use Pause, Resume, and Stop.
- Verify event batching remains bounded and completed batches are not redrawn
  as thousands of independent Streamlit state updates.
- Streamlit owns the browser WebSocket connection. Exercise browser disconnect
  and reconnect manually: the Streamlit session should re-establish and not
  restart an existing simulation automatically.
- The bounded session buffer should never exceed 4,096 UI rows.

## Memory and throughput benchmarks

- Run: `.venv/bin/python -m pulsewire.benchmark --repeats 3`
- Record environment, median elapsed time, event throughput, and peak traced
  memory. Evidence is in `docs/PERFORMANCE.md`.
- Do not report benchmark targets as guaranteed capacity.

## Topology validation cases

- Run: `.venv/bin/python -m pytest -q tests/test_topology.py`
- Validate duplicate IDs, missing node references, self-links, duplicate
  directed links, nonpositive bandwidth, negative latency, negative buffers,
  and node removal while referenced.
- Verify layout coordinates are not passed to `SimulationConfig`.

## Reproducible deployment checks

Clean clone:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m pulsewire --help
.venv/bin/python -m streamlit run dashboard.py
```

GitHub Actions runs tests and verifies CLI and Streamlit startup. No cloud
deployment is claimed or configured. Future HTTP deployment should add a real
readiness endpoint and isolate each simulation session.
