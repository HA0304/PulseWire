# PulseWire engineering notes

Keep the simulator deterministic and dependency-light. Changes to packet
semantics should include analytical tests, and all dashboard values must come
from `SimulationResult` or `Metrics`.

The supported verification commands are:

```bash
python -m pytest -q
python -m pulsewire --help
```

Use the seven existing milestone commits as the project history. Do not push
to a remote or create infrastructure without explicit approval.
