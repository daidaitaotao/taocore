"""Composite metric for combining multiple metrics with weights."""

from typing import Dict, List, Optional, Any
from .base import Metric


class CompositeMetric(Metric):
    """
    Combines multiple metrics with weighted aggregation.

    Supports:
    - Weighted combinations of metrics
    - Layered metric composition
    - Hierarchical aggregation
    - Explicit weight exposure

    Design principles:
    - Preserves interpretability (no implicit normalization)
    - Exposes weights explicitly
    - Allows inspection of individual metric contributions
    """

    def __init__(
        self,
        metrics: List[Metric],
        weights: Optional[List[float]] = None,
        aggregation: str = "weighted_sum",
        normalize: bool = False,
        **params
    ):
        """
        Args:
            metrics: List of Metric instances to combine
            weights: Optional weights for each metric (default: equal weights)
            aggregation: One of 'weighted_sum', 'weighted_avg', 'max', 'min'
            normalize: If True, normalize weights to sum to 1.0
        """
        super().__init__(**params)

        if not metrics:
            raise ValueError("At least one metric required")

        self.metrics = metrics

        # Default to equal weights
        if weights is None:
            weights = [1.0] * len(metrics)

        if len(weights) != len(metrics):
            raise ValueError(f"Number of weights ({len(weights)}) must match number of metrics ({len(metrics)})")

        # Normalize weights if requested
        if normalize and sum(weights) > 0:
            total = sum(weights)
            weights = [w / total for w in weights]

        self.weights = weights
        self.aggregation = aggregation
        self.normalize = normalize

    def compute(
        self,
        *args,
        return_components: bool = False,
        **kwargs
    ) -> Any:
        """
        Compute composite metric by aggregating individual metrics.

        Args:
            *args: Positional arguments passed to each metric
            return_components: If True, return dict with individual scores
            **kwargs: Keyword arguments passed to each metric

        Returns:
            If return_components=False: Aggregated score (type depends on metrics)
            If return_components=True: Dict with 'composite', 'components', 'weights'

        Example:
            balance = BalanceMetric()
            flow = FlowMetric()
            composite = CompositeMetric([balance, flow], weights=[0.6, 0.4])

            score = composite.compute(graph)
            # score = 0.6 * balance + 0.4 * flow

            result = composite.compute(graph, return_components=True)
            # result = {
            #     'composite': 0.75,
            #     'components': [0.8, 0.65],
            #     'weights': [0.6, 0.4]
            # }
        """
        # Compute all individual metrics
        components = []
        for metric in self.metrics:
            result = metric.compute(*args, **kwargs)
            components.append(result)

        # Aggregate based on method
        if self.aggregation == "weighted_sum":
            composite = self._weighted_sum(components)
        elif self.aggregation == "weighted_avg":
            composite = self._weighted_avg(components)
        elif self.aggregation == "max":
            composite = self._max_aggregation(components)
        elif self.aggregation == "min":
            composite = self._min_aggregation(components)
        else:
            raise ValueError(f"Unknown aggregation: {self.aggregation}")

        if return_components:
            return {
                "composite": composite,
                "components": components,
                "weights": self.weights,
            }

        return composite

    def _weighted_sum(self, components: List[Any]) -> Any:
        """Compute weighted sum of metric results."""
        # Handle scalar results
        if all(isinstance(c, (int, float)) for c in components):
            return sum(w * c for w, c in zip(self.weights, components))

        # Handle dict results (merge with weighted values)
        if all(isinstance(c, dict) for c in components):
            return self._weighted_sum_dicts(components)

        raise TypeError(f"Cannot aggregate mixed or unsupported types: {[type(c) for c in components]}")

    def _weighted_avg(self, components: List[Any]) -> Any:
        """Compute weighted average of metric results."""
        total_weight = sum(self.weights)
        if total_weight == 0:
            raise ValueError("Cannot compute weighted average with zero total weight")

        # Handle scalar results
        if all(isinstance(c, (int, float)) for c in components):
            return sum(w * c for w, c in zip(self.weights, components)) / total_weight

        # Handle dict results
        if all(isinstance(c, dict) for c in components):
            result = self._weighted_sum_dicts(components)
            # Normalize all values
            return {k: v / total_weight for k, v in result.items()}

        raise TypeError(f"Cannot aggregate mixed or unsupported types: {[type(c) for c in components]}")

    def _max_aggregation(self, components: List[Any]) -> Any:
        """Take maximum across metric results."""
        if all(isinstance(c, (int, float)) for c in components):
            return max(components)

        if all(isinstance(c, dict) for c in components):
            # Union of all keys, take max for each
            all_keys = set()
            for comp in components:
                all_keys.update(comp.keys())

            result = {}
            for key in all_keys:
                values = [comp.get(key, float('-inf')) for comp in components]
                result[key] = max(values)

            return result

        raise TypeError(f"Cannot aggregate mixed or unsupported types: {[type(c) for c in components]}")

    def _min_aggregation(self, components: List[Any]) -> Any:
        """Take minimum across metric results."""
        if all(isinstance(c, (int, float)) for c in components):
            return min(components)

        if all(isinstance(c, dict) for c in components):
            # Union of all keys, take min for each
            all_keys = set()
            for comp in components:
                all_keys.update(comp.keys())

            result = {}
            for key in all_keys:
                values = [comp.get(key, float('inf')) for comp in components]
                result[key] = min(values)

            return result

        raise TypeError(f"Cannot aggregate mixed or unsupported types: {[type(c) for c in components]}")

    def _weighted_sum_dicts(self, components: List[Dict]) -> Dict:
        """
        Compute weighted sum of dictionaries.

        Takes union of all keys and sums weighted values.
        Missing keys are treated as 0.0.
        """
        all_keys = set()
        for comp in components:
            all_keys.update(comp.keys())

        result = {}
        for key in all_keys:
            weighted_value = sum(
                w * comp.get(key, 0.0)
                for w, comp in zip(self.weights, components)
            )
            result[key] = weighted_value

        return result

    def get_weights(self) -> List[float]:
        """Return the current weights."""
        return self.weights.copy()

    def get_metrics(self) -> List[Metric]:
        """Return the list of composed metrics."""
        return self.metrics.copy()
