#!/usr/bin/env python3
"""
TaoCore Demo Script

Demonstrates all core functionality:
- Primitives (Node, Edge, Graph, StateVector)
- Metrics (Balance, Flow)
- Equilibrium Solver
- Practical use cases
"""

import numpy as np
from taocore import (
    Node,
    Edge,
    Graph,
    StateVector,
    BalanceMetric,
    FlowMetric,
    EquilibriumSolver,
    Decider,
    Decision,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def demo_primitives():
    """Demonstrate basic primitives."""
    print_section("1. Primitives Demo")

    # Nodes
    print("Creating nodes with features...")
    node_a = Node(id="server_a", features={"cpu": 0.5, "memory": 0.6})
    node_b = Node(id="server_b", features={"cpu": 0.8, "memory": 0.7})
    print(f"  {node_a}")
    print(f"  {node_b}")

    # Edges
    print("\nCreating edges...")
    edge = Edge(source="server_a", target="server_b", weight=1.0)
    print(f"  {edge}")

    # Graph
    print("\nBuilding graph...")
    graph = Graph()
    graph.add_node(node_a)
    graph.add_node(node_b)
    graph.add_edge(edge)
    print(f"  Nodes: {len(graph.nodes())}")
    print(f"  Edges: {len(graph.edges())}")
    print(f"  Neighbors of server_a: {graph.neighbors('server_a')}")

    # StateVector
    print("\nCreating state vectors...")
    state_dict = StateVector({"x": 1.0, "y": 2.0, "z": 3.0})
    state_array = StateVector(np.array([1.0, 2.0, 3.0]))
    print(f"  Dict form: {state_dict}")
    print(f"  Array form: {state_array}")
    print(f"  Distance: {state_dict.distance(state_array):.4f}")


def demo_balance_metric():
    """Demonstrate balance metric for bounded stability."""
    print_section("2. Balance Metric Demo")

    # Define acceptable operating ranges
    metric = BalanceMetric(
        bounds={
            "cpu_usage": (0.0, 80.0),
            "memory_pct": (0.0, 90.0),
            "latency_ms": (0.0, 200.0),
            "error_rate": (0.0, 1.0),
        }
    )

    # Test various system states
    scenarios = [
        {
            "name": "Healthy System",
            "values": {
                "cpu_usage": 45.0,
                "memory_pct": 60.0,
                "latency_ms": 50.0,
                "error_rate": 0.1,
            },
        },
        {
            "name": "High Load",
            "values": {
                "cpu_usage": 75.0,
                "memory_pct": 85.0,
                "latency_ms": 180.0,
                "error_rate": 0.8,
            },
        },
        {
            "name": "Overloaded",
            "values": {
                "cpu_usage": 95.0,
                "memory_pct": 98.0,
                "latency_ms": 350.0,
                "error_rate": 2.5,
            },
        },
    ]

    for scenario in scenarios:
        score = metric.compute(scenario["values"])
        status = "✓ GOOD" if score > 0.8 else "⚠ WARNING" if score > 0.5 else "✗ CRITICAL"
        print(f"{scenario['name']:20} → Balance: {score:.3f}  {status}")


def demo_flow_metric():
    """Demonstrate flow metrics for coherence analysis."""
    print_section("3. Flow Metric Demo")

    # Smooth progression
    smooth_states = [
        StateVector(np.array([0.0, 0.0])),
        StateVector(np.array([1.0, 1.0])),
        StateVector(np.array([2.0, 2.0])),
        StateVector(np.array([3.0, 3.0])),
        StateVector(np.array([4.0, 4.0])),
    ]

    # Erratic changes
    erratic_states = [
        StateVector(np.array([0.0, 0.0])),
        StateVector(np.array([5.0, -2.0])),
        StateVector(np.array([1.0, 8.0])),
        StateVector(np.array([-3.0, 2.0])),
        StateVector(np.array([7.0, -5.0])),
    ]

    # Oscillating
    oscillating_states = [
        StateVector(np.array([1.0, 0.0])),
        StateVector(np.array([0.0, 1.0])),
        StateVector(np.array([-1.0, 0.0])),
        StateVector(np.array([0.0, -1.0])),
        StateVector(np.array([1.0, 0.0])),
    ]

    modes = ["coherence", "volatility", "directionality"]
    datasets = [
        ("Smooth", smooth_states),
        ("Erratic", erratic_states),
        ("Oscillating", oscillating_states),
    ]

    for mode in modes:
        print(f"\n{mode.upper()} Mode:")
        metric = FlowMetric(mode=mode)
        for name, states in datasets:
            score = metric.compute(states)
            print(f"  {name:15} → {score:.3f}")


def demo_equilibrium_solver():
    """Demonstrate equilibrium solver."""
    print_section("4. Equilibrium Solver Demo")

    # Example 1: Simple damping (converges to zero)
    print("Example 1: Damped System (converges to equilibrium)")

    def damped_update(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.9)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    initial = StateVector(np.array([10.0, 5.0]))

    result = solver.solve(initial, damped_update)
    print(f"  Initial state: {initial.array}")
    print(f"  Final state: {result.state.array}")
    print(f"  Converged: {result.converged}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Final residual: {result.residuals[-1]:.2e}")

    # Example 2: Oscillating system (does not converge)
    print("\nExample 2: Oscillating System (no equilibrium)")

    def oscillating_update(state: StateVector) -> StateVector:
        return StateVector(-state.array)

    initial = StateVector(np.array([1.0, 1.0]))
    result = solver.solve(initial, oscillating_update)
    print(f"  Initial state: {initial.array}")
    print(f"  Final state: {result.state.array}")
    print(f"  Converged: {result.converged}")
    print(f"  Iterations: {result.iterations}")

    # Example 3: Attraction to fixed point
    print("\nExample 3: Spring System (converges to center)")

    def spring_update(state: StateVector) -> StateVector:
        # Pull toward origin with damping
        target = np.array([0.0, 0.0])
        force = (target - state.array) * 0.3
        return StateVector(state.array + force)

    initial = StateVector(np.array([5.0, -3.0]))
    result = solver.solve(initial, spring_update)
    print(f"  Initial state: {initial.array}")
    print(f"  Final state: {result.state.array}")
    print(f"  Converged: {result.converged}")
    print(f"  Iterations: {result.iterations}")


def demo_decider():
    """Demonstrate policy-based decision making."""
    print_section("5. Decider Demo")

    # Simple threshold-based decider
    class ThresholdDecider(Decider):
        def decide(self, metrics: dict[str, float]) -> Decision:
            balance = metrics.get("balance", 1.0)
            coherence = metrics.get("coherence", 1.0)

            if balance < 0.5:
                return Decision(
                    action="SCALE_UP",
                    confidence=1.0 - balance,
                    metadata={"reason": "balance critically low"},
                )
            elif balance < 0.7 and coherence < 0.6:
                return Decision(
                    action="INVESTIGATE",
                    confidence=0.7,
                    metadata={"reason": "degraded performance"},
                )
            else:
                return Decision(
                    action="MAINTAIN",
                    confidence=min(balance, coherence),
                    metadata={"reason": "system healthy"},
                )

    decider = ThresholdDecider()

    scenarios = [
        {"balance": 0.95, "coherence": 0.90},
        {"balance": 0.65, "coherence": 0.55},
        {"balance": 0.40, "coherence": 0.70},
    ]

    for i, metrics in enumerate(scenarios, 1):
        decision = decider.decide(metrics)
        print(f"Scenario {i}: balance={metrics['balance']:.2f}, coherence={metrics['coherence']:.2f}")
        print(f"  → Action: {decision.action}")
        print(f"  → Confidence: {decision.confidence:.2f}")
        print(f"  → Reason: {decision.metadata['reason']}\n")


def demo_practical_example():
    """Demonstrate a practical end-to-end example."""
    print_section("6. Practical Example: Service Health Monitor")

    print("Simulating a microservice experiencing load spikes...\n")

    # Define acceptable ranges
    balance_metric = BalanceMetric(
        bounds={
            "cpu": (0.0, 80.0),
            "memory": (0.0, 85.0),
            "latency": (0.0, 200.0),
        }
    )

    # Simulate system states over time
    timeline = []
    states = []

    # Normal operation
    for t in range(5):
        state = {
            "cpu": 40 + np.random.normal(0, 5),
            "memory": 50 + np.random.normal(0, 3),
            "latency": 50 + np.random.normal(0, 10),
        }
        timeline.append(state)
        states.append(StateVector(np.array(list(state.values()))))

    # Load spike
    for t in range(5, 10):
        state = {
            "cpu": 70 + (t - 5) * 5,
            "memory": 75 + (t - 5) * 3,
            "latency": 150 + (t - 5) * 20,
        }
        timeline.append(state)
        states.append(StateVector(np.array(list(state.values()))))

    # Recovery
    for t in range(10, 15):
        state = {
            "cpu": 90 - (t - 10) * 8,
            "memory": 90 - (t - 10) * 6,
            "latency": 250 - (t - 10) * 30,
        }
        timeline.append(state)
        states.append(StateVector(np.array(list(state.values()))))

    # Analyze timeline
    flow_metric = FlowMetric(mode="volatility")

    print(f"{'Time':>4} {'CPU':>6} {'Memory':>7} {'Latency':>8} {'Balance':>8} {'Phase':>12}")
    print("-" * 60)

    for t, (metrics, state) in enumerate(zip(timeline, states)):
        balance = balance_metric.compute(metrics)

        # Determine phase
        if balance > 0.8:
            phase = "HEALTHY"
        elif balance > 0.5:
            phase = "DEGRADED"
        else:
            phase = "CRITICAL"

        print(
            f"{t:4} {metrics['cpu']:6.1f} {metrics['memory']:7.1f} "
            f"{metrics['latency']:8.1f} {balance:8.3f} {phase:>12}"
        )

    # Overall flow analysis
    volatility = flow_metric.compute(states)
    print(f"\nOverall volatility: {volatility:.3f}")
    print("(Higher volatility indicates more turbulent period)")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  TaoCore Demonstration")
    print("  Systems Layer for Stability Analysis")
    print("=" * 60)

    demo_primitives()
    demo_balance_metric()
    demo_flow_metric()
    demo_equilibrium_solver()
    demo_decider()
    demo_practical_example()

    print_section("Demo Complete")
    print("All features demonstrated successfully!")
    print("\nNext steps:")
    print("  - Explore the API: see README.md")
    print("  - Read the design: see docs/rfc1.md")
    print("  - Run tests: make test")
    print()


if __name__ == "__main__":
    main()
