"""Test attention metric."""

import numpy as np
from taocore import Node, Graph, AttentionMetric


def test_attention_similarity_cosine():
    """Test similarity mode with cosine distance."""
    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")

    query = {"joy": 1.0, "energy": 0.5}
    target = {"joy": 1.0, "energy": 0.5}

    score = metric.compute(query, target)
    assert abs(score - 1.0) < 1e-6  # Identical vectors


def test_attention_similarity_euclidean():
    """Test similarity mode with euclidean distance."""
    metric = AttentionMetric(mode="similarity", similarity_fn="euclidean")

    query = {"x": 0.0, "y": 0.0}
    target = {"x": 3.0, "y": 4.0}  # Distance = 5

    score = metric.compute(query, target)
    expected = 1.0 / (1.0 + 5.0)  # = 0.1667
    assert abs(score - expected) < 1e-4


def test_attention_with_node():
    """Test attention scoring a single node."""
    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")

    query = {"emotion": 0.8}
    node = Node("n1", features={"emotion": 0.6})

    score = metric.compute(query, node)
    assert isinstance(score, float)
    assert score > 0


def test_attention_with_graph():
    """Test attention scoring all nodes in graph."""
    graph = Graph()
    graph.add_node(Node("n1", {"joy": 0.9, "energy": 0.8}))
    graph.add_node(Node("n2", {"joy": 0.2, "energy": 0.1}))
    graph.add_node(Node("n3", {"joy": 0.7, "energy": 0.6}))

    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")
    query = {"joy": 1.0, "energy": 1.0}

    scores = metric.compute(query, graph)

    assert isinstance(scores, dict)
    assert len(scores) == 3
    assert scores["n1"] > scores["n2"]  # n1 more similar
    assert scores["n3"] > scores["n2"]


def test_attention_composite_mode():
    """Test composite mode with multiple signals."""
    metric = AttentionMetric(
        mode="composite",
        composite_weights={"similarity": 0.5, "recency": 0.3, "strength": 0.2},
    )

    query = {"x": 1.0}
    node = Node("n1", features={"x": 0.8}, timestamp=90.0, decay_rate=0.01)

    score = metric.compute(query, node, current_time=100.0)

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_attention_composite_without_time():
    """Test composite mode when temporal data missing."""
    metric = AttentionMetric(
        mode="composite",
        composite_weights={
            "similarity": 0.7,
            "recency": 0.3,  # Should handle gracefully
        },
    )

    query = {"x": 1.0}
    node = Node("n1", features={"x": 0.8})  # No timestamp

    # Should not crash, recency signal = 0
    score = metric.compute(query, node, current_time=100.0)
    assert isinstance(score, float)


def test_attention_no_common_features():
    """Test attention with no overlapping features."""
    metric = AttentionMetric(mode="similarity")

    query = {"a": 1.0}
    target = {"b": 1.0}

    score = metric.compute(query, target)
    assert score == 0.0


def test_attention_with_node_list():
    """Test attention with list of nodes."""
    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")

    query = {"x": 1.0, "y": 1.0}
    nodes = [
        Node("n1", {"x": 0.9, "y": 0.9}),  # Very similar direction
        Node("n2", {"x": 0.7, "y": 0.5}),  # Somewhat similar
        Node("n3", {"x": 0.1, "y": 0.9}),  # Different direction
    ]

    scores = metric.compute(query, nodes)

    assert isinstance(scores, dict)
    assert len(scores) == 3
    assert scores["n1"] > scores["n2"]
    assert scores["n2"] > scores["n3"]


def test_attention_cosine_orthogonal():
    """Test cosine similarity with orthogonal vectors."""
    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")

    query = {"x": 1.0, "y": 0.0}
    target = {"x": 0.0, "y": 1.0}

    score = metric.compute(query, target)
    assert abs(score - 0.0) < 1e-6  # Orthogonal vectors


def test_attention_cosine_opposite():
    """Test cosine similarity with opposite vectors."""
    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")

    query = {"x": 1.0}
    target = {"x": -1.0}

    score = metric.compute(query, target)
    assert abs(score - (-1.0)) < 1e-6  # Opposite vectors


def test_attention_zero_vector():
    """Test attention with zero vector."""
    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")

    query = {"x": 0.0, "y": 0.0}
    target = {"x": 1.0, "y": 1.0}

    score = metric.compute(query, target)
    assert score == 0.0  # Zero vector handling


def test_attention_composite_only_similarity():
    """Test composite mode with only similarity signal."""
    metric = AttentionMetric(
        mode="composite",
        composite_weights={"similarity": 1.0},
    )

    query = {"x": 1.0}
    node = Node("n1", {"x": 1.0})

    score = metric.compute(query, node)
    assert abs(score - 1.0) < 1e-6


def test_attention_composite_recency():
    """Test composite mode recency signal."""
    metric = AttentionMetric(
        mode="composite",
        composite_weights={"recency": 1.0},
    )

    # Recent node
    recent_node = Node("recent", timestamp=95.0)
    recent_score = metric.compute({}, recent_node, current_time=100.0)

    # Old node
    old_node = Node("old", timestamp=0.0)
    old_score = metric.compute({}, old_node, current_time=100.0)

    assert recent_score > old_score


def test_attention_composite_strength():
    """Test composite mode strength signal."""
    metric = AttentionMetric(
        mode="composite",
        composite_weights={"strength": 1.0},
    )

    # Strong node (no decay)
    strong_node = Node("strong", timestamp=0.0, decay_rate=0.0)
    strong_score = metric.compute({}, strong_node, current_time=100.0)

    # Weak node (high decay)
    weak_node = Node("weak", timestamp=0.0, decay_rate=0.1)
    weak_score = metric.compute({}, weak_node, current_time=100.0)

    assert strong_score > weak_score


def test_attention_get_params():
    """Test parameter introspection."""
    metric = AttentionMetric(
        mode="composite",
        similarity_fn="euclidean",
        composite_weights={"similarity": 0.5},
        custom_param="test",
    )

    params = metric.get_params()
    assert "custom_param" in params
    assert params["custom_param"] == "test"
