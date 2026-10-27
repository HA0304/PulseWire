# opencode Agents: Project Guidelines

## Goal
Build PulseWire, a discrete-event packet network simulator, with a Streamlit dashboard, CLI, documented architecture, GitHub Actions CI, and meaningful Git commits.

## Stack
- Python 3.12+
- `heapq` for the min-event heap
- `pytest` for testing
- `streamlit` for the dashboard
- Standard library only (no external math/simulation packages)

## Project Structure
```
pulsewire/
  __init__.py
  __main__.py
  models.py
  events.py
  engine.py
  metrics.py
dashboard.py
tests/
.github/workflows/ci.yml
requirements.txt
.gitignore
README.md
AGENTS.md
```

## Mandatory Git Workflow
- **7 sequential milestones**; after each: run tests, review git diff/git status, commit only milestone-relevant files using conventional commit messages (`feat:`, `fix:`, `test:`, `chore:`, `ci:`, `docs:`).
- Never include unfinished or unrelated changes.
- Never squash commits into a single commit.
- Never create empty or artificial commits.
- Record the commit hash and tests run after each commit.
- Never commit secrets.
- Do not push or create a remote repository until explicitly approved.

## Milestone Payment/Completion Pattern
After EACH milestone:
1. Run relevant tests
2. Review git diff and git status
3. Commit only files belonging to that milestone
4. Use conventional commit messages
5. Never include unfinished or unrelated changes
6. Do not fabricate a successful test run
7. Preserve existing commit history

## Conventional Commit Examples
- `feat: add Packet data model`
- `fix: correct serialization delay calculation`
- `test: add event ordering tie-breaking test`
- `chore: update requirements.txt`
- `ci: add GitHub Actions workflow`
- `docs: add example simulation output to README`

## CLI Guidelines
- Entry point: `python -m pulsewire --help`
- Must support a reproducible demo scenario
- All config parameters should be adjustable via CLI flags or environment variables

## Dashboard Guidelines
- `streamlit run dashboard.py`
- All KPIs must come from the actual simulation engine, not hardcoded
- Sliders/inputs for: bandwidth, latency, buffer size, packet size, rate, loss probability, simulation horizon, random seed
- KPI display: packets generated, delivered, queue drops, random losses, delivery ratio, throughput, avg latency, avg RTT
- Charts: packet delivery over time, queue occupancy over time
- Table of packet events with CSV export

## Test Guidelines
- `pytest` discovery: `tests/` directory
- All tests must be deterministic (fixed random seed where stochasticity is involved)
- Conservation invariant test: generated = delivered + dropped + lost + in_flight_or_queued
- Event ordering tie-breaking test
- Edge case tests: zero bandwidth, 100% loss, empty buffer, etc.
- Repeatability test with same random seed

## Architecture Guidelines
- Separation of concerns: models (data), events (heap engine), engine (simulation logic), metrics (KPI extraction)
- Deterministic event execution: timestamps tie-breaking by sequence_number
- Document all assumptions (especially RTT model)
- Make invalid configurations raise clear errors

## Agent Instructions
- Follow the 7-milestone pattern strictly
- After each milestone, commit only the files belonging to that milestone
- Use `git diff` to verify only intended changes are present
- Report anything not verified
- If blocked, ask for clarification but try to proceed with the minimal working implementation