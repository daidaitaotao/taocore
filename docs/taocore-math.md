# TaoCore: Math and Logic Explained (Engineer-Friendly Deep Dive)

This document explains how TaoCore works at the math/logic level for software engineers without a data science background. It focuses on the “why” behind each component, the minimal math you need, and how the pieces fit together.

## 1. Mental Model

TaoCore treats a system as:

- A **graph** of entities (nodes) and relationships (edges).
- A **state vector** that captures the current numeric snapshot of the system.
- A set of **metrics** that measure structure and dynamics.
- An **equilibrium solver** that repeatedly applies an update rule until the system stabilizes.

You can think of it like:

1. Build a graph and a state vector.
2. Compute metrics to describe structure and behavior.
3. Run a fixed-point iteration to find a stable state.
4. Use a policy/decider to interpret results.

## 2. Core Primitives

### 2.1 Node

A `Node` is an entity with numeric features and optional time decay:

- `features`: dict of numeric values (e.g., `"energy": 0.7`).
- `timestamp` + `decay_rate`: allow the node’s strength to decay over time.

**Strength** is exponential decay:

```
strength(t) = exp(-decay_rate * age)
```

This gives you a clean, monotonic “freshness” factor.

### 2.2 Edge

An `Edge` connects two nodes and can be directed or undirected:

- `weight` is a real number.
- `directed=False` makes the adjacency symmetric.
- Edges can also decay over time like nodes.

### 2.3 Graph

`Graph` stores nodes, edges, and adjacency:

- `neighbors(node)` returns outgoing neighbors.
- BFS-based utilities support k-hop and shortest paths.

Note: If you add only one directed edge, the graph is directed for that pair. If you want undirected behavior, set `directed=False` on the edge.

Implementation reference:
- `src/taocore/primitives/graph.py` for adjacency
- `src/taocore/primitives/edge.py` for `directed` semantics

### 2.4 StateVector

`StateVector` is a numeric vector used by solvers and metrics:

- It can be built from a dict or a NumPy array.
- If dict-based, keys are sorted to guarantee alignment.
- Distance uses Euclidean (L2) norm:

```
distance(a, b) = ||a - b||_2
```

If dict keys or shapes mismatch, the distance is invalid and raises a `ValueError`.

Implementation reference:
- `src/taocore/primitives/state.py`

## 3. Equilibrium Solver (Fixed-Point Iteration)

The solver repeatedly applies an update rule until the system stabilizes. This is the classic **fixed-point iteration**:

```
x_{t+1} = f(x_t)
```

If the sequence converges, it reaches a fixed point `x*` where:

```
f(x*) = x*
```

This is a standard numerical method used to find stable points of a function. citeturn1search46

### 3.1 Convergence Criteria

TaoCore tracks residuals:

```
residual_t = ||x_{t+1} - x_t||_2
```

Convergence occurs when residuals fall below a tolerance for a given number of steps. It also detects oscillations (2-cycle or 3-cycle) and reports them as a failure mode.

Implementation reference:
- `src/taocore/solvers/equilibrium.py`

### 3.2 Why This Matters

Many complex systems “settle” even if individual signals conflict. The fixed-point iteration gives a principled way to find that settled point, or to detect that no stable state exists.

## 4. Metrics: What They Measure

### 4.1 BalanceMetric (Bounds Compliance)

Given bounds for each feature, the metric scores how far values are from acceptable ranges:

```
score = 1.0                       if min <= value <= max
score = max(0, 1 - dist / range)  otherwise
```

This is a simple, interpretable penalty curve that degrades linearly as values move out of bounds.

Implementation reference:
- `src/taocore/metrics/balance.py`

### 4.2 FlowMetric (Dynamics)

Given a sequence of state vectors, define deltas:

```
delta_t = x_{t+1} - x_t
```

Modes:

- **Coherence:** if the step sizes are consistent, the system is “coherent.”
- **Volatility:** average magnitude of changes.
- **Directionality:** average cosine similarity between consecutive deltas (alignment of direction).

Cosine similarity measures alignment of directions and ranges from -1 to 1. citeturn0search2

Implementation reference:
- `src/taocore/metrics/flow.py`

### 4.3 ClusterMetric (Graph Structure)

TaoCore supports:

- **Connected components:** groups where each node can reach every other node (for undirected graphs). citeturn1search1
- **Modularity (greedy heuristic):** finds communities by local improvement.
- **Distance-based:** clusters by feature distance thresholds.

The connected-components approach is based on reachability within the graph. citeturn3view3

Implementation reference:
- `src/taocore/metrics/cluster.py`

### 4.4 HubMetric (Influence / Centrality)

Supported centrality measures:

- **Degree:** number of direct neighbors. citeturn0search50
- **Betweenness:** frequency of appearing on shortest paths. citeturn0search49
- **Eigenvector:** importance via connections to important nodes. citeturn0search48
- **PageRank:** random-surfer importance with damping. citeturn2search43

PageRank handles nodes with no outgoing edges by redistributing their rank across all nodes (dangling-node handling). citeturn2search43

Implementation reference:
- `src/taocore/metrics/hub.py`

### 4.5 AttentionMetric (Relevance)

Two modes:

- **Similarity:** cosine or Euclidean-based similarity between query and target features.
- **Composite:** weighted mix of similarity, recency, and strength.

Cosine similarity is the main “directional similarity” measure. citeturn0search2

Implementation reference:
- `src/taocore/metrics/attention.py`

### 4.6 CompositeMetric (Weighted Fusion)

Combines multiple metrics with explicit weights:

```
composite = sum(weight_i * metric_i)
```

Weights are exposed directly; no magic normalization unless you ask for it.

Implementation reference:
- `src/taocore/metrics/composite.py`

## 5. Why This Design Is Practical

TaoCore is meant to be:

- **Deterministic**: no hidden randomness in metrics.
- **Inspectable**: metrics and weights are explicit.
- **Fail-safe**: oscillation and non-convergence are surfaced, not hidden.

This makes it suitable for systems where you want *explainability and stability*, not just prediction accuracy.

## 6. Evidence in the Codebase

There are unit and integration tests that validate:

- Graph traversal and shortest paths.
- Metric behavior under edge cases.
- Equilibrium convergence and oscillation detection.
- Attention scoring and temporal decay.

See `tests/` for concrete examples.

Recommended tests to read:
- `tests/test_solvers.py` (convergence and oscillation)
- `tests/test_metrics.py` (balance/flow/cluster/hub/composite)
- `tests/test_attention.py` (similarity and composite attention)

## 7. How to Read TaoCore as an Engineer

1. Start with `primitives` to understand the data model.
2. Review `metrics` to see how structure and dynamics are quantified.
3. Read `solvers/equilibrium.py` to see fixed-point iteration logic.
4. Look at tests to see intended behavior and edge cases.

If you want a guided walkthrough of any part, I can add it.

## References

- Fixed-point iteration (definition and convergence framing): https://en.wikipedia.org/wiki/Fixed-point_iteration
- Cosine similarity (definition and range): https://www.ibm.com/think/topics/cosine-similarity
- Connected components (definition): https://www.baeldung.com/cs/graph-connected-components
- Degree centrality (definition): https://en.wikipedia.org/wiki/Centrality
- Betweenness centrality (definition): https://en.wikipedia.org/wiki/Betweenness_centrality
- Eigenvector centrality (definition): https://en.wikipedia.org/wiki/Eigenvector_centrality
- PageRank (random surfer model and dangling-node handling): https://en.wikipedia.org/wiki/PageRank
