# Development log

## Time tracking

- AI-assisted implementation time: record manually.
- Independent implementation time: record manually.
- Testing and debugging time: record manually.

## Engineering decisions

- Used `heapq` with an explicit monotonically increasing sequence number for
  deterministic ordering of simultaneous events.
- Kept a single serialized forward link and modeled ACKs as reverse
  propagation only.
- Used standard-library data structures for the simulator and kept Streamlit
  limited to presentation.
- Seeded a dedicated `random.Random` instance so simulations do not mutate
  global random state.

## Bugs discovered and corrected

- Replaced the incomplete scheduler implementation with packet lifecycle
  tracking that distinguishes queue drops, channel losses, delivery, and ACK.
- Added analytical transmission-delay and RTT checks.
- Added validation for non-finite numeric configuration values and zero-rate
  and zero-buffer regressions.

## Commands executed

The implementation was verified with the project virtual environment using:

- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m pulsewire --help`
- `.venv/bin/python -m pulsewire --horizon 1`

## Feature status

Completed: simulator core, deterministic tests, CLI, Streamlit dashboard,
metrics, CSV export, CI workflow, and documentation.

Deferred: deployment to a cloud provider, because the requirements explicitly
limit CI/CD to GitHub Actions validation and no remote repository was
authorized.
