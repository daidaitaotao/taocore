"""Test equilibrium solver."""

import numpy as np
from taocore import EquilibriumSolver, StateVector


def test_equilibrium_solver():
    """Test EquilibriumSolver convergence."""
    def damping_rule(state: StateVector) -> StateVector:
        """Simple damping: multiply by 0.5."""
        return StateVector(state.array * 0.5)

    solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
    initial = StateVector(np.array([10.0, 10.0]))

    result = solver.solve(initial, damping_rule)

    assert result.converged
    assert result.iterations < 100
    assert len(result.residuals) > 0
    assert np.allclose(result.state.array, 0.0, atol=1e-5)
