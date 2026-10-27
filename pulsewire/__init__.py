from pulsewire.models import Packet, SimulationConfig
from pulsewire.events import Event, EventKind
from pulsewire.engine import SimulationEngine


def create_engine(config: SimulationConfig) -> SimulationEngine:
    """Factory function to create a SimulationEngine from a config."""
    return SimulationEngine(config)
