import csv
import io

import streamlit as st

from pulsewire.engine import SimulationEngine
from pulsewire.metrics import calculate_metrics
from pulsewire.models import SimulationConfig


st.set_page_config(page_title="PulseWire", page_icon="📡", layout="wide")
st.title("PulseWire Network Simulator")
st.caption("Deterministic discrete-event packet simulation with FIFO drop-tail buffering.")

with st.sidebar:
    st.header("Network configuration")
    bandwidth = st.number_input("Bandwidth (Mbps)", min_value=0.01, value=10.0)
    latency = st.number_input("Propagation delay (ms)", min_value=0.0, value=10.0)
    buffer_size = st.number_input("Buffer capacity (packets)", min_value=0, value=10, step=1)
    packet_size = st.number_input("Packet size (bytes)", min_value=1, value=500, step=1)
    rate = st.number_input("Generation rate (packets/sec)", min_value=0.0, value=1.0)
    loss = st.slider("Channel loss probability", 0.0, 1.0, 0.0)
    horizon = st.number_input("Simulation horizon (seconds)", min_value=0.01, value=10.0)
    seed = st.number_input("Random seed", value=42, step=1)
    run = st.button("Run simulation", type="primary")

if run or "result" not in st.session_state:
    config = SimulationConfig(
        bandwidth_mbps=bandwidth,
        latency_ms=latency,
        buffer_size=int(buffer_size),
        packet_size_bytes=int(packet_size),
        rate_packets_per_sec=rate,
        loss_probability=loss,
        simulation_horizon_seconds=horizon,
        random_seed=int(seed),
    )
    try:
        st.session_state.result = SimulationEngine(config).run()
        st.session_state.metrics = calculate_metrics(st.session_state.result, horizon)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

result = st.session_state.result
metrics = st.session_state.metrics
columns = st.columns(5)
for column, label, value in zip(
    columns,
    ("Throughput", "Avg latency", "Avg RTT", "Delivery ratio", "Packet loss"),
    (
        f"{metrics.throughput_mbps:.3f} Mbps",
        f"{metrics.average_latency_ms:.3f} ms",
        f"{metrics.average_rtt_ms:.3f} ms",
        f"{metrics.delivery_ratio:.1%}",
        str(metrics.queue_drops + metrics.random_losses),
    ),
):
    column.metric(label, value)

st.subheader("Queue occupancy")
st.line_chart(
    [{"time": time, "queued_packets": occupancy} for time, occupancy in result.queue_occupancy],
    x="time",
    y="queued_packets",
)

st.subheader("Packet outcomes")
outcomes = {}
for packet in result.packets:
    outcomes[packet.status] = outcomes.get(packet.status, 0) + 1
st.bar_chart([{"status": status, "packets": count} for status, count in outcomes.items()], x="status", y="packets")

st.subheader("Event timeline")
st.dataframe(result.event_trace, use_container_width=True)

packet_rows = [
    {
        "packet_id": packet.packet_id,
        "status": packet.status,
        "created": packet.creation_time,
        "transmission_start": packet.transmission_start,
        "delivered": packet.delivery_time,
        "acknowledged": packet.acknowledgment_time,
    }
    for packet in result.packets
]
st.subheader("Packet-level results")
st.dataframe(packet_rows, use_container_width=True)
csv_buffer = io.StringIO()
if packet_rows:
    writer = csv.DictWriter(csv_buffer, fieldnames=packet_rows[0].keys())
    writer.writeheader()
    writer.writerows(packet_rows)
st.download_button("Download packet results CSV", csv_buffer.getvalue(), "pulsewire-packets.csv", "text/csv")
