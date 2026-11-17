# PulseWire performance evidence

Run:

```bash
python -m pulsewire.benchmark --repeats 3
```

The benchmark uses the same Python process and fixed seed. Each target is
measured with `time.perf_counter()` and `tracemalloc`. Event count includes
packet arrivals, transmissions, deliveries, and ACK arrivals.

Observed locally on the development environment with one repetition:

| Packet target | Event count | Median/elapsed seconds | Events/second | Peak traced bytes |
|---|---:|---:|---:|---:|
| 1,000 | 4,000 | 0.1473 | 27,159 | 1,345,600 |
| 10,000 | 40,000 | 1.0751 | 37,207 | 4,775,920 |
| 100,000 | 400,000 | 10.7164 | 37,326 | 42,696,968 |

UI transport batches 256 events and retains only 4,096 UI rows. The engine
event history is configurable and bounded. The 100,000-packet run remains
expensive because the current process retains packet objects for metrics;
distributed workers and shared session storage are not implemented.

## Future worker introduction

The engine, transport batches, topology model, and Streamlit UI are separated.
A future independent worker could consume a versioned run request and return
batched event messages; the session object would then hold only bounded UI
state. Shared session storage would require an external stateless-session store,
but Redis, Kubernetes, Kafka, and distributed databases are intentionally not
added now.
