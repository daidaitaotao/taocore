"""Test core primitives."""

import numpy as np
from taocore import Node, Edge, Graph, StateVector


def test_node():
    """Test Node primitive."""
    node = Node(id="n1", features={"x": 1.0, "y": 2.0})
    assert node.id == "n1"
    assert node.features["x"] == 1.0


def test_edge():
    """Test Edge primitive."""
    edge = Edge(source="n1", target="n2", weight=0.5)
    assert edge.source == "n1"
    assert edge.target == "n2"
    assert edge.weight == 0.5


def test_graph():
    """Test Graph primitive."""
    graph = Graph()
    n1 = Node(id="n1")
    n2 = Node(id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge("n1", "n2", 1.0))

    assert len(graph.nodes()) == 2
    assert len(graph.edges()) == 1
    assert "n2" in graph.neighbors("n1")


def test_state_vector():
    """Test StateVector primitive."""
    s1 = StateVector({"a": 1.0, "b": 2.0})
    s2 = StateVector({"a": 1.5, "b": 2.5})

    distance = s1.distance(s2)
    assert distance > 0
    assert isinstance(s1.array, np.ndarray)


def test_graph_find_nodes():
    """Test find_nodes with predicate."""
    graph = Graph()
    graph.add_node(Node("n1", {"energy": 0.8}))
    graph.add_node(Node("n2", {"energy": 0.3}))
    graph.add_node(Node("n3", {"energy": 0.9}))

    high_energy = graph.find_nodes(lambda n: n.features.get("energy", 0) > 0.5)
    assert len(high_energy) == 2
    assert set(n.id for n in high_energy) == {"n1", "n3"}


def test_graph_filter_edges():
    """Test filter_edges with predicate."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))
    graph.add_node(Node("n3"))

    graph.add_edge(Edge("n1", "n2", weight=0.9))
    graph.add_edge(Edge("n2", "n3", weight=0.3))

    strong_edges = graph.filter_edges(lambda e: e.weight > 0.5)
    assert len(strong_edges) == 1
    assert strong_edges[0].source == "n1"


def test_graph_k_hop_neighbors():
    """Test k-hop neighborhood finding."""
    graph = Graph()
    for i in range(5):
        graph.add_node(Node(f"n{i}"))

    # Linear chain: n0 -> n1 -> n2 -> n3 -> n4
    graph.add_edge(Edge("n0", "n1"))
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n3"))
    graph.add_edge(Edge("n3", "n4"))

    # 1-hop from n0
    neighbors = graph.k_hop_neighbors("n0", k=1)
    assert neighbors == {"n1"}

    # 2-hop from n0
    neighbors = graph.k_hop_neighbors("n0", k=2)
    assert neighbors == {"n1", "n2"}

    # With distances
    neighbors = graph.k_hop_neighbors("n0", k=3, include_distances=True)
    assert neighbors == {"n1": 1, "n2": 2, "n3": 3}


def test_graph_k_hop_neighbors_nonexistent():
    """Test k-hop neighbors for nonexistent node."""
    graph = Graph()
    graph.add_node(Node("n1"))

    neighbors = graph.k_hop_neighbors("nonexistent", k=1)
    assert neighbors == set()

    neighbors = graph.k_hop_neighbors("nonexistent", k=1, include_distances=True)
    assert neighbors == {}


def test_graph_shortest_path():
    """Test shortest path finding."""
    graph = Graph()
    graph.add_node(Node("a"))
    graph.add_node(Node("b"))
    graph.add_node(Node("c"))
    graph.add_node(Node("d"))

    graph.add_edge(Edge("a", "b"))
    graph.add_edge(Edge("b", "c"))
    graph.add_edge(Edge("a", "d"))
    graph.add_edge(Edge("d", "c"))

    # Two possible paths: a->b->c or a->d->c (both length 2)
    path = graph.shortest_path("a", "c")
    assert len(path) == 3
    assert path[0] == "a"
    assert path[-1] == "c"


def test_graph_shortest_path_no_path():
    """Test shortest path when no path exists."""
    graph = Graph()
    graph.add_node(Node("a"))
    graph.add_node(Node("isolated"))

    path = graph.shortest_path("a", "isolated")
    assert path is None


def test_graph_shortest_path_same_node():
    """Test shortest path from node to itself."""
    graph = Graph()
    graph.add_node(Node("a"))

    path = graph.shortest_path("a", "a")
    assert path == ["a"]


def test_graph_shortest_path_nonexistent():
    """Test shortest path with nonexistent nodes."""
    graph = Graph()
    graph.add_node(Node("a"))

    path = graph.shortest_path("a", "nonexistent")
    assert path is None

    path = graph.shortest_path("nonexistent", "a")
    assert path is None


def test_graph_subgraph():
    """Test subgraph extraction."""
    graph = Graph()
    for i in range(5):
        graph.add_node(Node(f"n{i}", {"val": float(i)}))

    graph.add_edge(Edge("n0", "n1"))
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n3"))
    graph.add_edge(Edge("n3", "n4"))

    # Extract subgraph
    subg = graph.subgraph({"n1", "n2", "n3"}, include_edges_between=True)

    assert len(subg.nodes()) == 3
    assert len(subg.edges()) == 2  # n1->n2, n2->n3

    # Verify edge preservation
    edge_pairs = {(e.source, e.target) for e in subg.edges()}
    assert ("n1", "n2") in edge_pairs
    assert ("n2", "n3") in edge_pairs


def test_graph_subgraph_without_edges():
    """Test subgraph extraction without edges."""
    graph = Graph()
    for i in range(3):
        graph.add_node(Node(f"n{i}"))

    graph.add_edge(Edge("n0", "n1"))
    graph.add_edge(Edge("n1", "n2"))

    subg = graph.subgraph({"n0", "n1"}, include_edges_between=False)

    assert len(subg.nodes()) == 2
    assert len(subg.edges()) == 0


def test_graph_undirected_edge():
    """Test undirected edge adds reverse adjacency."""
    graph = Graph()
    graph.add_node(Node("a"))
    graph.add_node(Node("b"))
    graph.add_edge(Edge("a", "b", directed=False))

    assert "b" in graph.neighbors("a")
    assert "a" in graph.neighbors("b")
