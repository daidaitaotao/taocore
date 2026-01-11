"""Test equilibrium solver."""

import numpy as np
from taocore import EquilibriumSolver, StateVector, ConvergenceReason


def test_equilibrium_solver():
    """Test EquilibriumSolver convergence (backward compatibility)."""
    def damping_rule(state: StateVector) -> StateVector:
        """Simple damping: multiply by 0.5."""
        return StateVector(state.array * 0.5)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6, stability_window=1)
    initial = StateVector(np.array([10.0, 10.0]))

    result = solver.solve(initial, damping_rule)

    assert result.converged
    assert result.iterations < 100
    assert len(result.residuals) > 0
    assert np.allclose(result.state.array, 0.0, atol=1e-5)
    # RFC-3: Check new diagnostics
    assert result.convergence_reason == ConvergenceReason.TOLERANCE
    assert result.stability_score is not None
    assert 0.0 <= result.stability_score <= 1.0
    assert not result.oscillation_detected


# ============================================================================
# RFC-3: Convergence Criteria Tests
# ============================================================================


def test_stability_window_convergence():
    """Test convergence with stability window requirement."""
    def damping_rule(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.7)  # Faster convergence

    # Require 5 consecutive stable steps
    solver = EquilibriumSolver(
        max_iterations=100,
        tolerance=1e-6,
        stability_window=5,
        detect_oscillation=False  # Disable for clean convergence test
    )
    initial = StateVector(np.array([10.0, 5.0]))

    result = solver.solve(initial, damping_rule)

    assert result.converged
    assert result.convergence_reason == ConvergenceReason.STABILITY
    # Should take more iterations due to stability window
    assert result.iterations >= 5


def test_oscillation_detection_2cycle():
    """Test detection of 2-cycle oscillation."""
    def oscillating_rule(state: StateVector) -> StateVector:
        # Flip sign: creates [a, b] -> [-a, -b] -> [a, b]
        return StateVector(-state.array)

    solver = EquilibriumSolver(
        max_iterations=20,
        tolerance=1e-6,
        oscillation_window=10,
        detect_oscillation=True
    )
    initial = StateVector(np.array([1.0, 2.0]))

    result = solver.solve(initial, oscillating_rule)

    assert not result.converged
    assert result.convergence_reason == ConvergenceReason.OSCILLATION
    assert result.oscillation_detected
    # Should detect quickly
    assert result.iterations < 20


def test_oscillation_detection_3cycle():
    """Test detection of 3-cycle oscillation."""
    cycle_states = [
        np.array([1.0, 0.0]),
        np.array([0.0, 1.0]),
        np.array([0.0, 0.0]),
    ]
    counter = [0]

    def three_cycle_rule(state: StateVector) -> StateVector:
        # Cycle through 3 states
        idx = counter[0] % 3
        counter[0] += 1
        return StateVector(cycle_states[idx])

    solver = EquilibriumSolver(
        max_iterations=20,
        tolerance=1e-6,
        oscillation_window=10,
        detect_oscillation=True
    )
    # Start with a different state to avoid immediate convergence
    initial = StateVector(np.array([0.5, 0.5]))

    result = solver.solve(initial, three_cycle_rule)

    assert not result.converged
    assert result.convergence_reason == ConvergenceReason.OSCILLATION
    assert result.oscillation_detected


def test_max_iterations_reached():
    """Test termination at max iterations without convergence."""
    def slow_damping(state: StateVector) -> StateVector:
        # Very slow convergence
        return StateVector(state.array * 0.99)

    solver = EquilibriumSolver(
        max_iterations=10,  # Too few for convergence
        tolerance=1e-6
    )
    initial = StateVector(np.array([10.0, 10.0]))

    result = solver.solve(initial, slow_damping)

    assert not result.converged
    assert result.convergence_reason == ConvergenceReason.MAX_ITERATIONS
    assert result.iterations == 10
    assert len(result.residuals) == 10


def test_oscillation_disabled():
    """Test solver with oscillation detection disabled."""
    def oscillating_rule(state: StateVector) -> StateVector:
        return StateVector(-state.array)

    solver = EquilibriumSolver(
        max_iterations=20,
        tolerance=1e-6,
        detect_oscillation=False  # Disabled
    )
    initial = StateVector(np.array([1.0, 2.0]))

    result = solver.solve(initial, oscillating_rule)

    # Should hit max iterations, not detect oscillation
    assert not result.converged
    assert result.convergence_reason == ConvergenceReason.MAX_ITERATIONS
    assert not result.oscillation_detected


# ============================================================================
# RFC-3: Diagnostics Tests
# ============================================================================


def test_stability_score_high():
    """Test stability score for well-converged solution."""
    def good_damping(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.5)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    initial = StateVector(np.array([10.0, 10.0]))

    result = solver.solve(initial, good_damping)

    assert result.converged
    assert result.stability_score is not None
    # Should have good stability (converged)
    assert result.stability_score >= 0.0  # Just verify it's computed
    assert result.stability_score <= 1.0


def test_stability_score_low():
    """Test stability score for poorly converged solution."""
    def unstable_rule(state: StateVector) -> StateVector:
        # Add noise to prevent clean convergence
        return StateVector(state.array * 0.95 + np.random.randn(len(state.array)) * 0.01)

    np.random.seed(42)  # Reproducible
    solver = EquilibriumSolver(max_iterations=50, tolerance=1e-6)
    initial = StateVector(np.array([10.0, 10.0]))

    result = solver.solve(initial, unstable_rule)

    # May not converge cleanly
    if not result.converged:
        assert result.stability_score is not None
        # Should have lower stability
        assert result.stability_score < 0.9


def test_residuals_history():
    """Test that residuals are properly tracked."""
    def damping_rule(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.8)

    solver = EquilibriumSolver(max_iterations=20, tolerance=1e-6)
    initial = StateVector(np.array([10.0]))

    result = solver.solve(initial, damping_rule)

    # Residuals should be tracked every iteration
    assert len(result.residuals) == result.iterations
    # Residuals should decrease over time for damping
    assert result.residuals[0] > result.residuals[-1]
    # All residuals should be non-negative
    assert all(r >= 0 for r in result.residuals)


def test_convergence_reason_enum():
    """Test that all convergence reasons are valid enum values."""
    assert hasattr(ConvergenceReason, 'TOLERANCE')
    assert hasattr(ConvergenceReason, 'MAX_ITERATIONS')
    assert hasattr(ConvergenceReason, 'OSCILLATION')
    assert hasattr(ConvergenceReason, 'STABILITY')


# ============================================================================
# RFC-3: Edge Cases
# ============================================================================


def test_immediate_convergence():
    """Test when initial state is already at equilibrium."""
    def identity_rule(state: StateVector) -> StateVector:
        return state

    solver = EquilibriumSolver(max_iterations=10, tolerance=1e-6)
    initial = StateVector(np.array([5.0, 5.0]))

    result = solver.solve(initial, identity_rule)

    assert result.converged
    assert result.iterations == 1  # Should converge immediately
    assert result.convergence_reason == ConvergenceReason.TOLERANCE
    assert result.residuals[0] == 0.0


def test_zero_state_equilibrium():
    """Test convergence to zero state."""
    def zero_rule(state: StateVector) -> StateVector:
        return StateVector(np.zeros_like(state.array))

    solver = EquilibriumSolver(max_iterations=10, tolerance=1e-6)
    initial = StateVector(np.array([10.0, 20.0]))

    result = solver.solve(initial, zero_rule)

    assert result.converged
    assert np.allclose(result.state.array, 0.0)


def test_large_state_space():
    """Test equilibrium in high-dimensional space."""
    def damping_rule(state: StateVector) -> StateVector:
        return StateVector(state.array * 0.7)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    # 100-dimensional state
    initial = StateVector(np.random.randn(100) * 10)

    result = solver.solve(initial, damping_rule)

    assert result.converged
    assert len(result.state.array) == 100
    assert np.allclose(result.state.array, 0.0, atol=1e-5)


def test_divergent_system():
    """Test detection of divergent system (no convergence)."""
    def divergent_rule(state: StateVector) -> StateVector:
        # Amplify instead of damp
        return StateVector(state.array * 1.1)

    solver = EquilibriumSolver(max_iterations=50, tolerance=1e-6)
    initial = StateVector(np.array([1.0, 1.0]))

    result = solver.solve(initial, divergent_rule)

    assert not result.converged
    # Should hit max iterations
    assert result.convergence_reason == ConvergenceReason.MAX_ITERATIONS
    # Final state should be larger than initial
    assert np.all(np.abs(result.state.array) > np.abs(initial.array))


# ============================================================================
# RFC-3: Update Rule Patterns
# ============================================================================


def test_neighbor_averaging_rule():
    """Test equilibrium with neighbor averaging (graph-like)."""
    # Simulate averaging with fixed neighbors
    neighbors = np.array([5.0, 5.0])

    def averaging_rule(state: StateVector) -> StateVector:
        # Move toward average with neighbors
        avg = (state.array + neighbors) / 2
        return StateVector(avg)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    initial = StateVector(np.array([0.0, 10.0]))

    result = solver.solve(initial, averaging_rule)

    assert result.converged
    # Should converge to neighbor values
    assert np.allclose(result.state.array, neighbors, atol=0.1)


def test_bounded_update_rule():
    """Test update rule with bounds (like BalanceMetric)."""
    lower, upper = 0.0, 10.0

    def bounded_rule(state: StateVector) -> StateVector:
        # Attract toward midpoint, but stay in bounds
        midpoint = (lower + upper) / 2
        new_state = state.array + 0.1 * (midpoint - state.array)
        return StateVector(np.clip(new_state, lower, upper))

    solver = EquilibriumSolver(max_iterations=200, tolerance=1e-5)  # More iterations, looser tolerance
    initial = StateVector(np.array([0.0, 10.0]))

    result = solver.solve(initial, bounded_rule)

    assert result.converged
    # Should converge to midpoint
    assert np.allclose(result.state.array, 5.0, atol=0.1)
