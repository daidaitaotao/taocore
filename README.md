# TaoCore

**A systems-level abstraction layer for reasoning about stability, coherence, and dynamics in complex systems.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-115%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](docs/TESTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Why TaoCore?

Modern ML systems operate in a black box—predict, classify, recommend—but rarely **explain their behavior** or **guarantee stability**. When you ask:

> "Will this system stay within acceptable bounds?"
>
> "Are these state transitions coherent?"
>
> "What equilibrium will this converge to?"

...you get silence.

**TaoCore provides answers.**

It's a domain-agnostic layer that sits **above** ML models, data pipelines, and agent systems to analyze:

- **Stability** – Does the system reach equilibrium?
- **Coherence** – Are transitions smooth and directional?
- **Balance** – Do values stay within operating bounds?
- **Structure** – How are components organized and connected?

Unlike optimization frameworks, TaoCore doesn't tell systems what to do—it **observes** and **analyzes** what they actually do.

---

## Quick Start

### Installation

```bash
pip install taocore
```

Or from source:

```bash
git clone https://github.com/yourusername/taocore.git
cd taocore
make install
```

### 30-Second Example

```python
from taocore import EquilibriumSolver, StateVector, ConvergenceReason
import numpy as np

# Define system dynamics
def damping_rule(state):
    return StateVector(state.array * 0.9)

# Find equilibrium
solver = EquilibriumSolver(tolerance=1e-6)
result = solver.solve(
    initial=StateVector(np.array([10.0, 5.0])),
    update_rule=damping_rule
)

# Analyze results
if result.converged:
    print(f"✓ Equilibrium reached in {result.iterations} iterations")
    print(f"  Stability score: {result.stability_score:.3f}")
else:
    print(f"✗ {result.convergence_reason.value}")
    if result.oscillation_detected:
        print("  System is oscillating—conflicting dynamics")
```

**Output:**
```
✓ Equilibrium reached in 65 iterations
  Stability score: 0.847
```

---

## Core Concepts

### 1. Equilibrium as First-Class Abstraction

Instead of asking "what's the answer right now?", TaoCore asks:

> **"What does this system settle into when signals interact?"**

Equilibrium represents **consensus**, **resistance to noise**, and **stable interpretation**.

```python
from taocore import EquilibriumSolver, StateVector

# System with competing forces
def weighted_average(state):
    # Move 30% toward target [5, 5]
    target = np.array([5.0, 5.0])
    return StateVector(0.7 * state.array + 0.3 * target)

solver = EquilibriumSolver()
result = solver.solve(StateVector(np.array([0.0, 10.0])), weighted_average)

print(f"Converged to: {result.state.array}")
# Output: Converged to: [5.0, 5.0]
```

### 2. Metrics Without Objectives

TaoCore provides **descriptive metrics**, not prescriptive loss functions:

- **BalanceMetric** – Are values within acceptable bounds?
- **FlowMetric** – How coherent are state transitions?
- **ClusterMetric** – How is the system organized?
- **HubMetric** – What components are most influential?

```python
from taocore import BalanceMetric

# Define operating regime
metric = BalanceMetric(bounds={
    "cpu": (0, 80),      # %
    "memory": (0, 90),    # %
    "latency": (0, 200)   # ms
})

# Evaluate system health
score = metric.compute({
    "cpu": 65,
    "memory": 70,
    "latency": 120
})
print(f"Balance: {score:.2f}")  # 1.00 = perfect balance
```

### 3. Graph Analysis

Analyze system structure and relationships:

```python
from taocore import Graph, Node, Edge, HubMetric, ClusterMetric

# Build service dependency graph
graph = Graph()
for service in ["api", "db", "cache", "auth"]:
    graph.add_node(Node(service))

graph.add_edge(Edge("api", "db"))
graph.add_edge(Edge("api", "cache"))
graph.add_edge(Edge("api", "auth"))

# Find critical services
hub_metric = HubMetric(method="pagerank")
importance = hub_metric.compute(graph)
print(f"Most critical: {max(importance.items(), key=lambda x: x[1])}")

# Detect communities
cluster_metric = ClusterMetric(algorithm="modularity")
clusters = cluster_metric.compute(graph)
print(f"Found {clusters['num_clusters']} service groups")
```

---

## Features

### Primitives

- **Node** – Entities with numeric features
- **Edge** – Weighted relationships
- **Graph** – Topology with traversal and filtering
- **StateVector** – Dual dict/array representation

### Metrics

- **BalanceMetric** – Bounded stability analysis
- **FlowMetric** – Temporal coherence (volatility, directionality)
- **AttentionMetric** – Similarity and relevance scoring
- **ClusterMetric** – Community detection (components, modularity, distance)
- **HubMetric** – Centrality measures (degree, betweenness, eigenvector, PageRank)
- **CompositeMetric** – Weighted metric combinations

### Solvers

- **EquilibriumSolver** – Fixed-point iteration with:
  - Multiple convergence criteria (tolerance, stability window)
  - Oscillation detection (2-cycle, 3-cycle, general)
  - Comprehensive diagnostics (stability score, convergence reason)
  - Failure mode reporting

### Extensions (RFC-1)

- **Temporal primitives** – Timestamps, decay rates, expiration
- **Graph queries** – k-hop neighbors, shortest paths, subgraphs

---

## Real-World Use Cases

### 1. Service Mesh Health Monitoring

```python
from taocore import BalanceMetric, FlowMetric, StateVector, CompositeMetric

# Define health metrics
balance = BalanceMetric(bounds={
    "error_rate": (0, 0.05),
    "latency_p99": (0, 500),
    "cpu_usage": (0, 80)
})

flow = FlowMetric(mode="volatility")

# Combine metrics
health_metric = CompositeMetric(
    metrics=[balance, flow],
    weights=[0.7, 0.3],  # Prioritize balance
    aggregation="weighted_sum"
)

# Monitor system
current_state = {"error_rate": 0.02, "latency_p99": 350, "cpu_usage": 65}
history = [...]  # Previous states

health_score = health_metric.compute(current_state, history)

if health_score < 0.6:
    trigger_alert("System health degraded")
```

### 2. Multi-Agent Consensus

```python
# Agents updating beliefs based on neighbors
def agent_update(agent_id):
    def update_belief(state):
        neighbors = graph.neighbors(agent_id)
        neighbor_beliefs = [agents[n].belief for n in neighbors]
        # Move toward average
        avg = np.mean(neighbor_beliefs, axis=0)
        return StateVector(0.7 * state.array + 0.3 * avg)
    return update_belief

# Find equilibrium for each agent
solver = EquilibriumSolver(stability_window=5)
for agent_id, agent in agents.items():
    result = solver.solve(
        StateVector(agent.initial_belief),
        agent_update(agent_id)
    )
    agent.consensus_belief = result.state
```

### 3. Photo Memory Analysis (Temporal Graph)

```python
from taocore import Node, Graph, AttentionMetric

# Build memory graph with temporal decay
memories = []
current_time = time.time()

for photo in photos:
    node = Node(
        id=photo.id,
        features=photo.embedding,
        timestamp=photo.timestamp,
        decay_rate=0.01  # Decay over time
    )
    memories.append(node)

# Query relevant memories
attention = AttentionMetric(mode="composite")
query = {"joy": 0.8, "outdoor": 0.9}

scores = attention.compute(
    query=query,
    target=memories,
    current_time=current_time
)

# Filter expired or weak memories
relevant = [m for m, score in scores.items()
            if score > 0.5 and not memories[m].is_expired(current_time)]
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Applications                         │
│  (Service monitoring, agent systems, memory analysis, ...)  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                        TaoCore Layer                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Metrics    │  │   Solvers    │  │   Policies   │     │
│  │              │  │              │  │              │     │
│  │  Balance     │  │  Equilibrium │  │  Decider     │     │
│  │  Flow        │  │  Convergence │  │  Decision    │     │
│  │  Attention   │  │  Oscillation │  │              │     │
│  │  Cluster     │  │  Diagnostics │  │              │     │
│  │  Hub         │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                             │                               │
│  ┌──────────────────────────┴─────────────────────────┐   │
│  │              Primitives                              │   │
│  │  Node │ Edge │ Graph │ StateVector                  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    ML Models & Data                          │
│  (Neural networks, embeddings, feature extractors, ...)     │
└──────────────────────────────────────────────────────────────┘
```

**TaoCore sits between your models and your application logic, providing:**
- ✓ Stability analysis for model outputs
- ✓ Structural analysis of system relationships
- ✓ Equilibrium finding for multi-agent dynamics
- ✓ Quality metrics without optimization objectives

---

## Design Philosophy

### What TaoCore Is

- **Descriptive, not prescriptive** – Analyzes what systems do, doesn't tell them what to do
- **Domain-agnostic** – Works with any numeric state representation
- **Explicit and inspectable** – All behavior is observable
- **Minimal and composable** – Few primitives, powerful combinations

### What TaoCore Is Not

- ❌ **Not an ML framework** – No training, no gradient descent
- ❌ **Not an optimization library** – No loss functions, no objectives
- ❌ **Not a control system** – No feedback loops, no actuation
- ❌ **Not domain-specific** – No assumptions about what data represents

### Core Principles

1. **Equilibrium over optimization** – Seek stable states, not optimal solutions
2. **Stability over prediction** – Measure coherence, not accuracy
3. **Structure over semantics** – Analyze relationships, not meanings
4. **Diagnostics as data** – Failure modes are signals, not errors

---

## Documentation

- **[RFC-1: Core Systems Layer](docs/rfc1.md)** – Primitives, metrics, equilibrium
- **[RFC-2: Advanced Metrics](docs/rfc2.md)** – Clustering, hubs, composition
- **[RFC-3: Enhanced Equilibrium](docs/rfc3.md)** – Oscillation detection, diagnostics
- **[Testing Guide](docs/TESTING.md)** – Comprehensive testing documentation
- **[Publishing Guide](PUBLISHING.md)** – PyPI release process
- **[Docker Guide](docs/DOCKER.md)** – Container deployment

---

## Development

### Requirements

- **Python**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Dependencies**: NumPy ≥ 1.24.0 (≥ 1.26.0 for Python 3.13)

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/taocore.git
cd taocore

# Install dependencies
make install

# Install dev dependencies
make dev
```

### Testing

```bash
# Run tests
make test

# Run with coverage
make coverage

# Test across Python versions
make tox-all

# Run linting and type checking
make tox-lint
make tox-type
```

**Current metrics:**
- 115 tests passing
- 92% code coverage
- Supports Python 3.9-3.13

### Code Quality

```bash
# Format code
make format

# Type checking
make tox-type

# Linting
make tox-lint
```

---

## Examples

Comprehensive examples in [`examples/`](examples/):

- **[rfc1_verification.py](examples/rfc1_verification.py)** – Core primitives and metrics
- **[rfc2_verification.py](examples/rfc2_verification.py)** – Graph analysis features
- **[rfc3_verification.py](examples/rfc3_verification.py)** – Enhanced equilibrium solver

Run examples:

```bash
uv run python examples/rfc1_verification.py
uv run python examples/rfc2_verification.py
uv run python examples/rfc3_verification.py
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas for contribution:**
- Additional metrics (spectral clustering, information-theoretic measures)
- Performance optimizations (sparse matrices, GPU acceleration)
- Visualization tools (trajectory plots, graph rendering)
- Integration examples (with popular frameworks)
- Documentation improvements

---

## Citation

If you use TaoCore in your research, please cite:

```bibtex
@software{taocore2026,
  title = {TaoCore: A Systems-Level Abstraction Layer for Stability and Coherence Analysis},
  author = {TaoCore Contributors},
  year = {2026},
  url = {https://github.com/yourusername/taocore},
  version = {0.1.0}
}
```

---

## License

[MIT License](LICENSE)

---

## Roadmap

### v0.2.0 (Q1 2026)
- Adaptive solvers with auto-tuning
- Stochastic equilibrium analysis
- Performance benchmarks

### v0.3.0 (Q2 2026)
- Visualization toolkit
- Multi-attractor analysis
- Integration examples (LangChain, AutoGen, etc.)

### v1.0.0 (Q3 2026)
- Production-ready API freeze
- Comprehensive documentation site
- Community governance model

---

## Community

- **Issues**: [GitHub Issues](https://github.com/yourusername/taocore/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/taocore/discussions)
- **Twitter**: [@taocore_dev](https://twitter.com/taocore_dev)

---

**Built with ❤️ by the TaoCore team**

*Seeking equilibrium in complex systems, one fixed point at a time.*
## TaoCore Human CLI (Companion)

If you are using TaoCore for human behavior pipelines, the companion package `taocore-human` exposes a minimal CLI that OpenClaw can call via `exec`:

```bash
cd /Users/dadatoto/taocore-human
python -m pip install -e .

taocore-human photo-folder /path/to/photos
taocore-human video /path/to/video.mp4
```

It returns JSON to stdout or `--output <file>`.

