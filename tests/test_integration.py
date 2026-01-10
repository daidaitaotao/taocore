"""Integration tests for TaoCore components."""

import numpy as np
from taocore import (
    Node,
    Edge,
    Graph,
    StateVector,
    BalanceMetric,
    FlowMetric,
    AttentionMetric,
    EquilibriumSolver,
    Decider,
    Decision,
)


def test_graph_with_node_features():
    """Test graph operations with node features."""
    graph = Graph()

    # Add nodes with features
    n1 = Node(id="person1", features={"emotion": 0.8, "energy": 0.6})
    n2 = Node(id="person2", features={"emotion": 0.5, "energy": 0.7})
    n3 = Node(id="person3", features={"emotion": 0.3, "energy": 0.4})

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    # Add relationships
    graph.add_edge(Edge("person1", "person2", weight=0.9))
    graph.add_edge(Edge("person2", "person3", weight=0.5))

    # Verify structure
    assert len(graph.nodes()) == 3
    assert len(graph.edges()) == 2
    assert "person2" in graph.neighbors("person1")
    assert "person3" in graph.neighbors("person2")

    # Verify node retrieval
    retrieved = graph.get_node("person1")
    assert retrieved is not None
    assert retrieved.features["emotion"] == 0.8


def test_equilibrium_with_balance_metric():
    """Test equilibrium computation with balance evaluation."""

    def bounded_update(state: StateVector) -> StateVector:
        """Update rule with bounds."""
        new_vals = state.array * 0.8 + 0.1
        return StateVector(np.clip(new_vals, 0.0, 1.0))

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    initial = StateVector(np.array([5.0, 3.0]))

    result = solver.solve(initial, bounded_update)

    assert result.converged
    assert all(0.0 <= v <= 1.0 for v in result.state.array)

    # Evaluate balance of equilibrium
    metric = BalanceMetric(bounds={"x": (0.0, 1.0), "y": (0.0, 1.0)})
    balance = metric.compute({"x": result.state.array[0], "y": result.state.array[1]})

    assert balance == 1.0  # Should be in bounds


def test_flow_to_decision_pipeline():
    """Test flow metric → decider pipeline."""
    # Simulate state trajectory
    states = [
        StateVector(np.array([0.0, 0.0])),
        StateVector(np.array([0.1, 0.1])),
        StateVector(np.array([0.2, 0.2])),
        StateVector(np.array([0.25, 0.25])),
    ]

    # Compute flow metrics
    coherence_metric = FlowMetric(mode="coherence")
    volatility_metric = FlowMetric(mode="volatility")

    coherence = coherence_metric.compute(states)
    volatility = volatility_metric.compute(states)

    # Create decider
    class StabilityDecider(Decider):
        def decide(self, metrics: dict[str, float]) -> Decision:
            coherence = metrics.get("coherence", 0.0)
            volatility = metrics.get("volatility", 0.0)

            if coherence > 0.7 and volatility < 0.3:
                return Decision("stable", 0.9, {"coherence": coherence})
            else:
                return Decision("unstable", 0.6, {"volatility": volatility})

    decider = StabilityDecider()
    decision = decider.decide({"coherence": coherence, "volatility": volatility})

    assert decision.action in ["stable", "unstable"]
    assert 0.0 <= decision.confidence <= 1.0


def test_multi_node_equilibrium():
    """Test equilibrium across multiple node states."""
    graph = Graph()

    # Create nodes
    nodes = [Node(id=f"n{i}", features={"value": float(i)}) for i in range(5)]
    for node in nodes:
        graph.add_node(node)

    # Create ring topology
    for i in range(len(nodes)):
        graph.add_edge(Edge(f"n{i}", f"n{(i+1) % len(nodes)}", 1.0))

    # Extract initial state from graph
    initial_values = np.array([node.features["value"] for node in graph.nodes()])
    initial_state = StateVector(initial_values)

    # Define diffusion update
    def diffusion_update(state: StateVector) -> StateVector:
        """Average with neighbors (simple diffusion)."""
        return StateVector(state.array * 0.5 + np.mean(state.array) * 0.5)

    solver = EquilibriumSolver(max_iterations=200, tolerance=1e-6)
    result = solver.solve(initial_state, diffusion_update)

    assert result.converged

    # In diffusion, equilibrium should be near average
    expected_avg = np.mean(initial_values)
    assert np.allclose(result.state.array, expected_avg, atol=0.1)


def test_balance_metric_with_graph_features():
    """Test balance metric on graph node features."""
    graph = Graph()

    nodes = [
        Node(id="n1", features={"x": 5.0, "y": 2.5}),
        Node(id="n2", features={"x": 7.0, "y": 3.0}),
        Node(id="n3", features={"x": 15.0, "y": 2.0}),  # Out of bounds
    ]

    for node in nodes:
        graph.add_node(node)

    metric = BalanceMetric(bounds={"x": (0.0, 10.0), "y": (0.0, 5.0)})

    # Evaluate balance for each node
    balances = []
    for node in graph.nodes():
        balance = metric.compute(node.features)
        balances.append(balance)

    assert balances[0] == 1.0  # In bounds
    assert balances[1] == 1.0  # In bounds
    assert balances[2] < 1.0  # Out of bounds


def test_temporal_attention_workflow():
    """Test complete workflow: temporal graph + attention metric."""
    graph = Graph()
    current_time = 1000.0

    # Add nodes with timestamps (simulating memories)
    graph.add_node(
        Node(
            "memory1",
            {"joy": 0.9, "energy": 0.7},
            timestamp=950.0,  # Recent
            decay_rate=0.01,
        )
    )
    graph.add_node(
        Node(
            "memory2",
            {"joy": 0.8, "energy": 0.8},
            timestamp=500.0,  # Old
            decay_rate=0.01,
        )
    )
    graph.add_node(
        Node(
            "memory3",
            {"joy": 0.3, "energy": 0.4},
            timestamp=900.0,  # Recent but low similarity
            decay_rate=0.01,
        )
    )

    # Query for joyful memories
    query = {"joy": 1.0, "energy": 0.6}

    # Use composite attention
    metric = AttentionMetric(
        mode="composite",
        composite_weights={"similarity": 0.6, "recency": 0.2, "strength": 0.2},
    )

    scores = metric.compute(query, graph, current_time=current_time)

    # memory1 should score highest (high similarity + recent)
    assert scores["memory1"] > scores["memory2"]
    assert scores["memory1"] > scores["memory3"]

    # Use k-hop to find context
    graph.add_edge(Edge("memory1", "memory2"))
    context = graph.k_hop_neighbors("memory1", k=1)
    assert "memory2" in context


def test_graph_queries_with_temporal_filter():
    """Test combining graph queries with temporal filtering."""
    graph = Graph()
    current_time = 100.0

    # Add mix of temporal and non-temporal nodes
    graph.add_node(Node("recent", timestamp=95.0, decay_rate=0.1))
    graph.add_node(Node("old", timestamp=10.0, decay_rate=0.1))
    graph.add_node(Node("permanent"))

    # Find active nodes
    active = graph.find_nodes(
        lambda n: not n.is_expired(current_time, threshold=0.1)
    )

    assert any(n.id == "recent" for n in active)
    assert any(n.id == "permanent" for n in active)

    # Find expired nodes
    expired = graph.find_nodes(
        lambda n: n.timestamp is not None
        and n.is_expired(current_time, threshold=0.1)
    )

    assert any(n.id == "old" for n in expired)


def test_attention_with_graph_traversal():
    """Test attention metric combined with graph traversal."""
    graph = Graph()

    # Create a small knowledge graph
    graph.add_node(Node("concept1", {"importance": 0.9, "relevance": 0.8}))
    graph.add_node(Node("concept2", {"importance": 0.7, "relevance": 0.6}))
    graph.add_node(Node("concept3", {"importance": 0.5, "relevance": 0.3}))
    graph.add_node(Node("concept4", {"importance": 0.8, "relevance": 0.7}))

    # Add relationships
    graph.add_edge(Edge("concept1", "concept2"))
    graph.add_edge(Edge("concept2", "concept3"))
    graph.add_edge(Edge("concept1", "concept4"))

    # Find important concepts
    important = graph.find_nodes(lambda n: n.features.get("importance", 0) > 0.6)
    assert len(important) == 3

    # Compute attention on subgraph
    important_ids = {n.id for n in important}
    subgraph = graph.subgraph(important_ids)

    metric = AttentionMetric(mode="similarity", similarity_fn="cosine")
    query = {"importance": 1.0, "relevance": 1.0}
    scores = metric.compute(query, subgraph)

    assert scores["concept1"] > scores["concept2"]


def test_temporal_edge_strength():
    """Test temporal edges with varying strength over time."""
    graph = Graph()

    # Add nodes
    graph.add_node(Node("n1"))
    graph.add_node(Node("n2"))
    graph.add_node(Node("n3"))

    # Add edges with different timestamps
    graph.add_edge(Edge("n1", "n2", weight=1.0, timestamp=95.0, decay_rate=0.05))
    graph.add_edge(Edge("n2", "n3", weight=1.0, timestamp=10.0, decay_rate=0.1))

    current_time = 100.0

    # Find strong edges (threshold 0.5)
    strong_edges = graph.filter_edges(
        lambda e: e.compute_strength(current_time) > 0.5
    )

    # Recent edge with low decay should still be strong
    # strength = exp(-0.05 * 5) = exp(-0.25) ≈ 0.78 > 0.5
    assert any(e.source == "n1" and e.target == "n2" for e in strong_edges)

    # Old edge with high decay should be weak
    # strength = exp(-0.1 * 90) = exp(-9) ≈ 0.0001 < 0.5
    weak_edges = graph.filter_edges(lambda e: e.compute_strength(current_time) < 0.5)
    assert any(e.source == "n2" and e.target == "n3" for e in weak_edges)
