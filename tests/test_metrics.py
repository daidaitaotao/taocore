"""Test metrics."""

import numpy as np
from taocore import BalanceMetric, FlowMetric, StateVector


def test_balance_metric():
    """Test BalanceMetric."""
    metric = BalanceMetric(bounds={"x": (0.0, 10.0), "y": (0.0, 5.0)})

    # Perfect balance
    score = metric.compute({"x": 5.0, "y": 2.5})
    assert score == 1.0

    # Out of bounds
    score = metric.compute({"x": 15.0, "y": 2.5})
    assert score < 1.0


def test_flow_metric():
    """Test FlowMetric."""
    states = [
        StateVector(np.array([0.0, 0.0])),
        StateVector(np.array([1.0, 1.0])),
        StateVector(np.array([2.0, 2.0])),
    ]

    metric = FlowMetric(mode="coherence")
    score = metric.compute(states)
    assert isinstance(score, float)

    metric = FlowMetric(mode="volatility")
    score = metric.compute(states)
    assert score > 0
