"""Graph primitive."""

from typing import Callable, Dict, Hashable, List, Optional, Set, Union
from collections import deque

from .node import Node
from .edge import Edge


class Graph:
    """Container for nodes and edges with topology queries."""

    def __init__(self):
        self._nodes: Dict[Hashable, Node] = {}
        self._edges: List[Edge] = []
        self._adjacency: Dict[Hashable, Set[Hashable]] = {}

    def add_node(self, node: Node) -> None:
        """Add node to graph."""
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = set()

    def add_edge(self, edge: Edge) -> None:
        """Add edge to graph."""
        self._edges.append(edge)
        if edge.source not in self._adjacency:
            self._adjacency[edge.source] = set()
        self._adjacency[edge.source].add(edge.target)

    def get_node(self, node_id: Hashable) -> Optional[Node]:
        """Retrieve node by ID."""
        return self._nodes.get(node_id)

    def neighbors(self, node_id: Hashable) -> Set[Hashable]:
        """Get neighbors of a node."""
        return self._adjacency.get(node_id, set())

    def nodes(self) -> List[Node]:
        """Get all nodes."""
        return list(self._nodes.values())

    def edges(self) -> List[Edge]:
        """Get all edges."""
        return self._edges

    def find_nodes(self, predicate: Callable[[Node], bool]) -> List[Node]:
        """
        Find nodes matching a predicate function.

        Args:
            predicate: Function taking a Node and returning bool

        Returns:
            List of nodes where predicate(node) is True

        Example:
            # Find nodes with high energy
            graph.find_nodes(lambda n: n.features.get("energy", 0) > 0.5)

            # Find recent nodes (requires temporal primitives)
            graph.find_nodes(lambda n: n.age(current_time) < 100)
        """
        return [node for node in self._nodes.values() if predicate(node)]

    def filter_edges(self, predicate: Callable[[Edge], bool]) -> List[Edge]:
        """
        Find edges matching a predicate function.

        Args:
            predicate: Function taking an Edge and returning bool

        Returns:
            List of edges where predicate(edge) is True

        Example:
            # Find strong connections
            graph.filter_edges(lambda e: e.weight > 0.8)

            # Find recent edges
            graph.filter_edges(lambda e: e.age(current_time) < 50)
        """
        return [edge for edge in self._edges if predicate(edge)]

    def k_hop_neighbors(
        self, node_id: Hashable, k: int, include_distances: bool = False
    ) -> Union[Set[Hashable], Dict[Hashable, int]]:
        """
        Find all nodes within k hops using BFS.

        Args:
            node_id: Starting node ID
            k: Maximum number of hops (1 = direct neighbors)
            include_distances: If True, return dict with distances

        Returns:
            If include_distances=False: Set of reachable node IDs (excluding start)
            If include_distances=True: Dict mapping node_id -> hop distance

        Example:
            graph.k_hop_neighbors("n1", k=2)  # Returns: {"n2", "n3", "n4"}
            graph.k_hop_neighbors("n1", k=2, include_distances=True)
            # Returns: {"n2": 1, "n3": 1, "n4": 2}
        """
        if node_id not in self._nodes:
            return {} if include_distances else set()

        distances = {node_id: 0}
        queue = deque([(node_id, 0)])

        while queue:
            current, dist = queue.popleft()

            if dist < k:
                for neighbor in self.neighbors(current):
                    if neighbor not in distances:
                        distances[neighbor] = dist + 1
                        queue.append((neighbor, dist + 1))

        # Remove starting node
        distances.pop(node_id)

        if include_distances:
            return distances
        return set(distances.keys())

    def shortest_path(
        self, source: Hashable, target: Hashable
    ) -> Optional[List[Hashable]]:
        """
        Find shortest path between two nodes using BFS (unweighted).

        Args:
            source: Starting node ID
            target: Target node ID

        Returns:
            List of node IDs forming path from source to target,
            or None if no path exists. Includes both endpoints.

        Example:
            graph.shortest_path("n1", "n5")  # Returns: ["n1", "n2", "n4", "n5"]
        """
        if source not in self._nodes or target not in self._nodes:
            return None

        if source == target:
            return [source]

        # BFS with parent tracking
        parent = {source: None}
        queue = deque([source])

        while queue:
            current = queue.popleft()

            if current == target:
                # Reconstruct path
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return list(reversed(path))

            for neighbor in self.neighbors(current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    queue.append(neighbor)

        return None  # No path found

    def subgraph(
        self, node_ids: Set[Hashable], include_edges_between: bool = True
    ) -> "Graph":
        """
        Create a new graph containing only specified nodes.

        Args:
            node_ids: Set of node IDs to include in subgraph
            include_edges_between: If True, include edges between selected nodes

        Returns:
            New Graph instance with specified nodes and optionally their edges

        Example:
            subg = graph.subgraph({"n1", "n2", "n3"}, include_edges_between=True)
        """
        new_graph = Graph()

        # Add nodes
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node is not None:
                new_graph.add_node(node)

        # Add edges if requested
        if include_edges_between:
            for edge in self._edges:
                if edge.source in node_ids and edge.target in node_ids:
                    new_graph.add_edge(edge)

        return new_graph

    def __repr__(self):
        return f"Graph(nodes={len(self._nodes)}, edges={len(self._edges)})"
