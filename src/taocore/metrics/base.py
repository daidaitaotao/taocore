"""Base metric interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Metric(ABC):
    """Deterministic, parameterized, inspectable function."""

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def compute(self, *args, **kwargs) -> float:
        """Compute scalar output from inputs."""
        pass

    def get_params(self) -> Dict[str, Any]:
        """Return metric parameters."""
        return self.params
