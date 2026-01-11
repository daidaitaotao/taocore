"""Equilibrium solver for finding stable states."""

from typing import Callable, List, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

from ..primitives import StateVector


class ConvergenceReason(Enum):
    """Reason for solver termination."""

    TOLERANCE = "tolerance"  # Residual below tolerance
    MAX_ITERATIONS = "max_iterations"  # Hit iteration limit
    OSCILLATION = "oscillation"  # Detected oscillating behavior
    STABILITY = "stability"  # Stable for N consecutive steps


@dataclass
class EquilibriumResult:
    """
    Result of equilibrium computation.

    Attributes:
        state: Final equilibrium state (or best approximation)
        converged: Whether equilibrium was reached
        iterations: Number of update steps performed
        residuals: History of ||S_{t+1} - S_t|| values
        convergence_reason: Why the solver stopped
        stability_score: Optional stability metric [0, 1]
        oscillation_detected: Whether oscillating behavior was found
    """

    state: StateVector
    converged: bool
    iterations: int
    residuals: List[float]
    convergence_reason: ConvergenceReason
    stability_score: Optional[float] = None
    oscillation_detected: bool = False


class EquilibriumSolver:
    """
    Finds stable states through iterative application of update rules.

    The solver seeks fixed points where S_{t+1} ≈ S_t, representing
    equilibrium states that are stable under the given update dynamics.

    Convergence criteria:
    - Residual threshold: ||S_{t+1} - S_t|| < tolerance
    - Stability window: residual below threshold for N consecutive steps
    - Oscillation detection: periodic state repetition
    - Iteration limit: safety cap on computation

    Diagnostics are first-class outputs for debugging and trust calibration.
    """

    def __init__(
        self,
        max_iterations: int = 1000,
        tolerance: float = 1e-6,
        stability_window: int = 1,
        oscillation_window: int = 10,
        detect_oscillation: bool = True,
    ):
        """
        Args:
            max_iterations: Maximum update steps before termination
            tolerance: Residual threshold for convergence
            stability_window: Consecutive steps below tolerance for stability
            oscillation_window: Number of recent states to check for cycles
            detect_oscillation: Enable oscillation detection
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.stability_window = stability_window
        self.oscillation_window = oscillation_window
        self.detect_oscillation = detect_oscillation

    def solve(
        self,
        initial_state: StateVector,
        update_rule: Callable[[StateVector], StateVector],
    ) -> EquilibriumResult:
        """
        Find equilibrium state through iterative updates.

        Args:
            initial_state: Starting state S_0
            update_rule: Deterministic function F: S_t → S_{t+1}

        Returns:
            EquilibriumResult with final state and comprehensive diagnostics

        Example:
            solver = EquilibriumSolver(tolerance=1e-6)
            result = solver.solve(
                initial_state=StateVector(np.array([1.0, 2.0])),
                update_rule=lambda s: StateVector(s.array * 0.9)
            )

            if result.converged:
                print(f"Equilibrium: {result.state}")
            else:
                print(f"Failed: {result.convergence_reason}")
        """
        state = initial_state
        residuals = []
        stable_steps = 0
        state_history = []  # For oscillation detection

        for iteration in range(self.max_iterations):
            next_state = update_rule(state)
            residual = state.distance(next_state)
            residuals.append(residual)

            # Check tolerance convergence
            if residual < self.tolerance:
                stable_steps += 1

                # Single-step tolerance convergence (backward compatible with RFC-1)
                if self.stability_window == 1:
                    stability_score = self._compute_stability_score(residuals)
                    return EquilibriumResult(
                        state=next_state,
                        converged=True,
                        iterations=iteration + 1,
                        residuals=residuals,
                        convergence_reason=ConvergenceReason.TOLERANCE,
                        stability_score=stability_score,
                        oscillation_detected=False,
                    )

                # Stability window convergence (RFC-3)
                if stable_steps >= self.stability_window:
                    stability_score = self._compute_stability_score(residuals)
                    return EquilibriumResult(
                        state=next_state,
                        converged=True,
                        iterations=iteration + 1,
                        residuals=residuals,
                        convergence_reason=ConvergenceReason.STABILITY,
                        stability_score=stability_score,
                        oscillation_detected=False,
                    )
            else:
                stable_steps = 0

            # Oscillation detection
            if self.detect_oscillation:
                state_history.append(next_state)
                if len(state_history) > self.oscillation_window:
                    state_history.pop(0)

                if self._detect_oscillation(state_history):
                    stability_score = self._compute_stability_score(residuals)
                    return EquilibriumResult(
                        state=next_state,
                        converged=False,
                        iterations=iteration + 1,
                        residuals=residuals,
                        convergence_reason=ConvergenceReason.OSCILLATION,
                        stability_score=stability_score,
                        oscillation_detected=True,
                    )

            state = next_state

        # Max iterations reached
        stability_score = self._compute_stability_score(residuals)
        oscillation_detected = (
            self._detect_oscillation(state_history) if self.detect_oscillation else False
        )

        return EquilibriumResult(
            state=state,
            converged=False,
            iterations=self.max_iterations,
            residuals=residuals,
            convergence_reason=ConvergenceReason.MAX_ITERATIONS,
            stability_score=stability_score,
            oscillation_detected=oscillation_detected,
        )

    def _detect_oscillation(self, state_history: List[StateVector]) -> bool:
        """
        Detect periodic oscillation in recent states.

        Looks for state repetition within the oscillation window,
        indicating the system is cycling rather than converging.

        Args:
            state_history: Recent states (length ≤ oscillation_window)

        Returns:
            True if oscillation detected, False otherwise
        """
        if len(state_history) < 3:
            return False

        # Check for 2-cycle (most common)
        if len(state_history) >= 2:
            s1, s2 = state_history[-2], state_history[-1]
            if len(state_history) >= 4:
                s3, s4 = state_history[-4], state_history[-3]
                # Check if [s3, s4] ≈ [s1, s2]
                if s1.distance(s3) < self.tolerance and s2.distance(s4) < self.tolerance:
                    return True

        # Check for 3-cycle
        if len(state_history) >= 6:
            recent = state_history[-3:]
            earlier = state_history[-6:-3]
            cycle_match = all(
                recent[i].distance(earlier[i]) < self.tolerance for i in range(3)
            )
            if cycle_match:
                return True

        # Check for any recent state appearing again
        if len(state_history) >= self.oscillation_window:
            latest = state_history[-1]
            for i in range(len(state_history) - 2):
                if latest.distance(state_history[i]) < self.tolerance:
                    return True

        return False

    def _compute_stability_score(self, residuals: List[float]) -> float:
        """
        Compute stability metric from residual history.

        Score indicates how stable the final state is:
        - 1.0: Perfect convergence (final residual → 0)
        - 0.5: Moderate stability
        - 0.0: Highly unstable (large residuals)

        Args:
            residuals: History of ||S_{t+1} - S_t|| values

        Returns:
            Stability score in [0, 1]
        """
        if not residuals:
            return 0.0

        # Use recent residuals for stability assessment
        recent_window = min(10, len(residuals))
        recent = residuals[-recent_window:]

        # Mean and variance of recent residuals
        mean_residual = np.mean(recent)
        std_residual = np.std(recent)

        # Determine scale based on initial residual for normalization
        initial_residual = max(residuals[0], 1e-10)
        scale = max(initial_residual * 0.1, self.tolerance * 10)

        # Score based on mean (lower is better)
        # Use log scale to handle wide range of residuals
        if mean_residual < self.tolerance:
            mean_score = 1.0
        else:
            mean_score = max(0.0, 1.0 - np.log10(mean_residual / self.tolerance))
            mean_score = np.clip(mean_score, 0.0, 1.0)

        # Score based on variance (lower is better)
        if std_residual < self.tolerance:
            variance_score = 1.0
        else:
            variance_score = max(0.0, 1.0 - np.log10(std_residual / self.tolerance))
            variance_score = np.clip(variance_score, 0.0, 1.0)

        # Combined score (geometric mean)
        stability_score = np.sqrt(mean_score * variance_score)

        return float(np.clip(stability_score, 0.0, 1.0))
