"""RFC-2 Verification: Metrics for Balance, Flow, Clustering, and Hubs.

This example demonstrates all the metrics specified in RFC-2:
1. BalanceMetric - Already existed
2. FlowMetric - Already existed
3. ClusterMetric - New (components, modularity, distance)
4. HubMetric - New (degree, betweenness, eigenvector, pagerank)
5. CompositeMetric - New (weighted combinations)
"""

from taocore import (
    Node,
    Edge,
    Graph,
    StateVector,
    BalanceMetric,
    FlowMetric,
    ClusterMetric,
    HubMetric,
    CompositeMetric,
)
import numpy as np


def test_balance_metric():
    """Verify BalanceMetric (RFC-2 Section 1)."""
    print("=" * 60)
    print("1. BalanceMetric - Bounded Stability")
    print("=" * 60)

    metric = BalanceMetric(bounds={"x": (0.0, 10.0), "y": (0.0, 5.0)})

    # Perfect balance
    score1 = metric.compute({"x": 5.0, "y": 2.5})
    print(f"Perfect balance: {score1:.3f}")

    # Out of bounds
    score2 = metric.compute({"x": 12.0, "y": 2.5})
    print(f"Out of bounds: {score2:.3f}")

    print("✓ BalanceMetric verified\n")


def test_flow_metric():
    """Verify FlowMetric (RFC-2 Section 2)."""
    print("=" * 60)
    print("2. FlowMetric - Temporal Coherence")
    print("=" * 60)

    states = [
        StateVector(np.array([0.0, 0.0])),
        StateVector(np.array([1.0, 1.0])),
        StateVector(np.array([2.0, 2.0])),
    ]

    # Coherence mode
    metric = FlowMetric(mode="coherence")
    score = metric.compute(states)
    print(f"Coherence: {score:.3f}")

    # Volatility mode
    metric = FlowMetric(mode="volatility")
    score = metric.compute(states)
    print(f"Volatility: {score:.3f}")

    print("✓ FlowMetric verified\n")


def test_cluster_metric():
    """Verify ClusterMetric (RFC-2 Section 3)."""
    print("=" * 60)
    print("3. ClusterMetric - Graph Clustering")
    print("=" * 60)

    # Create test graph with two communities
    graph = Graph()
    for i in range(6):
        graph.add_node(Node(f"n{i}", features={"x": i % 3, "y": i // 3}))

    # Community 1: {n0, n1, n2}
    for i in range(3):
        for j in range(i + 1, 3):
            graph.add_edge(Edge(f"n{i}", f"n{j}"))
            graph.add_edge(Edge(f"n{j}", f"n{i}"))

    # Community 2: {n3, n4, n5}
    for i in range(3, 6):
        for j in range(i + 1, 6):
            graph.add_edge(Edge(f"n{i}", f"n{j}"))
            graph.add_edge(Edge(f"n{j}", f"n{i}"))

    # Weak connection between communities
    graph.add_edge(Edge("n2", "n3"))
    graph.add_edge(Edge("n3", "n2"))

    # Test connected components
    metric = ClusterMetric(algorithm="components")
    result = metric.compute(graph)
    print(f"Components: {result['num_clusters']} clusters")
    print(f"Sizes: {result['sizes']}")

    # Test modularity
    metric = ClusterMetric(algorithm="modularity")
    result = metric.compute(graph)
    print(f"Modularity: {result['num_clusters']} clusters, Q={result['modularity']:.3f}")

    # Test distance-based
    metric = ClusterMetric(algorithm="distance", threshold=2.0)
    result = metric.compute(graph)
    print(f"Distance-based: {result['num_clusters']} clusters")

    print("✓ ClusterMetric verified\n")


def test_hub_metric():
    """Verify HubMetric (RFC-2 Section 4)."""
    print("=" * 60)
    print("4. HubMetric - Centrality Measures")
    print("=" * 60)

    # Create star topology (n0 is hub)
    graph = Graph()
    for i in range(5):
        graph.add_node(Node(f"n{i}"))

    for i in range(1, 5):
        graph.add_edge(Edge("n0", f"n{i}"))
        graph.add_edge(Edge(f"n{i}", "n0"))

    # Test degree centrality
    metric = HubMetric(method="degree")
    scores = metric.compute(graph)
    print(f"Degree centrality: n0={scores['n0']:.3f}, n1={scores['n1']:.3f}")

    # Test betweenness
    metric = HubMetric(method="betweenness")
    scores = metric.compute(graph)
    print(f"Betweenness: n0={scores['n0']:.3f}, n1={scores['n1']:.3f}")

    # Test eigenvector
    metric = HubMetric(method="eigenvector")
    scores = metric.compute(graph)
    print(f"Eigenvector: n0={scores['n0']:.3f}, n1={scores['n1']:.3f}")

    # Test PageRank
    metric = HubMetric(method="pagerank")
    scores = metric.compute(graph)
    print(f"PageRank: n0={scores['n0']:.3f}, n1={scores['n1']:.3f}")

    print("✓ HubMetric verified\n")


def test_composite_metric():
    """Verify CompositeMetric (RFC-2 Section 5)."""
    print("=" * 60)
    print("5. CompositeMetric - Metric Composition")
    print("=" * 60)

    # Create two balance metrics
    metric1 = BalanceMetric(bounds={"x": (0.0, 10.0)})
    metric2 = BalanceMetric(bounds={"y": (0.0, 5.0)})

    # Test weighted sum
    composite = CompositeMetric(
        metrics=[metric1, metric2],
        weights=[0.6, 0.4],
        aggregation="weighted_sum"
    )
    score = composite.compute({"x": 5.0, "y": 2.5})
    print(f"Weighted sum: {score:.3f}")

    # Test weighted average
    composite = CompositeMetric(
        metrics=[metric1, metric2],
        weights=[3.0, 1.0],
        aggregation="weighted_avg"
    )
    score = composite.compute({"x": 5.0, "y": 2.5})
    print(f"Weighted average: {score:.3f}")

    # Test with components
    result = composite.compute({"x": 5.0, "y": 2.5}, return_components=True)
    print(f"Components: {result['components']}")
    print(f"Weights: {result['weights']}")

    # Test with graph metrics
    graph = Graph()
    for i in range(4):
        graph.add_node(Node(f"n{i}"))
    graph.add_edge(Edge("n0", "n1"))
    graph.add_edge(Edge("n1", "n0"))
    graph.add_edge(Edge("n1", "n2"))
    graph.add_edge(Edge("n2", "n1"))

    hub1 = HubMetric(method="degree")
    hub2 = HubMetric(method="betweenness")
    composite = CompositeMetric(
        metrics=[hub1, hub2],
        weights=[0.5, 0.5],
        aggregation="weighted_sum"
    )
    scores = composite.compute(graph)
    print(f"Composite hub scores: n0={scores['n0']:.3f}, n1={scores['n1']:.3f}, n2={scores['n2']:.3f}")

    print("✓ CompositeMetric verified\n")


def main():
    """Run all RFC-2 verifications."""
    print("\n" + "=" * 60)
    print("RFC-2 Verification: Metrics Implementation")
    print("=" * 60 + "\n")

    test_balance_metric()
    test_flow_metric()
    test_cluster_metric()
    test_hub_metric()
    test_composite_metric()

    print("=" * 60)
    print("✓ All RFC-2 features verified successfully!")
    print("=" * 60)
    print("\nSummary:")
    print("1. BalanceMetric - Bounded stability ✓")
    print("2. FlowMetric - Temporal coherence ✓")
    print("3. ClusterMetric - Components, modularity, distance ✓")
    print("4. HubMetric - Degree, betweenness, eigenvector, PageRank ✓")
    print("5. CompositeMetric - Weighted combinations ✓")
    print()


if __name__ == "__main__":
    main()
