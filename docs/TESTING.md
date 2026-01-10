# Testing Guide

TaoCore uses a comprehensive testing strategy to ensure reliability across multiple Python versions and configurations.

## Quick Start

```bash
# Install development dependencies
make dev

# Run tests (current Python version)
make test

# Run tests with coverage
make coverage
```

## Python Version Support

TaoCore supports Python **3.9, 3.10, 3.11, 3.12, and 3.13**.

### Version-Specific Requirements

- **Python 3.9-3.12**: NumPy >= 1.24.0
- **Python 3.13**: NumPy >= 1.26.0 (due to compatibility requirements)

## Testing with Tox

Tox allows testing across multiple Python versions in isolated environments.

### Basic Tox Commands

```bash
# Test with current Python version (3.9)
make tox

# Test with all Python versions (requires all versions installed)
make tox-all

# Run linting checks
make tox-lint

# Run type checking
make tox-type
```

### Tox Environment Matrix

| Environment | Description |
|-------------|-------------|
| `py39` | Test with Python 3.9 |
| `py310` | Test with Python 3.10 |
| `py311` | Test with Python 3.11 |
| `py312` | Test with Python 3.12 |
| `py313` | Test with Python 3.13 (requires NumPy >= 1.26.0) |
| `lint` | Run ruff linting |
| `type` | Run mypy type checking |
| `coverage` | Generate coverage report |

### Advanced Tox Usage

```bash
# Test specific Python version
uv run tox -e py311

# Test multiple specific versions
uv run tox -e py39,py311,py313

# Run tests in parallel
uv run tox -p auto

# Recreate environments (clean install)
uv run tox -r
```

## Coverage Reports

TaoCore maintains **94% test coverage**.

### Generate Coverage Report

```bash
# Terminal + HTML report
make coverage

# View HTML report
open htmlcov/index.html
```

### Coverage Breakdown

Coverage is tracked across all modules:
- **Primitives**: Node, Edge, Graph, StateVector
- **Metrics**: BalanceMetric, FlowMetric, AttentionMetric
- **Solvers**: EquilibriumSolver
- **Policies**: Decider, Decision

## Test Organization

```
tests/
├── test_primitives.py       # Core primitive tests
├── test_temporal.py          # Temporal feature tests
├── test_metrics.py           # Metric tests
├── test_attention.py         # AttentionMetric tests
├── test_solvers.py           # Equilibrium solver tests
├── test_policies.py          # Policy/decider tests
├── test_edge_cases.py        # Boundary conditions
└── test_integration.py       # End-to-end workflows
```

### Test Categories

1. **Unit Tests** (`test_primitives.py`, `test_metrics.py`, etc.)
   - Test individual components in isolation
   - Focus on API contracts and edge cases

2. **Integration Tests** (`test_integration.py`)
   - Test components working together
   - End-to-end workflows (e.g., temporal graph + attention)

3. **Edge Case Tests** (`test_edge_cases.py`)
   - Boundary conditions (empty inputs, zero values)
   - Error handling and graceful degradation

## Writing Tests

### Test Conventions

- Use descriptive test names: `test_<component>_<behavior>`
- Include docstrings explaining what is being tested
- Test both happy path and edge cases
- Ensure backward compatibility

### Example Test

```python
def test_node_with_timestamp():
    """Test node with temporal features."""
    node = Node(id="n1", features={"x": 1.0}, timestamp=100.0, decay_rate=0.1)

    assert node.timestamp == 100.0
    assert node.decay_rate == 0.1
    assert node.age(150.0) == 50.0

    # Strength should decay
    strength = node.compute_strength(150.0)
    assert 0.0 < strength < 1.0
```

## Continuous Integration

TaoCore uses GitHub Actions for CI/CD:

- **Test Matrix**: Runs tests on Python 3.9-3.13
- **Linting**: Checks code style with ruff
- **Type Checking**: Validates types with mypy
- **Coverage**: Generates coverage reports

See `.github/workflows/test.yml` for configuration.

## Installing Multiple Python Versions

### Using pyenv

```bash
# Install pyenv
curl https://pyenv.run | bash

# Install Python versions
pyenv install 3.9.19
pyenv install 3.10.14
pyenv install 3.11.9
pyenv install 3.12.4
pyenv install 3.13.1

# Make all versions available
pyenv local 3.9.19 3.10.14 3.11.9 3.12.4 3.13.1

# Verify tox can find all versions
uv run tox -e py39,py310,py311,py312,py313
```

### Using asdf

```bash
# Install asdf Python plugin
asdf plugin add python

# Install Python versions
asdf install python 3.9.19
asdf install python 3.10.14
asdf install python 3.11.9
asdf install python 3.12.4
asdf install python 3.13.1

# Set local versions
asdf local python 3.9.19 3.10.14 3.11.9 3.12.4 3.13.1
```

## Troubleshooting

### Tox can't find Python version

```bash
# Check which Python versions are available
tox --listenvs-all

# Verify Python is in PATH
which python3.11

# Use skip_missing_interpreters (already configured in tox.ini)
uv run tox --skip-missing-interpreters
```

### NumPy compatibility issues

For Python 3.13, ensure NumPy >= 1.26.0:

```bash
# The tox.ini already handles this automatically
uv run tox -e py313
```

### Clean rebuild

```bash
# Remove tox environments and caches
make clean

# Reinstall dependencies
make dev

# Rebuild tox environments
uv run tox -r
```

## Performance Benchmarks

Current test performance (Python 3.9, M2 Mac):
- **76 tests** complete in **~0.05 seconds**
- Tox full run (with environment setup): **~17 seconds**
- Coverage generation adds **~0.02 seconds**

## Next Steps

- Consider adding property-based testing with Hypothesis
- Add performance regression tests
- Set up mutation testing with mutmut
- Add benchmark suite for performance tracking
