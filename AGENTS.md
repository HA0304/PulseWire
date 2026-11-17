## Stage 2 — TCP Congestion Control

### Project Context
PulseWire is a discrete-event packet network simulator with packets, queues, link capacity, RTT, packet loss, and measurable simulation results.

Extend the existing architecture. Do not rewrite working Stage 1 functionality.

### Development Rules
1. Inspect the existing repository before making changes.
2. Preserve existing APIs, tests, and architectural conventions.
3. Use modular components with clear responsibilities.
4. Keep congestion control independent of packet scheduling and network topology.
5. Use deterministic simulations with configurable random seeds.
6. Add unit tests and regression tests for every new behavior.
7. Avoid unnecessary dependencies and abstractions.
8. Make small, meaningful commits after each completed milestone.
9. Never fabricate simulation results or claim tests passed without running them.

### Human-Owned Implementation — STRICT
The developer must personally implement the congestion-window update algorithm.

AI MUST NOT:
- Generate the final implementation of `update_cwnd()`.
- Automatically fill in the function body.
- Modify the human-written congestion-window update logic.
- Replace the implementation with an external TCP library.

AI MAY:
- Explain TCP congestion-control concepts.
- Create interfaces, type definitions, and scaffolding.
- Implement the simulation integration around the function.
- Generate tests and expected trace fixtures.
- Review the human-written implementation after completion.
- Identify bugs without directly rewriting the protected function.

Create a clearly marked TODO placeholder for the human implementation.

### TCP Model
Implement a simplified, explicitly documented TCP Reno-style model supporting:
- Slow start
- Congestion avoidance
- Slow-start threshold (`ssthresh`)
- Timeout-based loss response
- Triple-duplicate-ACK loss response
- Congestion-window evolution over time

Distinguish between educational simplifications and actual TCP Reno behavior.

### Architecture
Separate:
- TCP sender state
- Congestion-control policy
- ACK and loss events
- Existing network simulation engine
- Trace recording and export
- Metrics and visualization

Do not implement an entirely new network engine.

### Testing Requirements
- Unit tests for congestion-window transitions
- Hand-calculated reference traces
- Boundary tests at `cwnd == ssthresh`
- Timeout and duplicate-ACK scenarios
- Deterministic integration tests
- Regression tests for Stage 1

### Definition of Done
- All required tests pass.
- Human-written congestion-control logic remains intact.
- Simulation traces match reference calculations.
- Existing Stage 1 features still work.
- Results can be inspected as a table or CSV.
- Documentation explains assumptions and limitations.
- Changes are divided into reviewable Git commits.