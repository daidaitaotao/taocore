# RFC-2: Advanced Metrics for Graph Analysis

**Status:** Implemented
**Author:** TaoCore Team
**Created:** 2026-01-10
**Version:** 0.1.0
**Depends On:** RFC-1

## Abstract

RFC-2 extends TaoCore's metric system with advanced graph analysis capabilities. It introduces three new metric families for analyzing structural patterns, influence propagation, and metric composition:

1. **ClusterMetric** - Community detection and grouping analysis
2. **HubMetric** - Node centrality and influence measurement
3. **CompositeMetric** - Weighted metric combination framework

These additions enable sophisticated graph-based reasoning while maintaining TaoCore's domain-agnostic design principles.

## Context & Motivation

### The Gap in RFC-1

RFC-1 provided:
- ✓ Stability analysis (BalanceMetric)
- ✓ Flow coherence (FlowMetric)
- ✓ Equilibrium finding (EquilibriumSolver)

But lacked:
- ✗ Graph structural analysis (clustering, communities)
- ✗ Node importance ranking (hubs, centrality)
- ✗ Multi-metric composition (weighted combinations)

### Why These Metrics Matter

**Real-world use cases:**
- **Social networks**: Detect communities, identify influencers
- **Service meshes**: Find critical services, detect isolated components
- **Knowledge graphs**: Rank entity importance, group related concepts
- **Agent systems**: Identify coordinators, detect isolated agents
- **Memory systems**: Cluster related memories, rank relevance

**Design requirement:** All metrics must remain **domain-agnostic** - they analyze structure and dynamics, not semantic meaning.

## Design Principles

### 1. Structural Focus

Metrics analyze **topology** and **connectivity**, not content:
- ClusterMetric groups nodes by connection patterns
- HubMetric ranks nodes by structural position
- No assumptions about what nodes/edges represent

### 2. Algorithmic Transparency

All algorithms are:
- **Interpretable**: Clear mathematical definitions
- **Inspectable**: Return intermediate results (e.g., cluster assignments)
- **Configurable**: Expose key parameters (thresholds, iterations)

### 3. Composability

Metrics can be:
- Combined (CompositeMetric)
- Chained (cluster → hub within clusters)
- Used with existing metrics (balance + clustering)

### 4. Computational Pragmatism

Implementations prioritize:
- **Correctness** over speed (optimize later)
- **Simplicity** over sophistication (BFS not Dijkstra)
- **Dependencies** - only NumPy (no NetworkX, scikit-learn)

## Architecture Overview

```
TaoCore Metrics (Extended)
├── Base Layer
│   ├── BalanceMetric       # Bounded stability (RFC-1)
│   └── FlowMetric          # Temporal coherence (RFC-1)
│
├── Graph Analysis (RFC-2)
│   ├── ClusterMetric       # Community detection
│   │   ├── Components      # Connected components
│   │   ├── Modularity      # Quality optimization
│   │   └── Distance        # Feature-based clustering
│   │
│   ├── HubMetric          # Centrality measures
│   │   ├── Degree         # Connection count
│   │   ├── Betweenness    # Path frequency
│   │   ├── Eigenvector    # Recursive importance
│   │   └── PageRank       # Damped iteration
│   │
│   └── CompositeMetric    # Metric composition
│       ├── Weighted sum   # Linear combination
│       ├── Weighted avg   # Normalized combination
│       ├── Max/Min        # Extremal selection
│       └── Component inspection
```

## Implementation Specifications

### 1. ClusterMetric

**Purpose:** Identify groups of entities with dense internal relationships.

**File:** `src/taocore/metrics/cluster.py`

#### API

```python
class ClusterMetric(Metric):
    def __init__(
        self,
        algorithm: str = "components",      # 'components', 'modularity', 'distance'
        threshold: float = 0.5,             # For distance-based
        min_cluster_size: int = 1,          # Filter small clusters
        **params
    )

    def compute(self, graph: Graph, **kwargs) -> Dict[str, Any]:
        """
        Returns:
            {
                'assignments': Dict[node_id, cluster_id],
                'num_clusters': int,
                'sizes': List[int],
                'modularity': float  # Only for modularity algorithm
            }
        """
```

#### Algorithms

**1. Connected Components (`algorithm="components"`)**

- **Method:** BFS traversal
- **Time complexity:** O(V + E)
- **Returns:** Each connected component as a cluster
- **Use case:** Find disconnected subgraphs

**Implementation:**
```
1. Initialize: visited = {}, cluster_id = 0
2. For each unvisited node:
   a. BFS to find all reachable nodes
   b. Assign cluster_id to component
   c. cluster_id += 1
3. Filter clusters < min_cluster_size
```

**2. Modularity Optimization (`algorithm="modularity"`)**

- **Method:** Greedy Louvain-style community detection
- **Time complexity:** O(V·E·iterations)
- **Returns:** Communities maximizing modularity score Q
- **Use case:** Detect densely connected groups

**Modularity formula:**
```
Q = (edges_within_communities - expected_edges) / total_edges
```

**Implementation:**
```
1. Initialize: each node in own cluster
2. Repeat until no improvement:
   For each node:
     a. Try moving to each neighbor's cluster
     b. Compute modularity delta
     c. Move to cluster with highest gain
3. Return final clustering + Q score
```

**3. Distance-Based (`algorithm="distance"`)**

- **Method:** Feature similarity with threshold
- **Time complexity:** O(V²)
- **Returns:** Clusters where nodes are within threshold distance
- **Use case:** Group entities with similar features

**Implementation:**
```
1. Extract node features as StateVectors
2. Greedy clustering:
   For each unassigned node:
     a. Start new cluster
     b. Find all nodes within threshold distance
     c. Assign to cluster
3. Filter clusters < min_cluster_size
```

#### Edge Cases

- **Empty graph:** Returns `{'assignments': {}, 'num_clusters': 0, 'sizes': []}`
- **No features (distance mode):** Falls back to components
- **All isolated nodes:** Each node = separate cluster (or filtered by min_size)

---

### 2. HubMetric

**Purpose:** Rank nodes by structural importance/influence.

**File:** `src/taocore/metrics/hub.py`

#### API

```python
class HubMetric(Metric):
    def __init__(
        self,
        method: str = "degree",             # 'degree', 'betweenness', 'eigenvector', 'pagerank'
        damping: float = 0.85,              # For PageRank
        max_iterations: int = 100,          # For iterative methods
        tolerance: float = 1e-6,            # Convergence threshold
        **params
    )

    def compute(self, graph: Graph) -> Dict[str, float]:
        """
        Returns: Dict[node_id, influence_score]
        Scores normalized to [0, 1], higher = more influential
        """
```

#### Methods

**1. Degree Centrality (`method="degree"`)**

- **Formula:** `score = num_neighbors / (n - 1)`
- **Time complexity:** O(V)
- **Interpretation:** Connectivity strength
- **Use case:** Find highly connected nodes

**2. Betweenness Centrality (`method="betweenness"`)**

- **Formula:** `score = (paths_through_node) / (total_paths)`
- **Time complexity:** O(V²·E)
- **Interpretation:** Bridge/bottleneck importance
- **Use case:** Identify critical connectors

**Implementation:**
```
1. For each source node:
   a. BFS to find all shortest paths
   b. Count paths passing through each node
2. Normalize by (n-1)·(n-2)
```

**3. Eigenvector Centrality (`method="eigenvector"`)**

- **Formula:** `x = λ·A·x` (dominant eigenvector)
- **Time complexity:** O(V²·iterations)
- **Interpretation:** Importance via important connections
- **Use case:** Recursive influence propagation

**Implementation:**
```
1. Build adjacency matrix A
2. Power iteration:
   x_{t+1} = A·x_t / ||A·x_t||
3. Converge when ||x_{t+1} - x_t|| < tolerance
4. Normalize to [0, 1]
```

**4. PageRank (`method="pagerank"`)**

- **Formula:** `PR(v) = (1-d)/N + d·Σ(PR(u)/degree(u))`
- **Time complexity:** O(V²·iterations)
- **Interpretation:** Random walk steady-state probability
- **Use case:** Web-style ranking with damping

**Implementation:**
```
1. Initialize: PR(v) = 1/N for all v
2. Iterate until convergence:
   For each node v:
     PR_new(v) = (1-d)/N + d·Σ_{u→v}(PR(u)/outdegree(u))
3. Normalize to [0, 1]
```

#### Edge Cases

- **Empty graph:** Returns `{}`
- **Isolated nodes:** Score = 0.0
- **No edges (eigenvector):** Returns uniform 0.0
- **Invalid method:** Raises `ValueError`

---

### 3. CompositeMetric

**Purpose:** Combine multiple metrics with configurable aggregation.

**File:** `src/taocore/metrics/composite.py`

#### API

```python
class CompositeMetric(Metric):
    def __init__(
        self,
        metrics: List[Metric],              # Metrics to combine
        weights: Optional[List[float]] = None,  # Default: equal weights
        aggregation: str = "weighted_sum",  # 'weighted_sum', 'weighted_avg', 'max', 'min'
        normalize: bool = False,            # Normalize weights to sum=1
        **params
    )

    def compute(
        self,
        *args,
        return_components: bool = False,    # Return individual scores
        **kwargs
    ) -> Union[float, Dict, Dict[str, Any]]:
        """
        If return_components=True:
            Returns: {'composite': score, 'components': [...], 'weights': [...]}
        Else:
            Returns: Aggregated score (type depends on metrics)
        """
```

#### Aggregation Modes

**1. Weighted Sum (`aggregation="weighted_sum"`)**

```
composite = Σ(weight_i · metric_i)
```

**Use case:** Linear combination (e.g., 60% balance + 40% flow)

**2. Weighted Average (`aggregation="weighted_avg"`)**

```
composite = Σ(weight_i · metric_i) / Σ(weight_i)
```

**Use case:** Normalized combination regardless of weight magnitudes

**3. Max/Min (`aggregation="max"/"min"`)**

```
composite = max(metrics) or min(metrics)
```

**Use case:** Conservative (min) or optimistic (max) policy

#### Type Handling

**Scalar metrics:**
```python
balance = BalanceMetric(bounds={"x": (0, 10)})
flow = FlowMetric(mode="coherence")
composite = CompositeMetric([balance, flow], weights=[0.6, 0.4])
score = composite.compute(...)  # Returns: float
```

**Dict-valued metrics:**
```python
hub1 = HubMetric(method="degree")
hub2 = HubMetric(method="pagerank")
composite = CompositeMetric([hub1, hub2], weights=[0.5, 0.5])
scores = composite.compute(graph)  # Returns: Dict[node_id, float]
```

**Dict aggregation:**
- Takes **union** of all keys
- Missing keys treated as 0.0
- Applies weights element-wise

#### Design Philosophy

**Explicit over implicit:**
- Weights are visible via `get_weights()`
- No hidden normalization (unless `normalize=True`)
- Component scores accessible via `return_components=True`

**Interpretability:**
- Users understand how final score is computed
- Can inspect individual metric contributions
- No black-box transformations

#### Edge Cases

- **Empty metrics list:** Raises `ValueError`
- **Mismatched weights:** Raises `ValueError`
- **Mixed types:** Raises `TypeError`
- **Zero total weight (avg mode):** Raises `ValueError`

---

## Testing Strategy

### Test Coverage

**Files:**
- `tests/test_metrics.py` - All metric tests (24 new tests added)

**Test categories:**

**ClusterMetric (8 tests):**
- `test_cluster_components_basic` - Two components
- `test_cluster_components_single_component` - Fully connected
- `test_cluster_components_min_size` - Size filtering
- `test_cluster_modularity_basic` - Community structure
- `test_cluster_distance_basic` - Feature-based
- `test_cluster_empty_graph` - Edge case
- Additional: Invalid algorithm, no features

**HubMetric (7 tests):**
- `test_hub_degree_basic` - Star topology
- `test_hub_degree_isolated` - Disconnected nodes
- `test_hub_betweenness_basic` - Bridge detection
- `test_hub_eigenvector_basic` - Recursive importance
- `test_hub_pagerank_basic` - Damped ranking
- `test_hub_empty_graph` - Edge case
- `test_hub_invalid_method` - Error handling

**CompositeMetric (9 tests):**
- `test_composite_weighted_sum_scalars` - Scalar combination
- `test_composite_weighted_avg_scalars` - Average normalization
- `test_composite_equal_weights` - Default weights
- `test_composite_normalize_weights` - Weight normalization
- `test_composite_return_components` - Component inspection
- `test_composite_max_aggregation` - Max selection
- `test_composite_min_aggregation` - Min selection
- `test_composite_dict_aggregation` - Dict-valued metrics
- Error cases: Empty metrics, mismatched weights

### Coverage Results

```
ClusterMetric:  95% (133 statements, 7 missed)
HubMetric:      95% (122 statements, 6 missed)
CompositeMetric: 70% (90 statements, 27 missed)
Overall:        92% (707 statements, 60 missed)
```

**100 tests passing** (76 from RFC-1, 24 from RFC-2)

### Verification Script

**File:** `examples/rfc2_verification.py`

Demonstrates:
- All clustering algorithms
- All centrality methods
- Composite metric combinations
- Integration with existing metrics

**Run:** `uv run python examples/rfc2_verification.py`

---

## Usage Examples

### Example 1: Community Detection

```python
from taocore import Graph, Node, Edge, ClusterMetric

# Build social network
graph = Graph()
for user in users:
    graph.add_node(Node(user.id))
for friendship in friendships:
    graph.add_edge(Edge(friendship.source, friendship.target))

# Find communities
metric = ClusterMetric(algorithm="modularity", min_cluster_size=3)
result = metric.compute(graph)

print(f"Found {result['num_clusters']} communities")
print(f"Modularity Q: {result['modularity']:.3f}")
print(f"Cluster sizes: {result['sizes']}")

# Assign users to communities
user_community = result['assignments']
```

### Example 2: Influence Ranking

```python
from taocore import Graph, Node, Edge, HubMetric

# Service mesh topology
graph = Graph()
for service in services:
    graph.add_node(Node(service.name))
for dependency in dependencies:
    graph.add_edge(Edge(dependency.from_service, dependency.to_service))

# Rank by importance
metric = HubMetric(method="pagerank", damping=0.85)
scores = metric.compute(graph)

# Identify critical services
critical = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top 5 critical services:")
for service, score in critical:
    print(f"  {service}: {score:.3f}")
```

### Example 3: Multi-Metric Decision

```python
from taocore import BalanceMetric, FlowMetric, CompositeMetric

# Define individual metrics
balance = BalanceMetric(bounds={
    "cpu": (0, 80),
    "memory": (0, 90),
    "latency": (0, 200)
})

flow = FlowMetric(mode="coherence")

# Combine with policy weights
composite = CompositeMetric(
    metrics=[balance, flow],
    weights=[0.7, 0.3],  # Prioritize balance over flow
    aggregation="weighted_sum"
)

# Evaluate system health
score = composite.compute(
    {"cpu": 65, "memory": 70, "latency": 120},  # for balance
    state_history,  # for flow
    return_components=True
)

print(f"Overall health: {score['composite']:.2f}")
print(f"Balance contribution: {score['components'][0]:.2f}")
print(f"Flow contribution: {score['components'][1]:.2f}")

# Make decision
if score['composite'] < 0.6:
    trigger_alert("System health degraded")
```

### Example 4: Feature-Based Clustering

```python
from taocore import Graph, Node, ClusterMetric

# Knowledge graph with embeddings
graph = Graph()
for concept in concepts:
    graph.add_node(Node(
        concept.id,
        features=concept.embedding  # e.g., {"dim0": 0.5, "dim1": 0.8, ...}
    ))

# Cluster by semantic similarity
metric = ClusterMetric(
    algorithm="distance",
    threshold=0.3,  # Cosine distance threshold
    min_cluster_size=2
)

result = metric.compute(graph)

# Group related concepts
for cluster_id in range(result['num_clusters']):
    concepts_in_cluster = [
        node_id for node_id, cid in result['assignments'].items()
        if cid == cluster_id
    ]
    print(f"Cluster {cluster_id}: {concepts_in_cluster}")
```

### Example 5: Hierarchical Analysis

```python
from taocore import Graph, ClusterMetric, HubMetric

# 1. Detect communities
cluster_metric = ClusterMetric(algorithm="modularity")
clusters = cluster_metric.compute(graph)

# 2. Find hubs within each community
hub_metric = HubMetric(method="degree")

for cluster_id in range(clusters['num_clusters']):
    # Extract subgraph for this cluster
    nodes_in_cluster = [
        nid for nid, cid in clusters['assignments'].items()
        if cid == cluster_id
    ]
    subgraph = graph.subgraph(set(nodes_in_cluster))

    # Rank nodes within cluster
    hub_scores = hub_metric.compute(subgraph)
    leader = max(hub_scores.items(), key=lambda x: x[1])

    print(f"Cluster {cluster_id} leader: {leader[0]} (score: {leader[1]:.3f})")
```

---

## Integration with RFC-1

### Complementary Usage

**RFC-1 (stability):**
- BalanceMetric: Is the system within bounds?
- FlowMetric: Are transitions smooth?
- EquilibriumSolver: Does the system converge?

**RFC-2 (structure):**
- ClusterMetric: How is the system organized?
- HubMetric: What are the critical components?
- CompositeMetric: How do we weight multiple concerns?

**Combined example:**
```python
# Analyze both stability AND structure
balance = BalanceMetric(bounds={"load": (0, 1)})
cluster = ClusterMetric(algorithm="components")
hub = HubMetric(method="betweenness")

# Multi-dimensional system health
composite = CompositeMetric(
    metrics=[balance, cluster, hub],
    weights=[0.5, 0.2, 0.3]
)
```

### Backward Compatibility

RFC-2 metrics:
- ✓ Follow same `Metric` base class
- ✓ Same `compute()` interface pattern
- ✓ Compatible with existing code
- ✓ No breaking changes to RFC-1 APIs

---

## Performance Considerations

### Complexity Analysis

| Metric | Algorithm | Time | Space |
|--------|-----------|------|-------|
| ClusterMetric | Components | O(V + E) | O(V) |
| ClusterMetric | Modularity | O(V·E·iter) | O(V + E) |
| ClusterMetric | Distance | O(V²) | O(V²) |
| HubMetric | Degree | O(V) | O(V) |
| HubMetric | Betweenness | O(V²·E) | O(V²) |
| HubMetric | Eigenvector | O(V²·iter) | O(V²) |
| HubMetric | PageRank | O(V²·iter) | O(V) |
| CompositeMetric | Any | O(Σmetrics) | O(Σmetrics) |

### Scalability

**Current implementations suitable for:**
- Small-medium graphs (V < 10,000)
- Prototype/analysis workloads
- Non-time-critical applications

**Future optimizations (RFC-7):**
- Sparse matrix operations (scipy.sparse)
- Parallel BFS (multiprocessing)
- Approximate algorithms (sampling)
- GPU acceleration (CuPy)

**Design decision:** Correctness first, optimize later with profiling data.

---

## Acceptance Criteria

RFC-2 is considered complete when:

- [x] ClusterMetric implemented with 3 algorithms
- [x] HubMetric implemented with 4 centrality methods
- [x] CompositeMetric supports 4 aggregation modes
- [x] All metrics follow `Metric` base class
- [x] Comprehensive test suite (≥90% coverage)
- [x] Integration examples provided
- [x] Documentation complete
- [x] Backward compatible with RFC-1
- [x] Exports added to `__init__.py`
- [x] Verification script passes

**Status: ✓ All criteria met**

---

## Future Work

### RFC-3: Temporal Graph Metrics
- Time-windowed clustering
- Dynamic community detection
- Temporal centrality (considering edge timestamps)

### RFC-4: Advanced Composition
- Layered metrics (apply metric to metric outputs)
- Conditional composition (if-then metric selection)
- Adaptive weighting (learn from history)

### RFC-5: Metric Diagnostics
- Sensitivity analysis
- Stability under perturbations
- Confidence intervals for scores

### RFC-6: Specialized Algorithms
- Spectral clustering
- Label propagation
- Infomap community detection
- Katz centrality

---

## Conclusion

RFC-2 extends TaoCore with essential graph analysis capabilities while maintaining the core philosophy:

**Design principles preserved:**
- ✓ Domain-agnostic abstractions
- ✓ Explicit, interpretable algorithms
- ✓ Minimal dependencies (NumPy only)
- ✓ Composable components

**New capabilities:**
- ✓ Community detection (3 algorithms)
- ✓ Influence ranking (4 centrality measures)
- ✓ Flexible metric composition

**Production ready:**
- ✓ 100 tests passing
- ✓ 92% code coverage
- ✓ Comprehensive documentation
- ✓ Working examples

**TaoCore now supports both stability analysis (RFC-1) and structural analysis (RFC-2), providing a complete toolkit for reasoning about complex systems.**

---

## References

**Algorithms:**
- Louvain modularity: Blondel et al. (2008)
- Betweenness centrality: Brandes (2001)
- PageRank: Page et al. (1999)
- Eigenvector centrality: Bonacich (1987)

**Design inspiration:**
- NetworkX (API patterns)
- igraph (performance considerations)
- scikit-learn (composability patterns)

---

**Implementation:** 7 files, 1,500+ lines of code
**Testing:** 24 new tests, 92% coverage
**Status:** Implemented and verified ✓

Questions or contributions? See README.md for details.
