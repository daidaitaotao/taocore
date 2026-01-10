"""Flow metric for directional change."""

from typing import List
import numpy as np
from .base import Metric
from ..primitives import StateVector


class FlowMetric(Metric):
    """Evaluates directional change and coherence."""

    def __init__(self, mode: str = "coherence", **params):
        """
        Args:
            mode: One of 'coherence', 'volatility', 'directionality'
        """
        super().__init__(**params)
        self.mode = mode

    def compute(self, states: List[StateVector]) -> float:
        """
        Compute flow metric across state sequence.

        Args:
            states: Sequence of state vectors

        Returns:
            Flow score (interpretation depends on mode)
        """
        if len(states) < 2:
            return 0.0

        deltas = [
            states[i + 1].array - states[i].array
            for i in range(len(states) - 1)
        ]

        if self.mode == "coherence":
            # Measure consistency of direction
            if len(deltas) < 2:
                return 1.0
            norms = [np.linalg.norm(d) for d in deltas if np.linalg.norm(d) > 0]
            if not norms:
                return 1.0
            return float(1.0 - np.std(norms) / (np.mean(norms) + 1e-8))

        elif self.mode == "volatility":
            # Measure magnitude of changes
            norms = [np.linalg.norm(d) for d in deltas]
            return float(np.mean(norms))

        elif self.mode == "directionality":
            # Measure alignment of consecutive deltas
            if len(deltas) < 2:
                return 1.0
            alignments = []
            for i in range(len(deltas) - 1):
                d1, d2 = deltas[i], deltas[i + 1]
                norm1, norm2 = np.linalg.norm(d1), np.linalg.norm(d2)
                if norm1 > 0 and norm2 > 0:
                    cos_sim = np.dot(d1, d2) / (norm1 * norm2)
                    alignments.append(cos_sim)
            return float(np.mean(alignments)) if alignments else 0.0

        return 0.0
