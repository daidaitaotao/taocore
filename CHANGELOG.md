# Changelog

All notable changes to TaoCore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-10

### Added
- **Core Primitives**
  - `Node`: Entity with numeric state and optional temporal features
  - `Edge`: Directed relationship with weight and optional temporal decay
  - `Graph`: Container for nodes and edges with topology queries
  - `StateVector`: Numeric state representation for equilibrium computation

- **Temporal Features**
  - Optional `timestamp` and `decay_rate` parameters for Node and Edge
  - Exponential decay functions: `age()`, `compute_strength()`, `is_expired()`
  - Backward compatible (all temporal features are opt-in)

- **Graph Query Methods**
  - `find_nodes(predicate)`: Filter nodes by predicate function
  - `filter_edges(predicate)`: Filter edges by predicate function
  - `k_hop_neighbors(node_id, k)`: BFS to find nodes within k hops
  - `shortest_path(source, target)`: BFS shortest path finding
  - `subgraph(node_ids)`: Extract subgraph with specified nodes

- **Metrics**
  - `BalanceMetric`: Evaluates if values lie within desirable bounds
  - `FlowMetric`: Evaluates directional change and coherence
  - `AttentionMetric`: Relevance and salience computation
    - Similarity mode: Cosine and Euclidean similarity
    - Composite mode: Weighted combination of similarity, recency, and strength

- **Solvers**
  - `EquilibriumSolver`: Finds stable states through iterative updates
  - Configurable convergence tolerance and max iterations

- **Policies**
  - `Decider` ABC: Framework for policy-driven decision making
  - `Decision` dataclass: Structured decision output

- **Testing Infrastructure**
  - Comprehensive test suite (76 tests, 94% coverage)
  - Tox configuration for Python 3.9-3.13
  - GitHub Actions CI/CD
  - Coverage reporting

- **Documentation**
  - README with quick start guide
  - TESTING.md with comprehensive testing guide
  - Docker support (Dockerfile, docker-compose.yml)

### Python Support
- Python 3.9, 3.10, 3.11, 3.12, 3.13
- NumPy >= 1.24.0 (>= 1.26.0 for Python 3.13)

### Development
- Built with `uv` for fast, modern Python tooling
- Linting with `ruff`
- Type checking with `mypy`
- Testing with `pytest` and `tox`

[Unreleased]: https://github.com/yourusername/taocore/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/taocore/releases/tag/v0.1.0
