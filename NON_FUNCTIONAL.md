# Universal Performance, Reliability and Scalability Requirements

All projects must satisfy measurable nonfunctional requirements alongside their functional requirements.

## 1. User-perceived performance

- Prioritize fast interactions and responsive interfaces.
- Do not block the browser main thread with expensive computation.
- Avoid unnecessary React rerenders, repeated parsing and unbounded event processing.
- Use efficient data structures and algorithms appropriate to the workload.
- Move heavy CPU processing to Web Workers, worker threads or background jobs when justified.
- Use throttling, debouncing and batching where appropriate, without making direct manipulation feel delayed.
- Apply backpressure when incoming work exceeds processing capacity.
- Keep large datasets and simulation results bounded in memory.

Initial targets:
- Ordinary canvas interactions target 60 FPS on the development machine.
- Routine local UI actions target under 100 ms.
- Interactive main-thread tasks should avoid blocking for 50 ms or more.
- Non-AI API endpoints initially target p95 under 300 ms under a documented test workload.

These are targets, not guaranteed capacity claims.

## 2. Scalability and extensibility

Design for the possibility of tens of thousands of users in the future, without prematurely provisioning for them.

Requirements:
- Keep business logic separate from UI and transport layers.
- Prefer stateless request handlers where practical.
- Avoid relying on local process memory for shared production state.
- Use explicit interfaces around persistence, background jobs and external services.
- Design so that horizontal scaling can be introduced without rewriting core domain logic.
- Support pagination, bounded payloads, request limits and cancellation.
- Avoid O(n²) operations on frequently executed paths when a better practical approach exists.
- Avoid introducing distributed infrastructure until measurements justify it.

Do not claim support for a particular concurrency level without load-test evidence.

## 3. Reliability

- Handle timeouts, cancellation and connection failures.
- Validate all external inputs.
- Prevent uncontrolled memory growth.
- Use deterministic fixtures where possible.
- Ensure partial failures produce understandable errors.
- Provide health/readiness checks for server services.
- Preserve existing data formats and migrations.

## 4. Observability

Record useful development and production diagnostics:
- Operation latency and p95 latency where measurable.
- Error rates.
- Memory consumption.
- Processing throughput.
- Queue size and dropped events.
- External model latency and failures, where applicable.

Avoid logging API secrets, private documents or sensitive user content.

## 5. Testing and evidence

Create a small reproducible benchmark for each critical performance-sensitive operation.

Record:
- Hardware/runtime or deployment environment.
- Input size and test workload.
- Measurement methodology.
- Median, p95 and maximum latency where appropriate.
- Memory usage and detected bottlenecks.
- Known scaling limitations.

## 6. Engineering discipline

Do not optimize blindly.

First identify bottlenecks through profiling or a reproducible benchmark, then implement the simplest appropriate improvement.

Do not introduce Kubernetes, Redis, Kafka, microservices or distributed databases merely to appear scalable.

Every major feature should preserve existing performance and maintain a path to future scale.

Include performance regression checks for critical operations where practical.

Document results in docs/PERFORMANCE.md.

The implementation must remain deployable, maintainable and compatible with the December 10 release deadline.