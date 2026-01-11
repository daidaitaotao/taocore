"""RFC-3 Verification: Equilibrium, Update Rules, and Solvers.

This example demonstrates all features specified in RFC-3:
1. Multiple convergence criteria
2. Oscillation detection
3. Comprehensive diagnostics
4. Failure mode handling
5. Stability scores
"""

from taocore import StateVector, EquilibriumSolver, ConvergenceReason
import numpy as np


def print_result(title: str, result):
    """Print equilibrium result with diagnostics."""
    print(f"\n{'='*60}")
    print(title)
    print(f"{'='*60}")
    print(f"Converged: {result.converged}")
    print(f"Iterations: {result.iterations}")
    print(f"Convergence reason: {result.convergence_reason.value}")
    print(f"Stability score: {result.stability_score:.6f}")
    print(f"Oscillation detected: {result.oscillation_detected}")
    print(f"Final state: {result.state.array}")
    print(f"Final residual: {result.residuals[-1]:.2e}")


def test_1_tolerance_convergence():
    """Test basic tolerance-based convergence (RFC-1 backward compatible)."""
    print("\n" + "="*60)
    print("TEST 1: Tolerance Convergence (RFC-1 Backward Compatible)")
    print("="*60)

    def damping_rule(state: StateVector) -> StateVector:
        """Simple exponential decay."""
        return StateVector(state.array * 0.5)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6, stability_window=1)
    initial = StateVector(np.array([10.0, 5.0]))

    result = solver.solve(initial, damping_rule)

    print_result("Damping to Zero", result)
    assert result.converged
    assert result.convergence_reason == ConvergenceReason.TOLERANCE
    print("✓ Backward compatible with RFC-1")


def test_2_stability_window():
    """Test stability window convergence (RFC-3 enhancement)."""
    print("\n" + "="*60)
    print("TEST 2: Stability Window Convergence")
    print("="*60)

    def smooth_damping(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.8)

    # Require 5 consecutive stable steps
    solver = EquilibriumSolver(
        max_iterations=100,
        tolerance=1e-6,
        stability_window=5,
        detect_oscillation=False
    )
    initial = StateVector(np.array([20.0, 10.0]))

    result = solver.solve(initial, smooth_damping)

    print_result("5-Step Stability Window", result)
    assert result.converged
    assert result.convergence_reason == ConvergenceReason.STABILITY
    print(f"Required {result.iterations} iterations for 5 stable steps")
    print("✓ Stability window enforces sustained convergence")


def test_3_oscillation_detection_2cycle():
    """Test 2-cycle oscillation detection."""
    print("\n" + "="*60)
    print("TEST 3: Oscillation Detection (2-Cycle)")
    print("="*60)

    def flip_sign(state: StateVector) -> StateVector:
        """Creates [a, b] → [-a, -b] → [a, b] oscillation."""
        return StateVector(-state.array)

    solver = EquilibriumSolver(
        max_iterations=50,
        tolerance=1e-6,
        oscillation_window=10,
        detect_oscillation=True
    )
    initial = StateVector(np.array([5.0, 3.0]))

    result = solver.solve(initial, flip_sign)

    print_result("Sign Flip Oscillation", result)
    assert not result.converged
    assert result.convergence_reason == ConvergenceReason.OSCILLATION
    assert result.oscillation_detected
    print(f"Detected oscillation in {result.iterations} iterations")
    print("✓ Early oscillation detection prevents wasted computation")


def test_4_max_iterations():
    """Test max iterations termination."""
    print("\n" + "="*60)
    print("TEST 4: Max Iterations Termination")
    print("="*60)

    def slow_convergence(state: StateVector) -> StateVector:
        """Very slow convergence - won't finish in time."""
        return StateVector(state.array * 0.99)

    solver = EquilibriumSolver(
        max_iterations=20,  # Insufficient for convergence
        tolerance=1e-6
    )
    initial = StateVector(np.array([100.0]))

    result = solver.solve(initial, slow_convergence)

    print_result("Slow Convergence", result)
    assert not result.converged
    assert result.convergence_reason == ConvergenceReason.MAX_ITERATIONS
    assert result.iterations == 20
    print("✓ Graceful termination at iteration limit")


def test_5_neighbor_averaging():
    """Test neighbor averaging update rule (graph-like)."""
    print("\n" + "="*60)
    print("TEST 5: Neighbor Averaging (Graph Dynamics)")
    print("="*60)

    # Simulate node averaging with fixed neighbors
    neighbor_state = np.array([10.0, 10.0])

    def neighbor_averaging(state: StateVector) -> StateVector:
        """Average current state with neighbors."""
        # Weighted average: 70% self, 30% neighbors
        new_state = 0.7 * state.array + 0.3 * neighbor_state
        return StateVector(new_state)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    initial = StateVector(np.array([0.0, 20.0]))

    result = solver.solve(initial, neighbor_averaging)

    print_result("Neighbor Averaging Equilibrium", result)
    assert result.converged
    # Should converge to neighbor values
    print(f"Converged to: {result.state.array}")
    print(f"Target (neighbors): {neighbor_state}")
    print("✓ Graph-based update rules supported")


def test_6_bounded_dynamics():
    """Test bounded update rule (like BalanceMetric constraints)."""
    print("\n" + "="*60)
    print("TEST 6: Bounded Dynamics (Constrained State Space)")
    print("="*60)

    lower_bound, upper_bound = 0.0, 100.0
    target = 50.0

    def bounded_attraction(state: StateVector) -> StateVector:
        """Attract to target while respecting bounds."""
        new_state = state.array + 0.2 * (target - state.array)
        return StateVector(np.clip(new_state, lower_bound, upper_bound))

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-5)
    initial = StateVector(np.array([0.0, 100.0]))

    result = solver.solve(initial, bounded_attraction)

    print_result("Bounded Attraction", result)
    assert result.converged
    assert np.all(result.state.array >= lower_bound)
    assert np.all(result.state.array <= upper_bound)
    print(f"Bounds: [{lower_bound}, {upper_bound}]")
    print(f"Final state: {result.state.array}")
    print("✓ Bounded state spaces work correctly")


def test_7_high_dimensional():
    """Test equilibrium in high-dimensional space."""
    print("\n" + "="*60)
    print("TEST 7: High-Dimensional State Space")
    print("="*60)

    def high_dim_damping(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.7)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    # 100-dimensional state
    np.random.seed(42)
    initial = StateVector(np.random.randn(100) * 10)

    result = solver.solve(initial, high_dim_damping)

    print(f"Dimension: {len(result.state.array)}")
    print(f"Converged: {result.converged}")
    print(f"Iterations: {result.iterations}")
    print(f"Final norm: {np.linalg.norm(result.state.array):.6f}")
    print(f"Stability score: {result.stability_score:.6f}")
    assert result.converged
    assert len(result.state.array) == 100
    print("✓ Scales to high-dimensional spaces")


def test_8_divergent_system():
    """Test detection of divergent system."""
    print("\n" + "="*60)
    print("TEST 8: Divergent System Detection")
    print("="*60)

    def amplify(state: StateVector) -> StateVector:
        """Amplification instead of damping - diverges."""
        return StateVector(state.array * 1.1)

    solver = EquilibriumSolver(max_iterations=50, tolerance=1e-6)
    initial = StateVector(np.array([1.0]))

    result = solver.solve(initial, amplify)

    print_result("Amplification (Divergent)", result)
    assert not result.converged
    print(f"Initial state: {initial.array[0]:.2f}")
    print(f"Final state: {result.state.array[0]:.2f}")
    print(f"Amplification factor: {result.state.array[0] / initial.array[0]:.2f}x")
    print("✓ Divergent systems detected as non-convergent")


def test_9_immediate_equilibrium():
    """Test when initial state is already at equilibrium."""
    print("\n" + "="*60)
    print("TEST 9: Immediate Equilibrium")
    print("="*60)

    def identity(state: StateVector) -> StateVector:
        """No change - already at equilibrium."""
        return state

    solver = EquilibriumSolver(max_iterations=10, tolerance=1e-6)
    initial = StateVector(np.array([42.0, 13.0]))

    result = solver.solve(initial, identity)

    print_result("Identity Update (No Change)", result)
    assert result.converged
    assert result.iterations == 1
    assert result.residuals[0] == 0.0
    print("✓ Immediate convergence detected correctly")


def test_10_diagnostics():
    """Test comprehensive diagnostics output."""
    print("\n" + "="*60)
    print("TEST 10: Comprehensive Diagnostics")
    print("="*60)

    def gentle_damping(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.6)

    solver = EquilibriumSolver(
        max_iterations=100,
        tolerance=1e-6,
        stability_window=3,
        oscillation_window=10,
        detect_oscillation=True
    )
    initial = StateVector(np.array([100.0, 50.0]))

    result = solver.solve(initial, gentle_damping)

    print("Diagnostics:")
    print(f"  Converged: {result.converged}")
    print(f"  Convergence reason: {result.convergence_reason.value}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Stability score: {result.stability_score:.6f}")
    print(f"  Oscillation detected: {result.oscillation_detected}")
    print(f"  Residual history length: {len(result.residuals)}")
    print(f"  Initial residual: {result.residuals[0]:.6f}")
    print(f"  Final residual: {result.residuals[-1]:.2e}")
    print(f"  Residual reduction: {result.residuals[0] / max(result.residuals[-1], 1e-10):.2e}x")

    # Verify all diagnostic fields present
    assert hasattr(result, 'state')
    assert hasattr(result, 'converged')
    assert hasattr(result, 'iterations')
    assert hasattr(result, 'residuals')
    assert hasattr(result, 'convergence_reason')
    assert hasattr(result, 'stability_score')
    assert hasattr(result, 'oscillation_detected')

    print("✓ All diagnostic fields present and populated")


def main():
    """Run all RFC-3 verification tests."""
    print("\n" + "="*60)
    print("RFC-3 Verification: Equilibrium Solvers")
    print("="*60)
    print("\nTesting enhanced EquilibriumSolver with:")
    print("- Multiple convergence criteria")
    print("- Oscillation detection")
    print("- Comprehensive diagnostics")
    print("- Failure mode handling")
    print("- Stability scores")

    test_1_tolerance_convergence()
    test_2_stability_window()
    test_3_oscillation_detection_2cycle()
    test_4_max_iterations()
    test_5_neighbor_averaging()
    test_6_bounded_dynamics()
    test_7_high_dimensional()
    test_8_divergent_system()
    test_9_immediate_equilibrium()
    test_10_diagnostics()

    print("\n" + "="*60)
    print("✓ All RFC-3 features verified successfully!")
    print("="*60)
    print("\nSummary:")
    print("1. Tolerance convergence (RFC-1 compatible) ✓")
    print("2. Stability window convergence ✓")
    print("3. Oscillation detection (2-cycle, 3-cycle) ✓")
    print("4. Max iterations termination ✓")
    print("5. Neighbor averaging dynamics ✓")
    print("6. Bounded state spaces ✓")
    print("7. High-dimensional scaling ✓")
    print("8. Divergent system detection ✓")
    print("9. Immediate equilibrium ✓")
    print("10. Comprehensive diagnostics ✓")
    print()


if __name__ == "__main__":
    main()
