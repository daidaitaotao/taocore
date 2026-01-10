"""Node primitive."""

from typing import Dict, Hashable, Optional
import numpy as np


class Node:
    """Entity with numeric state."""

    def __init__(
        self,
        id: Hashable,
        features: Optional[Dict[str, float]] = None,
        timestamp: Optional[float] = None,
        decay_rate: float = 0.0,
    ):
        self.id = id
        self.features: Dict[str, float] = features or {}
        self.timestamp = timestamp
        self.decay_rate = decay_rate

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id

    def age(self, current_time: float) -> Optional[float]:
        """
        Compute age since creation.

        Args:
            current_time: Current timestamp in same units as node timestamp

        Returns:
            Age in time units, or None if node is timeless
        """
        if self.timestamp is None:
            return None
        return current_time - self.timestamp

    def compute_strength(self, current_time: float) -> float:
        """
        Compute current strength with exponential decay.

        Args:
            current_time: Current timestamp

        Returns:
            Strength value in [0, 1] range. 1.0 if timeless or no decay.
            Formula: exp(-decay_rate * age)
        """
        if self.timestamp is None or self.decay_rate == 0.0:
            return 1.0

        age = current_time - self.timestamp
        return float(np.exp(-self.decay_rate * age))

    def is_expired(self, current_time: float, threshold: float = 0.01) -> bool:
        """
        Check if node strength has decayed below threshold.

        Args:
            current_time: Current timestamp
            threshold: Minimum strength to consider active (default 0.01 = 1%)

        Returns:
            True if strength < threshold, False otherwise
        """
        return self.compute_strength(current_time) < threshold

    def __repr__(self):
        parts = [f"id={self.id!r}", f"features={self.features}"]
        if self.timestamp is not None:
            parts.append(f"timestamp={self.timestamp}")
        if self.decay_rate > 0:
            parts.append(f"decay_rate={self.decay_rate}")
        return f"Node({', '.join(parts)})"
