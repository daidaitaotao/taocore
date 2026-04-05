"""State vector primitive."""

from typing import Dict, Union
import numpy as np


class StateVector:
    """Numeric state representation that can be updated by rules."""

    def __init__(self, values: Union[Dict[str, float], np.ndarray]):
        if isinstance(values, dict):
            # Use sorted keys for deterministic alignment across dicts
            self._keys = sorted(values.keys())
            self._dict = values
            self._array = np.array([values[k] for k in self._keys])
        else:
            self._array = np.asarray(values)
            self._dict = {}
            self._keys = []

    @property
    def array(self) -> np.ndarray:
        """Get array representation."""
        return self._array

    @property
    def dict(self) -> Dict[str, float]:
        """Get dict representation."""
        return self._dict

    def distance(self, other: "StateVector") -> float:
        """Compute L2 distance to another state."""
        if self._keys or other._keys:
            if self._keys != other._keys:
                raise ValueError(
                    "StateVector key mismatch; ensure dict-based vectors use the same keys."
                )
        if self._array.shape != other._array.shape:
            raise ValueError("StateVector shape mismatch; arrays must have same shape.")
        return float(np.linalg.norm(self._array - other._array))

    def __repr__(self):
        if self._dict:
            return f"StateVector({self._dict})"
        return f"StateVector(shape={self._array.shape})"
