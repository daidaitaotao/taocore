"""Test policy interfaces."""

from taocore import Decider, Decision


class ThresholdDecider(Decider):
    """Example decider using threshold-based policy."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def decide(self, metrics: dict[str, float]) -> Decision:
        """Decide based on balance metric threshold."""
        balance = metrics.get("balance", 0.0)

        if balance >= self.threshold:
            return Decision(
                action="accept",
                confidence=balance,
                metadata={"threshold": self.threshold},
            )
        else:
            return Decision(
                action="reject",
                confidence=1.0 - balance,
                metadata={"threshold": self.threshold},
            )


def test_decider_interface():
    """Test Decider base interface."""
    decider = ThresholdDecider(threshold=0.7)

    # High balance - should accept
    decision = decider.decide({"balance": 0.9})
    assert decision.action == "accept"
    assert decision.confidence == 0.9
    assert decision.metadata["threshold"] == 0.7

    # Low balance - should reject
    decision = decider.decide({"balance": 0.3})
    assert decision.action == "reject"
    assert decision.confidence == 0.7
    assert decision.metadata["threshold"] == 0.7


def test_decision_dataclass():
    """Test Decision dataclass."""
    decision = Decision(
        action="trust",
        confidence=0.85,
        metadata={"reason": "stable_signal"},
    )

    assert decision.action == "trust"
    assert decision.confidence == 0.85
    assert decision.metadata["reason"] == "stable_signal"
