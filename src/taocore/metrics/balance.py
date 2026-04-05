"""Balance metric for bounded stability."""

from typing import Dict
from .base import Metric


class BalanceMetric(Metric):
    """Evaluates whether values lie within desirable operating regime."""

    def __init__(self, bounds: Dict[str, tuple[float, float]], **params):
        """
        Args:
            bounds: Dict mapping feature names to (min, max) acceptable ranges
        """
        super().__init__(**params)
        self.bounds = bounds

    def compute(self, values: Dict[str, float]) -> float:
        """
        Compute normalized balance score [0, 1].

        Args:
            values: Named scalar values to evaluate

        Returns:
            Balance score (1.0 = perfect balance, 0.0 = severely out of bounds)
        """
        if not values:
            return 1.0

        scores = []
        for name, value in values.items():
            if name not in self.bounds:
                continue
            min_val, max_val = self.bounds[name]
            if min_val <= value <= max_val:
                scores.append(1.0)
            else:
                # Distance from nearest bound
                dist = min(abs(value - min_val), abs(value - max_val))
                range_size = max_val - min_val
                if range_size == 0:
                    scores.append(0.0)
                else:
                    scores.append(max(0.0, 1.0 - dist / range_size))

        return sum(scores) / len(scores) if scores else 1.0
