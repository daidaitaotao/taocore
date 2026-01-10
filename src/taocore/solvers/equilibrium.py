"""Equilibrium solver for finding stable states."""

from typing import Callable, List
from dataclasses import dataclass

from ..primitives import StateVector


@dataclass
class EquilibriumResult:
    """Result of equilibrium computation."""

    state: StateVector
    converged: bool
    iterations: int
    residuals: List[float]


class EquilibriumSolver:
    """Finds stable states through iterative updates."""

    def __init__(
        self,
        max_iterations: int = 1000,
        tolerance: float = 1e-6,
    ):
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def solve(
        self,
        initial_state: StateVector,
        update_rule: Callable[[StateVector], StateVector],
    ) -> EquilibriumResult:
        """
        Find equilibrium state.

        Args:
            initial_state: Starting state
            update_rule: Function S_t -> S_{t+1}

        Returns:
            EquilibriumResult with final state and diagnostics
        """
        state = initial_state
        residuals = []

        for iteration in range(self.max_iterations):
            next_state = update_rule(state)
            residual = state.distance(next_state)
            residuals.append(residual)

            if residual < self.tolerance:
                return EquilibriumResult(
                    state=next_state,
                    converged=True,
                    iterations=iteration + 1,
                    residuals=residuals,
                )

            state = next_state

        return EquilibriumResult(
            state=state,
            converged=False,
            iterations=self.max_iterations,
            residuals=residuals,
        )
