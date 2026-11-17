from dataclasses import dataclass, replace


@dataclass(frozen=True)
class TopologyNode:
    node_id: str
    label: str
    x: float = 0.0
    y: float = 0.0


@dataclass(frozen=True)
class TopologyLink:
    link_id: str
    source: str
    destination: str
    bandwidth_mbps: float = 10.0
    latency_ms: float = 10.0
    buffer_size: int = 10


class TopologyGraph:
    def __init__(
        self,
        nodes: dict[str, TopologyNode] | None = None,
        links: dict[str, TopologyLink] | None = None,
    ):
        self.nodes = dict(nodes or {})
        self.links = dict(links or {})

    def add_node(self, node: TopologyNode) -> None:
        if not node.node_id or not node.label:
            raise ValueError("node ID and label are required")
        if node.node_id in self.nodes:
            raise ValueError(f"node '{node.node_id}' already exists")
        self.nodes[node.node_id] = node

    def move_node(self, node_id: str, x: float, y: float) -> None:
        if node_id not in self.nodes:
            raise ValueError(f"unknown node '{node_id}'")
        node = self.nodes[node_id]
        self.nodes[node_id] = replace(node, x=float(x), y=float(y))

    def add_link(self, link: TopologyLink) -> None:
        if link.link_id in self.links:
            raise ValueError(f"link '{link.link_id}' already exists")
        if link.source not in self.nodes:
            raise ValueError(f"link source '{link.source}' does not exist")
        if link.destination not in self.nodes:
            raise ValueError(f"link destination '{link.destination}' does not exist")
        if link.source == link.destination:
            raise ValueError("unsupported self-link")
        if any(
            existing.source == link.source and existing.destination == link.destination
            for existing in self.links.values()
        ):
            raise ValueError("duplicate directed link is unsupported")
        if link.bandwidth_mbps <= 0:
            raise ValueError("link bandwidth must be positive")
        if link.latency_ms < 0:
            raise ValueError("link latency must be nonnegative")
        if link.buffer_size < 0:
            raise ValueError("link buffer must be nonnegative")
        self.links[link.link_id] = link

    def remove_node(self, node_id: str) -> None:
        if node_id not in self.nodes:
            raise ValueError(f"unknown node '{node_id}'")
        dangling = [
            link.link_id
            for link in self.links.values()
            if link.source == node_id or link.destination == node_id
        ]
        if dangling:
            raise ValueError("cannot remove node while linked: " + ", ".join(dangling))
        del self.nodes[node_id]

    def remove_link(self, link_id: str) -> None:
        if link_id not in self.links:
            raise ValueError(f"unknown link '{link_id}'")
        del self.links[link_id]

    def validate(self) -> None:
        for link in self.links.values():
            if link.source not in self.nodes or link.destination not in self.nodes:
                raise ValueError(f"link '{link.link_id}' has a dangling reference")
