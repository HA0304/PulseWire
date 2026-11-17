import csv
import io

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from pulsewire.engine import SimulationEngine
from pulsewire.metrics import calculate_metrics
from pulsewire.models import SimulationConfig
from pulsewire.streaming import StreamSession, StreamStatus, batch_events
from pulsewire.topology import TopologyGraph, TopologyLink, TopologyNode


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

st.subheader("Topology editor")
if "topology" not in st.session_state:
    st.session_state.topology = TopologyGraph(
        nodes={
            "source": TopologyNode("source", "Source", 10, 50),
            "destination": TopologyNode("destination", "Destination", 90, 50),
        },
        links={
            "link-1": TopologyLink("link-1", "source", "destination", bandwidth, latency, int(buffer_size)),
        },
    )

topology = st.session_state.topology
topology_col1, topology_col2 = st.columns(2)
with topology_col1:
    new_node_id = st.text_input("New node ID", key="new_node_id")
    new_node_label = st.text_input("New node label", key="new_node_label")
    if st.button("Add node") and new_node_id:
        try:
            topology.add_node(TopologyNode(new_node_id.strip(), new_node_label.strip() or new_node_id.strip()))
        except ValueError as exc:
            st.error(str(exc))
with topology_col2:
    node_ids = list(topology.nodes)
    source_id = st.selectbox("Link source", node_ids, key="topology_source")
    destination_id = st.selectbox("Link destination", node_ids, key="topology_destination")
    link_id = st.text_input("Link ID", value="link-new", key="topology_link_id")
    link_bandwidth = st.number_input("Link bandwidth (Mbps)", min_value=0.01, value=10.0, key="topology_link_bandwidth")
    link_latency = st.number_input("Link propagation (ms)", min_value=0.0, value=10.0, key="topology_link_latency")
    link_buffer = st.number_input("Link buffer", min_value=0, value=10, key="topology_link_buffer")
    if st.button("Add link"):
        try:
            topology.add_link(
                TopologyLink(
                    link_id.strip(),
                    source_id,
                    destination_id,
                    link_bandwidth,
                    link_latency,
                    int(link_buffer),
                )
            )
        except ValueError as exc:
            st.error(str(exc))

node_rows = [
    {"node_id": node.node_id, "label": node.label, "x": node.x, "y": node.y}
    for node in topology.nodes.values()
]
edited_nodes = st.data_editor(
    node_rows,
    column_config={
        "node_id": st.column_config.TextColumn(disabled=True),
        "label": st.column_config.TextColumn(),
        "x": st.column_config.NumberColumn(min_value=0.0, max_value=100.0),
        "y": st.column_config.NumberColumn(min_value=0.0, max_value=100.0),
    },
    num_rows="fixed",
    key="topology_nodes_editor",
)
for row in edited_nodes:
    if row["node_id"] in topology.nodes:
        topology.move_node(row["node_id"], row["x"], row["y"])

link_rows = [
    {
        "link_id": link.link_id,
        "source": link.source,
        "destination": link.destination,
        "bandwidth_mbps": link.bandwidth_mbps,
        "latency_ms": link.latency_ms,
        "buffer_size": link.buffer_size,
    }
    for link in topology.links.values()
]
st.dataframe(link_rows, use_container_width=True)

topology_remove_col1, topology_remove_col2 = st.columns(2)
with topology_remove_col1:
    if topology.links:
        selected_link = st.selectbox(
            "Selected link",
            [link.link_id for link in topology.links.values()],
            key="topology_selected_link",
        )
        if st.button("Remove selected link"):
            topology.remove_link(selected_link)
with topology_remove_col2:
    if topology.nodes:
        selected_node = st.selectbox(
            "Selected node",
            [node.node_id for node in topology.nodes.values()],
            key="topology_selected_node",
        )
        if st.button("Remove selected node"):
            try:
                topology.remove_node(selected_node)
            except ValueError as exc:
                st.error(str(exc))

st.subheader("Live event streaming")
live_col1, live_col2, live_col3, live_col4 = st.columns(4)
start_live = live_col1.button("Start live stream")
pause_live = live_col2.button("Pause live stream")
resume_live = live_col3.button("Resume live stream")
stop_live = live_col4.button("Stop live stream")

if start_live:
    live_config = SimulationConfig(
        bandwidth_mbps=bandwidth,
        latency_ms=latency,
        buffer_size=int(buffer_size),
        packet_size_bytes=int(packet_size),
        rate_packets_per_sec=max(rate, 1.0),
        loss_probability=loss,
        simulation_horizon_seconds=min(horizon, 20.0),
        random_seed=int(seed),
        max_event_history=4096,
    )
    live_engine = SimulationEngine(live_config)
    st.session_state.live_session = StreamSession(batch_size=256, buffer_limit=4096)
    st.session_state.live_session.start()
    st.session_state.live_engine = live_engine
    st.session_state.live_iterator = live_engine.iter_events(
        cancel_check=lambda: st.session_state.live_session.status is StreamStatus.STOPPED
    )
    st.session_state.live_batches = []
    st.session_state.live_event_count = 0

if "live_session" in st.session_state:
    live_session = st.session_state.live_session
    if pause_live:
        live_session.pause()
    if resume_live:
        live_session.resume()
    if stop_live:
        live_session.stop()
        st.session_state.live_engine.cancel()

    if live_session.status is StreamStatus.RUNNING:
        st_autorefresh(interval=100, key="pulsewire-live-refresh")
        try:
            events = []
            for _ in range(live_session.batch_size):
                events.append(next(st.session_state.live_iterator))
        except StopIteration:
            live_session.status = StreamStatus.COMPLETED
        if events:
            batch = list(batch_events(events, live_session.batch_size))[0]
            st.session_state.live_batches.extend(batch.events)
            st.session_state.live_event_count += len(batch.events)
            if len(st.session_state.live_batches) > 4096:
                del st.session_state.live_batches[:-4096]

    st.caption(
        f"Status: {live_session.status.value} | "
        f"Events streamed: {st.session_state.live_event_count} | "
        f"Transport dropped: {st.session_state.live_session.buffer.dropped}"
    )
    st.dataframe(st.session_state.live_batches[-1000:], use_container_width=True)
