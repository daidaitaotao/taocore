"""Test metrics."""

import numpy as np
from taocore import (
    BalanceMetric,
    FlowMetric,
    StateVector,
    Graph,
    Node,
    Edge,
)
from taocore.metrics.cluster import ClusterMetric
from taocore.metrics.hub import HubMetric
from taocore.metrics.composite import CompositeMetric


def test_balance_metric():
    """Test BalanceMetric."""
    metric = BalanceMetric(bounds={"x": (0.0, 10.0), "y": (0.0, 5.0)})

    # Perfect balance
    score = metric.compute({"x": 5.0, "y": 2.5})
    assert score == 1.0

    # Out of bounds
    score = metric.compute({"x": 15.0, "y": 2.5})
    assert score < 1.0


def test_flow_metric():
    """Test FlowMetric."""
    states = [
        StateVector(np.array([0.0, 0.0])),
        StateVector(np.array([1.0, 1.0])),
        StateVector(np.array([2.0, 2.0])),
    ]

    metric = FlowMetric(mode="coherence")
    score = metric.compute(states)
    assert isinstance(score, float)

    metric = FlowMetric(mode="volatility")
    score = metric.compute(states)
    assert score > 0


# ============================================================================
# ClusterMetric Tests
# ============================================================================


def test_cluster_components_basic():
    """Test connected components clustering."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))
    graph.add_node(Node("n3"))
    graph.add_node(Node("n4"))

    # Two components: {n1, n2} and {n3, n4}
    # Add edges bidirectionally (graph is directed)
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n1"))
    graph.add_edge(Edge("n3", "n4"))
    graph.add_edge(Edge("n4", "n3"))

    metric = ClusterMetric(algorithm="components")
    result = metric.compute(graph)

    assert result["num_clusters"] == 2
    assert len(result["sizes"]) == 2
    assert set(result["sizes"]) == {2}
    assert result["assignments"]["n1"] == result["assignments"]["n2"]
    assert result["assignments"]["n3"] == result["assignments"]["n4"]
    assert result["assignments"]["n1"] != result["assignments"]["n3"]


def test_cluster_components_single_component():
    """Test single connected component."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))
    graph.add_node(Node("n3"))
    # Add bidirectional edges
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n1"))
    graph.add_edge(Edge("n2", "n3"))
    graph.add_edge(Edge("n3", "n2"))

    metric = ClusterMetric(algorithm="components")
    result = metric.compute(graph)

    assert result["num_clusters"] == 1
    assert result["sizes"] == [3]
    # All nodes in same cluster
    cluster_id = result["assignments"]["n1"]
    assert all(result["assignments"][nid] == cluster_id for nid in ["n1", "n2", "n3"])


def test_cluster_components_min_size():
    """Test minimum cluster size filtering."""
    graph = Graph()
    for i in range(5):
        graph.add_node(Node(f"n{i}"))

    # One large component {n0, n1, n2}, two isolated nodes
    # Add bidirectional edges
    graph.add_edge(Edge("n0", "n1"))
    graph.add_edge(Edge("n1", "n0"))
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n1"))

    metric = ClusterMetric(algorithm="components", min_cluster_size=2)
    result = metric.compute(graph)

    # Only the large component should be included
    assert result["num_clusters"] == 1
    assert result["sizes"] == [3]
    assert "n0" in result["assignments"]
    assert "n3" not in result["assignments"]  # Isolated node excluded


def test_cluster_modularity_basic():
    """Test modularity-based clustering."""
    graph = Graph()
    for i in range(6):
        graph.add_node(Node(f"n{i}"))

    # Two dense communities (bidirectional edges)
    # Triangle 1
    graph.add_edge(Edge("n0", "n1"))
    graph.add_edge(Edge("n1", "n0"))
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n1"))
    graph.add_edge(Edge("n0", "n2"))
    graph.add_edge(Edge("n2", "n0"))

    # Triangle 2
    graph.add_edge(Edge("n3", "n4"))
    graph.add_edge(Edge("n4", "n3"))
    graph.add_edge(Edge("n4", "n5"))
    graph.add_edge(Edge("n5", "n4"))
    graph.add_edge(Edge("n3", "n5"))
    graph.add_edge(Edge("n5", "n3"))

    # Weak connection between communities
    graph.add_edge(Edge("n2", "n3"))
    graph.add_edge(Edge("n3", "n2"))

    metric = ClusterMetric(algorithm="modularity")
    result = metric.compute(graph)

    # Should find communities (at least 1, possibly 2)
    assert result["num_clusters"] >= 1
    assert "modularity" in result
    assert isinstance(result["modularity"], float)


def test_cluster_distance_basic():
    """Test distance-based clustering with features."""
    graph = Graph()
    graph.add_node(Node("n1", features={"x": 0.0, "y": 0.0}))
    graph.add_node(Node("n2", features={"x": 0.1, "y": 0.1}))
    graph.add_node(Node("n3", features={"x": 10.0, "y": 10.0}))
    graph.add_node(Node("n4", features={"x": 10.1, "y": 10.1}))

    metric = ClusterMetric(algorithm="distance", threshold=1.0)
    result = metric.compute(graph)

    # Should cluster {n1, n2} and {n3, n4}
    assert result["num_clusters"] == 2
    assert result["assignments"]["n1"] == result["assignments"]["n2"]
    assert result["assignments"]["n3"] == result["assignments"]["n4"]
    assert result["assignments"]["n1"] != result["assignments"]["n3"]


def test_cluster_empty_graph():
    """Test clustering on empty graph."""
    graph = Graph()

    metric = ClusterMetric(algorithm="components")
    result = metric.compute(graph)

    assert result["num_clusters"] == 0
    assert result["sizes"] == []
    assert result["assignments"] == {}


# ============================================================================
# HubMetric Tests
# ============================================================================


def test_hub_degree_basic():
    """Test degree centrality."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))
    graph.add_node(Node("n3"))
    graph.add_node(Node("n4"))

    # n1 is hub (connected to all)
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n1", "n3"))
    graph.add_edge(Edge("n1", "n4"))

    metric = HubMetric(method="degree")
    scores = metric.compute(graph)

    assert scores["n1"] == 1.0  # Maximum degree
    assert scores["n2"] == scores["n3"] == scores["n4"]
    assert scores["n2"] < scores["n1"]


def test_hub_degree_isolated():
    """Test degree centrality with isolated nodes."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))

    metric = HubMetric(method="degree")
    scores = metric.compute(graph)

    assert scores["n1"] == 0.0
    assert scores["n2"] == 0.0


def test_hub_betweenness_basic():
    """Test betweenness centrality."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))
    graph.add_node(Node("n3"))

    # n2 is on path from n1 to n3
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n3"))

    metric = HubMetric(method="betweenness")
    scores = metric.compute(graph)

    # n2 should have higher betweenness (bridge node)
    assert scores["n2"] > scores["n1"]
    assert scores["n2"] > scores["n3"]


def test_hub_eigenvector_basic():
    """Test eigenvector centrality."""
    graph = Graph()
    for i in range(4):
        graph.add_node(Node(f"n{i}"))

    # Star topology: n0 is central hub
    graph.add_edge(Edge("n0", "n1"))
    graph.add_edge(Edge("n0", "n2"))
    graph.add_edge(Edge("n0", "n3"))

    metric = HubMetric(method="eigenvector")
    scores = metric.compute(graph)

    # Central node should have highest score
    assert scores["n0"] == 1.0 or scores["n0"] > 0.9
    assert all(scores[f"n{i}"] < scores["n0"] for i in [1, 2, 3])


def test_hub_pagerank_basic():
    """Test PageRank."""
    graph = Graph()
    for i in range(4):
        graph.add_node(Node(f"n{i}"))

    # n0 receives links from all others
    graph.add_edge(Edge("n1", "n0"))
    graph.add_edge(Edge("n2", "n0"))
    graph.add_edge(Edge("n3", "n0"))

    metric = HubMetric(method="pagerank", damping=0.85)
    scores = metric.compute(graph)

    # n0 should have highest PageRank
    assert scores["n0"] > scores["n1"]
    assert scores["n0"] > scores["n2"]
    assert scores["n0"] > scores["n3"]


def test_hub_empty_graph():
    """Test hub metrics on empty graph."""
    graph = Graph()

    metric = HubMetric(method="degree")
    scores = metric.compute(graph)

    assert scores == {}


def test_hub_invalid_method():
    """Test invalid centrality method."""
    graph = Graph()
    graph.add_node(Node("n1"))

    metric = HubMetric(method="invalid")

    try:
        metric.compute(graph)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Unknown method" in str(e)


# ============================================================================
# CompositeMetric Tests
# ============================================================================


def test_composite_weighted_sum_scalars():
    """Test weighted sum aggregation with scalar metrics."""
    # Create two simple balance metrics with different bounds
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        weights=[0.6, 0.4],
        aggregation="weighted_sum"
    )

    # metric1.compute({"x": 5.0}) = 1.0 (perfect balance)
    # metric2.compute({"y": 2.5}) = 1.0 (perfect balance)
    # composite = 0.6 * 1.0 + 0.4 * 1.0 = 1.0
    score = composite.compute({"x": 5.0, "y": 2.5})
    assert abs(score - 1.0) < 0.01


def test_composite_weighted_avg_scalars():
    """Test weighted average aggregation."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        weights=[3.0, 1.0],  # Unnormalized
        aggregation="weighted_avg"
    )

    # Same as weighted_sum but normalized by total weight (4.0)
    score = composite.compute({"x": 5.0, "y": 2.5})
    expected = (3.0 * 1.0 + 1.0 * 1.0) / 4.0
    assert abs(score - expected) < 0.01


def test_composite_equal_weights():
    """Test default equal weights."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        aggregation="weighted_sum"
    )

    # Default weights should be [1.0, 1.0]
    assert composite.get_weights() == [1.0, 1.0]


def test_composite_normalize_weights():
    """Test weight normalization."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        weights=[3.0, 1.0],
        normalize=True,
        aggregation="weighted_sum"
    )

    # Weights should be normalized to sum to 1.0
    weights = composite.get_weights()
    assert abs(sum(weights) - 1.0) < 1e-10
    assert abs(weights[0] - 0.75) < 1e-10
    assert abs(weights[1] - 0.25) < 1e-10


def test_composite_return_components():
    """Test returning individual component scores."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        weights=[0.6, 0.4],
        aggregation="weighted_sum"
    )

    result = composite.compute({"x": 5.0, "y": 2.5}, return_components=True)

    assert "composite" in result
    assert "components" in result
    assert "weights" in result
    assert len(result["components"]) == 2
    assert result["weights"] == [0.6, 0.4]


def test_composite_max_aggregation():
    """Test max aggregation."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        aggregation="max"
    )

    # metric1 = 0.5, metric2 = 1.0, max = 1.0
    score = composite.compute({"x": 7.5, "y": 2.5})
    assert score == 1.0


def test_composite_min_aggregation():
    """Test min aggregation."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        aggregation="min"
    )

    # metric1(x=12.0) -> out of bounds, score < 1.0
    # metric2(y=2.5) -> perfect balance, score = 1.0
    # min should be the lower score
    score = composite.compute({"x": 12.0, "y": 2.5})
    assert score < 1.0  # Should take the minimum (out-of-bounds metric)


def test_composite_dict_aggregation():
    """Test aggregating metrics that return dicts."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))
    graph.add_node(Node("n3"))
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n3"))

    metric1 = HubMetric(method="degree")
    metric2 = HubMetric(method="betweenness")

    composite = CompositeMetric(
        metrics=[metric1, metric2],
        weights=[0.5, 0.5],
        aggregation="weighted_sum"
    )

    scores = composite.compute(graph)

    # Should return dict with weighted sums
    assert isinstance(scores, dict)
    assert set(scores.keys()) == {"n1", "n2", "n3"}
    assert all(isinstance(v, float) for v in scores.values())


def test_composite_empty_metrics():
    """Test error on empty metrics list."""
    try:
        CompositeMetric(metrics=[])
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "At least one metric" in str(e)


def test_composite_mismatched_weights():
    """Test error on mismatched weights."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    try:
        CompositeMetric(metrics=[metric1, metric2], weights=[0.5])
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "must match" in str(e)


def test_composite_get_metrics():
    """Test retrieving composed metrics."""
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    composite = CompositeMetric(metrics=[metric1, metric2])

    metrics = composite.get_metrics()
    assert len(metrics) == 2
    assert isinstance(metrics[0], BalanceMetric)
    assert isinstance(metrics[1], BalanceMetric)
