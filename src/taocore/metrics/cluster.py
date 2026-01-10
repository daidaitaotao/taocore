"""Clustering metric for graph and state analysis."""

from typing import Dict, List, Set, Tuple, Optional
import numpy as np
from .base import Metric
from ..primitives import Graph, Node, StateVector


class ClusterMetric(Metric):
    """
    Identifies groups of entities with dense internal relationships.

    Supports multiple clustering algorithms:
    - 'components': Connected components (graph connectivity)
    - 'modularity': Greedy modularity optimization
    - 'distance': Distance-based clustering for StateVectors

    Returns cluster assignments and optional statistics.
    """

    def __init__(
        self,
        algorithm: str = "components",
        threshold: float = 0.5,
        min_cluster_size: int = 1,
        **params
    ):
        """
        Args:
            algorithm: One of 'components', 'modularity', 'distance'
            threshold: Algorithm-specific threshold (for distance-based)
            min_cluster_size: Minimum nodes per cluster
        """
        super().__init__(**params)
        self.algorithm = algorithm
        self.threshold = threshold
        self.min_cluster_size = min_cluster_size

    def compute(
        self, graph: Graph, **kwargs
    ) -> Dict[str, any]:
        """
        Compute clustering on graph.

        Args:
            graph: Graph to cluster

        Returns:
            Dict with:
            - 'assignments': Dict[node_id, cluster_id]
            - 'num_clusters': int
            - 'sizes': List[int] (cluster sizes)
            - 'modularity': float (if applicable)

        Example:
            metric = ClusterMetric(algorithm='components')
            result = metric.compute(graph)
            # result['assignments'] = {'n1': 0, 'n2': 0, 'n3': 1}
        """
        if self.algorithm == "components":
            return self._compute_components(graph)
        elif self.algorithm == "modularity":
            return self._compute_modularity(graph)
        elif self.algorithm == "distance":
            return self._compute_distance(graph, **kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")

    def _compute_components(self, graph: Graph) -> Dict[str, any]:
        """
        Find connected components via BFS.

        Returns cluster where each component gets a unique ID.
        """
        nodes = {node.id for node in graph.nodes()}
        visited = set()
        assignments = {}
        cluster_id = 0

        for start_node in nodes:
            if start_node in visited:
                continue

            # BFS to find component
            component = set()
            queue = [start_node]
            component.add(start_node)
            visited.add(start_node)

            while queue:
                current = queue.pop(0)
                for neighbor in graph.neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)

            # Assign cluster ID
            if len(component) >= self.min_cluster_size:
                for node_id in component:
                    assignments[node_id] = cluster_id
                cluster_id += 1

        return self._format_result(assignments)

    def _compute_modularity(self, graph: Graph) -> Dict[str, any]:
        """
        Greedy modularity optimization (simplified Louvain-style).

        Assigns nodes to communities that maximize modularity.
        """
        nodes = [node.id for node in graph.nodes()]
        edges = graph.edges()

        # Initialize: each node in its own cluster
        assignments = {node_id: i for i, node_id in enumerate(nodes)}

        # Build adjacency info
        degrees = {node_id: len(graph.neighbors(node_id)) for node_id in nodes}
        total_edges = len(edges)

        if total_edges == 0:
            # No edges, each node is own cluster
            return self._format_result(assignments)

        # Greedy optimization (single pass for simplicity)
        improved = True
        iterations = 0
        max_iterations = 10

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            for node_id in nodes:
                current_cluster = assignments[node_id]
                best_cluster = current_cluster
                best_delta = 0.0

                # Try moving to neighbor clusters
                neighbor_clusters = set()
                for neighbor in graph.neighbors(node_id):
                    neighbor_clusters.add(assignments[neighbor])

                for target_cluster in neighbor_clusters:
                    if target_cluster == current_cluster:
                        continue

                    # Simplified modularity delta calculation
                    # (proper implementation would track cluster internals)
                    delta = self._modularity_delta(
                        graph, node_id, current_cluster, target_cluster, assignments
                    )

                    if delta > best_delta:
                        best_delta = delta
                        best_cluster = target_cluster

                if best_cluster != current_cluster:
                    assignments[node_id] = best_cluster
                    improved = True

        # Relabel clusters to 0, 1, 2, ...
        unique_clusters = sorted(set(assignments.values()))
        cluster_map = {old: new for new, old in enumerate(unique_clusters)}
        assignments = {
            node_id: cluster_map[cluster_id]
            for node_id, cluster_id in assignments.items()
        }

        result = self._format_result(assignments)
        result["modularity"] = self._compute_modularity_score(graph, assignments)
        return result

    def _modularity_delta(
        self,
        graph: Graph,
        node_id: str,
        from_cluster: int,
        to_cluster: int,
        assignments: Dict[str, int],
    ) -> float:
        """
        Estimate modularity change from moving node between clusters.

        Simplified heuristic: count edges to each cluster.
        """
        neighbors = graph.neighbors(node_id)

        # Count edges to each cluster
        edges_to_from = sum(
            1 for n in neighbors if assignments.get(n) == from_cluster
        )
        edges_to_to = sum(1 for n in neighbors if assignments.get(n) == to_cluster)

        # Prefer clusters with more connections
        return edges_to_to - edges_to_from

    def _compute_modularity_score(
        self, graph: Graph, assignments: Dict[str, int]
    ) -> float:
        """
        Compute modularity Q for current clustering.

        Q = (edges within clusters - expected) / total edges
        """
        edges = graph.edges()
        if len(edges) == 0:
            return 0.0

        # Count edges within vs between clusters
        within = 0
        total = len(edges)

        for edge in edges:
            if assignments.get(edge.source) == assignments.get(edge.target):
                within += 1

        # Simplified modularity (proper formula requires degree distribution)
        return (within / total) if total > 0 else 0.0

    def _compute_distance(
        self, graph: Graph, states: Optional[Dict[str, StateVector]] = None
    ) -> Dict[str, any]:
        """
        Distance-based clustering using node features or provided states.

        Groups nodes within threshold distance.
        """
        if states is None:
            # Use node features as state vectors
            states = {}
            for node in graph.nodes():
                if node.features:
                    states[node.id] = StateVector(node.features)

        if not states:
            # No features, fall back to components
            return self._compute_components(graph)

        # Build distance matrix
        node_ids = list(states.keys())
        n = len(node_ids)

        if n == 0:
            return self._format_result({})

        # Simple greedy clustering
        assignments = {}
        cluster_id = 0

        for i, node_id in enumerate(node_ids):
            if node_id in assignments:
                continue

            # Start new cluster
            cluster = {node_id}
            assignments[node_id] = cluster_id

            # Find nearby nodes
            for j, other_id in enumerate(node_ids):
                if i == j or other_id in assignments:
                    continue

                distance = states[node_id].distance(states[other_id])
                if distance <= self.threshold:
                    cluster.add(other_id)
                    assignments[other_id] = cluster_id

            if len(cluster) >= self.min_cluster_size:
                cluster_id += 1
            else:
                # Remove too-small cluster
                for nid in cluster:
                    del assignments[nid]

        return self._format_result(assignments)

    def _format_result(self, assignments: Dict[str, int]) -> Dict[str, any]:
        """Format clustering result with statistics."""
        if not assignments:
            return {
                "assignments": {},
                "num_clusters": 0,
                "sizes": [],
            }

        # Count cluster sizes
        cluster_sizes = {}
        for cluster_id in assignments.values():
            cluster_sizes[cluster_id] = cluster_sizes.get(cluster_id, 0) + 1

        sizes = list(cluster_sizes.values())

        return {
            "assignments": assignments,
            "num_clusters": len(cluster_sizes),
            "sizes": sizes,
        }
