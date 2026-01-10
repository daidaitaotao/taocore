# TaoCore

Systems layer for stability, coherence, and dynamics analysis.

## Overview

TaoCore is a pure, abstract core for reasoning about system behavior. It sits above ML models and provides:

- **Stability analysis** via equilibrium computation
- **Coherence evaluation** via flow metrics
- **Balance assessment** via bounded stability metrics
- **Explicit policy decisions** via deciders
- **Temporal primitives** for time-aware graph dynamics
- **Graph query methods** for traversal and filtering
- **Attention metrics** for relevance scoring

## Requirements

- **Python**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Dependencies**: NumPy >= 1.24.0 (>= 1.26.0 for Python 3.13)

## Installation

```bash
make install
```

Or with uv directly:

```bash
uv sync
```

## Quick Start

### Local Development

Run the comprehensive demo to see all features in action:

```bash
make demo
```

This demonstrates:
- All primitives (Node, Edge, Graph, StateVector)
- Balance and Flow metrics
- Equilibrium solver with various systems
- Policy-based decision making
- Practical service monitoring example

### Docker

Run in a Docker container:

```bash
# Build and run demo
make docker-build
make docker-demo

# Run tests
make docker-test
```

See [docs/DOCKER.md](docs/DOCKER.md) for comprehensive Docker guide.

## Development

Install dev dependencies:

```bash
make dev
```

Run tests:

```bash
make test
```

Run tests across multiple Python versions with tox:

```bash
make tox          # Test with Python 3.9
make tox-all      # Test with all supported Python versions
make tox-lint     # Run linting checks
make tox-type     # Run type checking
```

Run tests with coverage:

```bash
make coverage     # Generate coverage report (HTML in htmlcov/)
```

Format code:

```bash
make format
```

### Testing Matrix

TaoCore is tested against:
- Python 3.9, 3.10, 3.11, 3.12, 3.13
- NumPy 1.24.0+ (1.26.0+ for Python 3.13)
- Current test coverage: **94%**

For comprehensive testing documentation, see [docs/TESTING.md](docs/TESTING.md).

## Core Primitives

### Node
Entity with numeric state.

```python
from taocore import Node

node = Node(id="n1", features={"x": 1.0, "y": 2.0})
```

### Edge
Directed or undirected relationship with weight.

```python
from taocore import Edge

edge = Edge(source="n1", target="n2", weight=0.5)
```

### Graph
Container for nodes and edges with topology queries.

```python
from taocore import Graph, Node, Edge

graph = Graph()
graph.add_node(Node("n1"))
graph.add_node(Node("n2"))
graph.add_edge(Edge("n1", "n2", 1.0))
```

### StateVector
Numeric state representation for equilibrium computation.

```python
from taocore import StateVector
import numpy as np

state = StateVector({"a": 1.0, "b": 2.0})
# or
state = StateVector(np.array([1.0, 2.0]))
```

## Metrics

### BalanceMetric
Evaluates whether values lie within desirable operating regime.

```python
from taocore import BalanceMetric

metric = BalanceMetric(bounds={"x": (0.0, 10.0), "y": (0.0, 5.0)})
score = metric.compute({"x": 5.0, "y": 2.5})
```

### FlowMetric
Evaluates directional change and coherence.

```python
from taocore import FlowMetric, StateVector
import numpy as np

states = [
    StateVector(np.array([0.0, 0.0])),
    StateVector(np.array([1.0, 1.0])),
    StateVector(np.array([2.0, 2.0])),
]

metric = FlowMetric(mode="coherence")
score = metric.compute(states)
```

## Equilibrium Solver

Finds stable states through iterative updates.

```python
from taocore import EquilibriumSolver, StateVector
import numpy as np

def update_rule(state: StateVector) -> StateVector:
    return StateVector(state.array * 0.5)

solver = EquilibriumSolver(max_iterations=100, tolerance=1e-6)
initial = StateVector(np.array([10.0, 10.0]))

result = solver.solve(initial, update_rule)
print(f"Converged: {result.converged}")
print(f"Iterations: {result.iterations}")
```

## Design Principles

1. **Abstraction before semantics** - No domain-specific logic
2. **Stability over prediction** - Evaluates coherence, not accuracy
3. **Explicit structure** - All components are inspectable
4. **Model agnostic** - Works with any ML model outputs
5. **Minimalism** - Few primitives, well defined

## License

MIT
