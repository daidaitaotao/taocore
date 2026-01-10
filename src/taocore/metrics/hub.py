"""Hub detection metric for identifying structurally influential nodes."""

from typing import Dict, List, Optional
import numpy as np
from .base import Metric
from ..primitives import Graph


class HubMetric(Metric):
    """
    Assigns influence scores to nodes based on structural position.

    Supports multiple centrality measures:
    - 'degree': Simple connection count
    - 'betweenness': Frequency on shortest paths
    - 'eigenvector': Connections to important nodes
    - 'pagerank': Iterative importance propagation

    Hub scores indicate structural importance, not semantic meaning.
    """

    def __init__(
        self,
        method: str = "degree",
        damping: float = 0.85,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
        **params
    ):
        """
        Args:
            method: One of 'degree', 'betweenness', 'eigenvector', 'pagerank'
            damping: For pagerank (default 0.85)
            max_iterations: For iterative methods
            tolerance: Convergence tolerance for iterative methods
        """
        super().__init__(**params)
        self.method = method
        self.damping = damping
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def compute(self, graph: Graph) -> Dict[str, float]:
        """
        Compute hub scores for all nodes.

        Args:
            graph: Graph to analyze

        Returns:
            Dict mapping node_id -> influence score (normalized to [0, 1])

        Example:
            metric = HubMetric(method='degree')
            scores = metric.compute(graph)
            # scores = {'n1': 1.0, 'n2': 0.5, 'n3': 0.0}
        """
        if self.method == "degree":
            return self._degree_centrality(graph)
        elif self.method == "betweenness":
            return self._betweenness_centrality(graph)
        elif self.method == "eigenvector":
            return self._eigenvector_centrality(graph)
        elif self.method == "pagerank":
            return self._pagerank(graph)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _degree_centrality(self, graph: Graph) -> Dict[str, float]:
        """
        Degree centrality: normalized connection count.

        Score = num_neighbors / max_possible_neighbors
        """
        nodes = [node.id for node in graph.nodes()]
        n = len(nodes)

        if n <= 1:
            return {node_id: 0.0 for node_id in nodes}

        scores = {}
        max_degree = n - 1  # Maximum possible connections

        for node_id in nodes:
            degree = len(graph.neighbors(node_id))
            scores[node_id] = degree / max_degree if max_degree > 0 else 0.0

        return scores

    def _betweenness_centrality(self, graph: Graph) -> Dict[str, float]:
        """
        Betweenness centrality: frequency on shortest paths.

        Measures how often a node appears on shortest paths between other nodes.
        """
        nodes = [node.id for node in graph.nodes()]
        n = len(nodes)

        if n <= 2:
            return {node_id: 0.0 for node_id in nodes}

        # Count shortest paths through each node
        betweenness = {node_id: 0.0 for node_id in nodes}

        for source in nodes:
            # BFS from source to find all shortest paths
            paths = self._all_shortest_paths(graph, source)

            for target in nodes:
                if source == target:
                    continue

                if target not in paths:
                    continue

                # Count nodes on shortest paths from source to target
                for path in paths[target]:
                    for node_id in path[1:-1]:  # Exclude source and target
                        betweenness[node_id] += 1.0

        # Normalize
        normalizer = (n - 1) * (n - 2)
        if normalizer > 0:
            for node_id in nodes:
                betweenness[node_id] /= normalizer

        return betweenness

    def _all_shortest_paths(
        self, graph: Graph, source: str
    ) -> Dict[str, List[List[str]]]:
        """
        Find all shortest paths from source to all other nodes.

        Returns dict of {target: [path1, path2, ...]}
        """
        from collections import deque

        nodes = {node.id for node in graph.nodes()}

        # BFS with path tracking
        distances = {source: 0}
        paths = {source: [[source]]}
        queue = deque([source])

        while queue:
            current = queue.popleft()
            current_dist = distances[current]

            for neighbor in graph.neighbors(current):
                if neighbor not in distances:
                    # First time seeing this node
                    distances[neighbor] = current_dist + 1
                    paths[neighbor] = []
                    queue.append(neighbor)

                if distances[neighbor] == current_dist + 1:
                    # This is a shortest path
                    for path in paths[current]:
                        paths[neighbor].append(path + [neighbor])

        return paths

    def _eigenvector_centrality(self, graph: Graph) -> Dict[str, float]:
        """
        Eigenvector centrality: importance from connections to important nodes.

        Uses power iteration to find dominant eigenvector of adjacency matrix.
        """
        nodes = [node.id for node in graph.nodes()]
        n = len(nodes)

        if n == 0:
            return {}

        # Build adjacency matrix
        node_index = {node_id: i for i, node_id in enumerate(nodes)}
        adjacency = np.zeros((n, n))

        for edge in graph.edges():
            if edge.source in node_index and edge.target in node_index:
                i = node_index[edge.source]
                j = node_index[edge.target]
                adjacency[i, j] = edge.weight
                adjacency[j, i] = edge.weight  # Undirected for centrality

        # Power iteration
        centrality = np.ones(n) / n

        for iteration in range(self.max_iterations):
            new_centrality = adjacency @ centrality

            # Normalize
            norm = np.linalg.norm(new_centrality)
            if norm < 1e-10:
                # No edges or disconnected graph
                return {node_id: 0.0 for node_id in nodes}

            new_centrality /= norm

            # Check convergence
            if np.linalg.norm(new_centrality - centrality) < self.tolerance:
                centrality = new_centrality
                break

            centrality = new_centrality

        # Normalize to [0, 1]
        max_val = np.max(centrality) if np.max(centrality) > 0 else 1.0
        centrality /= max_val

        return {nodes[i]: float(centrality[i]) for i in range(n)}

    def _pagerank(self, graph: Graph) -> Dict[str, float]:
        """
        PageRank: iterative importance propagation with damping.

        PR(node) = (1-d)/N + d * sum(PR(neighbor) / outdegree(neighbor))
        """
        nodes = [node.id for node in graph.nodes()]
        n = len(nodes)

        if n == 0:
            return {}

        # Initialize
        pagerank = {node_id: 1.0 / n for node_id in nodes}

        # Compute outdegrees
        outdegree = {
            node_id: max(len(graph.neighbors(node_id)), 1) for node_id in nodes
        }

        # Power iteration
        for iteration in range(self.max_iterations):
            new_pagerank = {}

            for node_id in nodes:
                # Base probability (random jump)
                rank = (1.0 - self.damping) / n

                # Add contributions from incoming edges
                for neighbor_id in nodes:
                    if node_id in graph.neighbors(neighbor_id):
                        rank += (
                            self.damping * pagerank[neighbor_id] / outdegree[neighbor_id]
                        )

                new_pagerank[node_id] = rank

            # Check convergence
            delta = sum(
                abs(new_pagerank[nid] - pagerank[nid]) for nid in nodes
            )
            if delta < self.tolerance:
                pagerank = new_pagerank
                break

            pagerank = new_pagerank

        # Normalize to [0, 1]
        max_val = max(pagerank.values()) if pagerank else 1.0
        if max_val > 0:
            pagerank = {nid: score / max_val for nid, score in pagerank.items()}

        return pagerank
