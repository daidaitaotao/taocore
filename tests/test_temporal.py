"""Test temporal primitives."""

import numpy as np
from taocore import Node, Edge, Graph


def test_node_with_timestamp():
    """Test node with timestamp."""
    node = Node(id="n1", features={"x": 1.0}, timestamp=100.0, decay_rate=0.1)

    assert node.timestamp == 100.0
    assert node.decay_rate == 0.1
    assert node.age(150.0) == 50.0

    # Strength should decay
    strength = node.compute_strength(150.0)
    assert 0.0 < strength < 1.0
    assert abs(strength - np.exp(-0.1 * 50.0)) < 1e-6


def test_node_without_timestamp():
    """Test backward compatibility - node without temporal features."""
    node = Node(id="n1", features={"x": 1.0})

    assert node.timestamp is None
    assert node.decay_rate == 0.0
    assert node.age(100.0) is None
    assert node.compute_strength(100.0) == 1.0  # No decay
    assert not node.is_expired(100.0)


def test_node_no_decay():
    """Test node with timestamp but no decay."""
    node = Node(id="n1", timestamp=100.0, decay_rate=0.0)

    assert node.compute_strength(1000.0) == 1.0  # No decay
    assert not node.is_expired(1000.0)


def test_node_expiration():
    """Test node expiration threshold."""
    node = Node(id="n1", timestamp=0.0, decay_rate=0.5)

    # At small time, not expired
    assert not node.is_expired(1.0, threshold=0.5)

    # At large time, expired
    assert node.is_expired(20.0, threshold=0.01)


def test_edge_with_timestamp():
    """Test edge with temporal features."""
    edge = Edge("n1", "n2", weight=1.0, timestamp=100.0, decay_rate=0.1)

    assert edge.timestamp == 100.0
    assert edge.age(150.0) == 50.0

    # Effective weight should decay
    strength = edge.compute_strength(150.0)
    expected = 1.0 * np.exp(-0.1 * 50.0)
    assert abs(strength - expected) < 1e-6


def test_edge_backward_compatibility():
    """Test edge without temporal features."""
    edge = Edge("n1", "n2", weight=0.5)

    assert edge.timestamp is None
    assert edge.compute_strength(100.0) == 0.5  # Base weight, no decay


def test_edge_zero_weight():
    """Test edge with zero weight is always expired."""
    edge = Edge("n1", "n2", weight=0.0, timestamp=100.0, decay_rate=0.1)

    assert edge.is_expired(150.0)


def test_temporal_graph_workflow():
    """Test temporal features in graph context."""
    graph = Graph()

    # Add nodes with different timestamps
    n1 = Node("n1", {"x": 1.0}, timestamp=0.0, decay_rate=0.1)
    n2 = Node("n2", {"x": 2.0}, timestamp=50.0, decay_rate=0.1)
    n3 = Node("n3", {"x": 3.0})  # No timestamp

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    # Add temporal edge
    graph.add_edge(Edge("n1", "n2", weight=1.0, timestamp=10.0, decay_rate=0.05))

    current_time = 100.0

    # Check node strengths
    assert n1.compute_strength(current_time) < 1.0  # Decayed
    assert n2.compute_strength(current_time) < 1.0  # Decayed less
    assert n3.compute_strength(current_time) == 1.0  # No decay

    # Find active nodes (not expired)
    active_nodes = [
        n for n in graph.nodes() if not n.is_expired(current_time, threshold=0.01)
    ]
    assert len(active_nodes) >= 1


def test_node_repr_with_temporal():
    """Test node string representation with temporal features."""
    node = Node("n1", {"x": 1.0}, timestamp=100.0, decay_rate=0.5)
    repr_str = repr(node)

    assert "timestamp=100.0" in repr_str
    assert "decay_rate=0.5" in repr_str


def test_node_repr_without_temporal():
    """Test node string representation without temporal features."""
    node = Node("n1", {"x": 1.0})
    repr_str = repr(node)

    assert "timestamp" not in repr_str
    assert "decay_rate" not in repr_str


def test_edge_repr_with_temporal():
    """Test edge string representation with temporal features."""
    edge = Edge("n1", "n2", weight=0.8, timestamp=50.0, decay_rate=0.1)
    repr_str = repr(edge)

    assert "timestamp=50.0" in repr_str
    assert "decay_rate=0.1" in repr_str


def test_edge_repr_without_temporal():
    """Test edge string representation without temporal features."""
    edge = Edge("n1", "n2", weight=0.8)
    repr_str = repr(edge)

    assert "timestamp" not in repr_str
    assert "decay_rate" not in repr_str
