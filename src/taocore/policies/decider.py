"""Decider for policy-driven choices."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class Decision:
    """Result of a policy decision."""

    action: str
    confidence: float
    metadata: Dict[str, Any]


class Decider(ABC):
    """Consumes metrics and chooses actions."""

    @abstractmethod
    def decide(self, metrics: Dict[str, float]) -> Decision:
        """
        Make decision based on metric values.

        Args:
            metrics: Named metric scores

        Returns:
            Decision with action and confidence
        """
        pass
