"""Attention metric for relevance and salience computation."""

from typing import Dict, List, Optional, Union
import numpy as np
from .base import Metric
from ..primitives import Node, Graph


class AttentionMetric(Metric):
    """
    Evaluates attention/relevance between query and items.

    Supports multiple modes:
    - 'similarity': Compute similarity between query and target features
    - 'composite': Combine multiple signals with weights
    """

    def __init__(
        self,
        mode: str = "similarity",
        similarity_fn: str = "cosine",  # 'cosine' or 'euclidean'
        composite_weights: Optional[Dict[str, float]] = None,
        **params
    ):
        """
        Args:
            mode: One of 'similarity', 'composite'
            similarity_fn: Distance function ('cosine' or 'euclidean')
            composite_weights: For composite mode, weights for each signal
                              e.g., {'similarity': 0.5, 'recency': 0.3, 'strength': 0.2}
        """
        super().__init__(**params)
        self.mode = mode
        self.similarity_fn = similarity_fn
        self.composite_weights = composite_weights or {}

    def compute(
        self,
        query: Dict[str, float],
        target: Union[Dict[str, float], Node, List[Node], Graph],
        current_time: Optional[float] = None,
    ) -> Union[float, Dict[str, float]]:
        """
        Compute attention score(s).

        Args:
            query: Query feature vector as dict
            target: Target to score against. Can be:
                   - Dict[str, float]: Single feature vector -> returns float
                   - Node: Single node -> returns float
                   - List[Node]: Multiple nodes -> returns Dict[node_id, score]
                   - Graph: All graph nodes -> returns Dict[node_id, score]
            current_time: Current timestamp (required for temporal features)

        Returns:
            Single score (float) or dict mapping node_id -> score

        Example:
            # Similarity mode
            metric = AttentionMetric(mode='similarity', similarity_fn='cosine')
            score = metric.compute(
                query={'joy': 0.8, 'energy': 0.6},
                target={'joy': 0.7, 'energy': 0.5}
            )

            # Composite mode with temporal features
            metric = AttentionMetric(
                mode='composite',
                composite_weights={'similarity': 0.5, 'recency': 0.3, 'strength': 0.2}
            )
            scores = metric.compute(
                query={'joy': 0.8},
                target=graph,
                current_time=1000.0
            )
        """
        # Normalize target to list of nodes
        if isinstance(target, dict):
            # Single feature dict -> wrap as Node
            nodes = [Node(id="target", features=target)]
            return_single = True
        elif isinstance(target, Node):
            nodes = [target]
            return_single = True
        elif isinstance(target, Graph):
            nodes = target.nodes()
            return_single = False
        else:  # List[Node]
            nodes = target
            return_single = False

        # Compute scores for each node
        scores = {}
        for node in nodes:
            if self.mode == "similarity":
                score = self._compute_similarity(query, node.features)
            elif self.mode == "composite":
                score = self._compute_composite(query, node, current_time)
            else:
                score = 0.0

            scores[node.id] = score

        if return_single:
            return scores["target"] if "target" in scores else list(scores.values())[0]
        return scores

    def _compute_similarity(
        self, query: Dict[str, float], target: Dict[str, float]
    ) -> float:
        """
        Compute similarity between query and target feature vectors.

        Returns:
            Similarity score. For cosine: [-1, 1] (1=identical direction).
            For euclidean: 1/(1+distance) (1=identical, 0.5=distance 1, etc.)
        """
        # Find common features
        common_keys = set(query.keys()) & set(target.keys())
        if not common_keys:
            return 0.0

        # Extract aligned vectors
        q_vec = np.array([query[k] for k in common_keys])
        t_vec = np.array([target[k] for k in common_keys])

        if self.similarity_fn == "cosine":
            # Cosine similarity
            q_norm = np.linalg.norm(q_vec)
            t_norm = np.linalg.norm(t_vec)

            if q_norm == 0 or t_norm == 0:
                return 0.0

            cos_sim = np.dot(q_vec, t_vec) / (q_norm * t_norm)
            return float(cos_sim)

        elif self.similarity_fn == "euclidean":
            # Euclidean distance converted to similarity
            distance = np.linalg.norm(q_vec - t_vec)
            # Convert to [0, 1] where 1 = identical
            similarity = 1.0 / (1.0 + distance)
            return float(similarity)

        return 0.0

    def _compute_composite(
        self, query: Dict[str, float], node: Node, current_time: Optional[float]
    ) -> float:
        """
        Compute weighted combination of multiple signals.

        Signals:
        - 'similarity': Feature similarity to query
        - 'recency': Recency score (1.0 for recent, decays with age)
        - 'strength': Node strength (from temporal decay)

        Returns:
            Weighted sum of signals, normalized to [0, 1]
        """
        signals = {}
        total_weight = 0.0

        # Compute similarity signal
        if "similarity" in self.composite_weights:
            signals["similarity"] = self._compute_similarity(query, node.features)
            total_weight += self.composite_weights["similarity"]

        # Compute recency signal (requires timestamp)
        if "recency" in self.composite_weights:
            if current_time is not None and node.timestamp is not None:
                age = node.age(current_time)
                # Recency score: exponential decay with fixed rate
                # Using rate=0.01 as reasonable default
                recency = np.exp(-0.01 * age) if age > 0 else 1.0
                signals["recency"] = float(recency)
            else:
                signals["recency"] = 0.0
            total_weight += self.composite_weights["recency"]

        # Compute strength signal (requires timestamp and decay_rate)
        if "strength" in self.composite_weights:
            if current_time is not None:
                signals["strength"] = node.compute_strength(current_time)
            else:
                signals["strength"] = 1.0 if node.decay_rate == 0 else 0.0
            total_weight += self.composite_weights["strength"]

        # Weighted sum
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(
            signals[name] * self.composite_weights[name] for name in signals
        )

        # Normalize by total weight to keep in [0, 1]
        return weighted_sum / total_weight
