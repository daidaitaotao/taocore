"""TaoCore: Systems layer for stability, coherence, and dynamics analysis."""

from .primitives import Node, Edge, Graph, StateVector
from .metrics import (
    Metric,
    BalanceMetric,
    FlowMetric,
    AttentionMetric,
    ClusterMetric,
    HubMetric,
    CompositeMetric,
)
from .solvers import EquilibriumSolver, EquilibriumResult
from .policies import Decider, Decision

__version__ = "0.1.0"

__all__ = [
    "Node",
    "Edge",
    "Graph",
    "StateVector",
    "Metric",
    "BalanceMetric",
    "FlowMetric",
    "AttentionMetric",
    "ClusterMetric",
    "HubMetric",
    "CompositeMetric",
    "EquilibriumSolver",
    "EquilibriumResult",
    "Decider",
    "Decision",
]
