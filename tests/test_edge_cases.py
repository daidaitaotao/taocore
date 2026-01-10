"""Edge case tests for TaoCore."""

import numpy as np
import pytest
from taocore import (
    Node,
    Edge,
    Graph,
    StateVector,
    BalanceMetric,
    FlowMetric,
    EquilibriumSolver,
)


def test_empty_graph():
    """Test graph with no nodes."""
    graph = Graph()
    assert len(graph.nodes()) == 0
    assert len(graph.edges()) == 0
    assert graph.neighbors("nonexistent") == set()


def test_node_with_no_features():
    """Test node without features."""
    node = Node(id="empty")
    assert node.features == {}
    assert hash(node) == hash("empty")


def test_graph_nonexistent_node():
    """Test querying nonexistent node."""
    graph = Graph()
    result = graph.get_node("does_not_exist")
    assert result is None


def test_edge_with_zero_weight():
    """Test edge with zero weight."""
    edge = Edge(source="a", target="b", weight=0.0)
    assert edge.weight == 0.0


def test_edge_with_negative_weight():
    """Test edge with negative weight."""
    edge = Edge(source="a", target="b", weight=-1.5)
    assert edge.weight == -1.5


def test_state_vector_empty_dict():
    """Test state vector with empty dict."""
    state = StateVector({})
    assert len(state.array) == 0
    assert state.dict == {}


def test_state_vector_single_value():
    """Test state vector with single value."""
    state = StateVector({"x": 5.0})
    assert state.array[0] == 5.0
    assert state.dict["x"] == 5.0


def test_state_vector_distance_to_self():
    """Test distance from state to itself."""
    state = StateVector(np.array([1.0, 2.0, 3.0]))
    distance = state.distance(state)
    assert distance == 0.0


def test_balance_metric_empty_values():
    """Test balance metric with empty values."""
    metric = BalanceMetric(bounds={"x": (0.0, 10.0)})
    score = metric.compute({})
    assert score == 1.0  # No values to violate bounds


def test_balance_metric_unknown_key():
    """Test balance metric with unknown feature."""
    metric = BalanceMetric(bounds={"x": (0.0, 10.0)})
    score = metric.compute({"x": 5.0, "y": 100.0})  # y not in bounds
    assert score == 1.0  # Only evaluates known keys


def test_balance_metric_multiple_violations():
    """Test balance metric with multiple out-of-bounds values."""
    metric = BalanceMetric(bounds={"x": (0.0, 10.0), "y": (0.0, 5.0)})
    score = metric.compute({"x": 20.0, "y": 10.0})
    assert score < 1.0


def test_flow_metric_single_state():
    """Test flow metric with only one state."""
    states = [StateVector(np.array([1.0, 2.0]))]
    metric = FlowMetric(mode="coherence")
    score = metric.compute(states)
    assert score == 0.0


def test_flow_metric_two_identical_states():
    """Test flow metric with identical states."""
    state = StateVector(np.array([1.0, 2.0]))
    states = [state, state]
    metric = FlowMetric(mode="volatility")
    score = metric.compute(states)
    assert score == 0.0  # No change


def test_flow_metric_zero_movement():
    """Test flow metric with zero magnitude movements."""
    states = [
        StateVector(np.array([1.0, 1.0])),
        StateVector(np.array([1.0, 1.0])),
        StateVector(np.array([1.0, 1.0])),
    ]
    metric = FlowMetric(mode="directionality")
    score = metric.compute(states)
    assert isinstance(score, float)


def test_equilibrium_already_converged():
    """Test equilibrium solver with already-converged state."""

    def identity_update(state: StateVector) -> StateVector:
        return state

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    initial = StateVector(np.array([1.0, 2.0]))

    result = solver.solve(initial, identity_update)

    assert result.converged
    assert result.iterations == 1
    assert result.residuals[0] == 0.0


def test_equilibrium_no_convergence():
    """Test equilibrium solver that doesn't converge."""

    def diverging_update(state: StateVector) -> StateVector:
        """Update that oscillates."""
        return StateVector(-state.array)

    solver = EquilibriumSolver(max_iterations=10, tolerance=1e-6)
    initial = StateVector(np.array([1.0, 2.0]))

    result = solver.solve(initial, diverging_update)

    assert not result.converged
    assert result.iterations == 10
    assert len(result.residuals) == 10


def test_equilibrium_very_large_values():
    """Test equilibrium with very large initial values."""

    def damping_update(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.1)

    solver = EquilibriumSolver(max_iterations=1000, tolerance=1e-6)
    initial = StateVector(np.array([1e6, 1e6]))

    result = solver.solve(initial, damping_update)

    assert result.converged
    assert np.allclose(result.state.array, 0.0, atol=1e-5)


def test_node_equality():
    """Test node equality based on ID."""
    n1 = Node(id="same", features={"x": 1.0})
    n2 = Node(id="same", features={"x": 2.0})
    n3 = Node(id="different", features={"x": 1.0})

    assert n1 == n2  # Same ID
    assert n1 != n3  # Different ID
    assert n1 != "not a node"


def test_graph_duplicate_nodes():
    """Test adding same node multiple times."""
    graph = Graph()
    node = Node(id="n1", features={"x": 1.0})

    graph.add_node(node)
    graph.add_node(node)  # Add again

    assert len(graph.nodes()) == 1  # Should not duplicate


def test_graph_self_loop():
    """Test graph with self-loop edge."""
    graph = Graph()
    graph.add_node(Node("n1"))
    graph.add_edge(Edge("n1", "n1", 1.0))

    assert "n1" in graph.neighbors("n1")


def test_metric_get_params():
    """Test metric parameter retrieval."""
    metric = BalanceMetric(
        bounds={"x": (0.0, 10.0)}, custom_param="test_value"
    )

    params = metric.get_params()
    assert "custom_param" in params
    assert params["custom_param"] == "test_value"
