import pytest

from pulsewire.topology import TopologyGraph, TopologyLink, TopologyNode


def graph():
    topology = TopologyGraph()
    topology.add_node(TopologyNode("a", "A", 10, 20))
    topology.add_node(TopologyNode("b", "B", 80, 20))
    return topology


def test_add_move_and_select_link():
    topology = graph()
    topology.move_node("a", 30, 40)
    topology.add_link(TopologyLink("l1", "a", "b"))
    assert topology.nodes["a"].x == 30
    assert topology.links["l1"].source == "a"


@pytest.mark.parametrize(
    "link",
    [
        TopologyLink("l1", "missing", "b"),
        TopologyLink("l1", "a", "missing"),
        TopologyLink("l1", "a", "a"),
        TopologyLink("l1", "a", "b", bandwidth_mbps=0),
    ],
)
def test_illegal_link_rejected(link):
    topology = graph()
    with pytest.raises(ValueError):
        topology.add_link(link)


def test_duplicate_link_and_dangling_removal():
    topology = graph()
    topology.add_link(TopologyLink("l1", "a", "b"))
    with pytest.raises(ValueError, match="duplicate"):
        topology.add_link(TopologyLink("l2", "a", "b"))
    with pytest.raises(ValueError, match="cannot remove"):
        topology.remove_node("a")
    topology.remove_link("l1")
    topology.remove_node("a")
    assert "a" not in topology.nodes
