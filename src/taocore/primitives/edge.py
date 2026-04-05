"""Edge primitive."""

from typing import Hashable, Optional
import numpy as np


class Edge:
    """Directed or undirected relationship with weight."""

    def __init__(
        self,
        source: Hashable,
        target: Hashable,
        weight: float = 1.0,
        directed: bool = True,
        timestamp: Optional[float] = None,
        decay_rate: float = 0.0,
    ):
        self.source = source
        self.target = target
        self.weight = weight
        self.directed = directed
        self.timestamp = timestamp
        self.decay_rate = decay_rate

    def age(self, current_time: float) -> Optional[float]:
        """
        Compute edge age.

        Args:
            current_time: Current timestamp in same units as edge timestamp

        Returns:
            Age in time units, or None if edge is timeless
        """
        if self.timestamp is None:
            return None
        return current_time - self.timestamp

    def compute_strength(self, current_time: float) -> float:
        """
        Compute effective edge weight with decay.

        Args:
            current_time: Current timestamp

        Returns:
            Effective weight = base_weight * exp(-decay_rate * age)
        """
        if self.timestamp is None or self.decay_rate == 0.0:
            return self.weight

        age = current_time - self.timestamp
        decay_factor = float(np.exp(-self.decay_rate * age))
        return self.weight * decay_factor

    def is_expired(self, current_time: float, threshold: float = 0.01) -> bool:
        """
        Check if edge has decayed below threshold strength.

        Args:
            current_time: Current timestamp
            threshold: Minimum strength to consider active (default 0.01 = 1%)

        Returns:
            True if edge strength below threshold, False otherwise
        """
        if self.weight == 0.0:
            return True
        relative_strength = self.compute_strength(current_time) / abs(self.weight)
        return relative_strength < threshold

    def __repr__(self):
        parts = [
            f"source={self.source!r}",
            f"target={self.target!r}",
            f"weight={self.weight}",
        ]
        if not self.directed:
            parts.append("directed=False")
        if self.timestamp is not None:
            parts.append(f"timestamp={self.timestamp}")
        if self.decay_rate > 0:
            parts.append(f"decay_rate={self.decay_rate}")
        return f"Edge({', '.join(parts)})"
