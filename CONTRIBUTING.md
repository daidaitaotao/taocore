# Contributing to TaoCore

Thank you for your interest in contributing to TaoCore! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Areas for Contribution

We welcome contributions in several areas:

1. **Core Features**
   - Additional metrics (spectral clustering, information-theoretic measures)
   - Performance optimizations (sparse matrices, GPU acceleration)
   - New solver algorithms (adaptive solvers, stochastic equilibrium)

2. **Documentation**
   - Tutorials and guides
   - API documentation improvements
   - Example use cases
   - Translation to other languages

3. **Testing**
   - Additional test cases
   - Edge case coverage
   - Performance benchmarks
   - Integration tests

4. **Tools & Integrations**
   - Visualization tools (trajectory plots, graph rendering)
   - Framework integrations (LangChain, AutoGen, etc.)
   - CI/CD improvements
   - Development tooling

5. **Bug Fixes**
   - Report and fix bugs
   - Improve error messages
   - Performance issues

## Development Setup

### Prerequisites

- Python 3.9, 3.10, 3.11, 3.12, or 3.13
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/taocore.git
cd taocore

# Install dependencies
make install

# Install development dependencies
make dev

# Run tests to verify setup
make test
```

### Development Tools

```bash
# Run tests with coverage
make coverage

# Format code
make format

# Type checking
make tox-type

# Linting
make tox-lint

# Test across all Python versions
make tox-all
```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check the [issue tracker](https://github.com/yourusername/taocore/issues) for existing reports
2. Verify the bug exists in the latest version

When reporting a bug, include:
- Python version and OS
- Minimal code to reproduce the issue
- Expected vs. actual behavior
- Full error traceback
- Any relevant configuration

**Use this template:**

```markdown
**Environment:**
- Python version: 3.11
- TaoCore version: 0.1.0
- OS: macOS 14.0

**Description:**
A clear description of the bug.

**Reproduction:**
\`\`\`python
# Minimal code to reproduce
from taocore import ...
\`\`\`

**Expected behavior:**
What you expected to happen.

**Actual behavior:**
What actually happened.

**Traceback:**
\`\`\`
Full error traceback here
\`\`\`
```

### Suggesting Features

Before suggesting a feature:
1. Check if it aligns with TaoCore's [design philosophy](README.md#design-philosophy)
2. Search existing issues and discussions
3. Consider if it can be implemented as an extension

Feature requests should include:
- **Use case**: What problem does it solve?
- **Proposed API**: How would users interact with it?
- **Alternatives**: Other approaches you considered
- **Domain-agnostic**: How does it generalize beyond your specific use case?

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation
   - Keep commits focused and atomic

4. **Test your changes**
   ```bash
   make test
   make coverage
   make tox-lint
   make tox-type
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `perf:` Performance improvements
   - `chore:` Maintenance tasks

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Type checking passes (`make tox-type`)
- [ ] Linting passes (`make tox-lint`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)
- [ ] All commits follow Conventional Commits format

### PR Guidelines

1. **Title**: Clear, descriptive summary (e.g., "Add spectral clustering to ClusterMetric")

2. **Description**: Include:
   - What changes were made
   - Why the changes are needed
   - Links to related issues
   - Breaking changes (if any)
   - Example usage (if applicable)

3. **Size**: Keep PRs focused and reasonably sized
   - Large changes should be discussed in an issue first
   - Consider breaking into smaller PRs

4. **Reviews**:
   - Address review feedback promptly
   - Request re-review after making changes
   - Be open to suggestions

### PR Template

```markdown
## Description
Brief description of changes.

## Related Issues
Fixes #123
Related to #456

## Changes Made
- Added X feature to Y module
- Updated Z documentation
- Added tests for W

## Breaking Changes
None / List any breaking changes

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Documentation
- [ ] README updated (if needed)
- [ ] Docstrings added/updated
- [ ] Examples added/updated

## Example Usage
\`\`\`python
# Show how to use new feature
from taocore import NewFeature
\`\`\`
```

## Coding Standards

### Code Style

TaoCore follows PEP 8 with some preferences:

- **Line length**: 100 characters (not 79)
- **Imports**: Group by standard library, third-party, local
- **Type hints**: Use type hints for all public APIs
- **Docstrings**: Google style docstrings

### Design Principles

Follow TaoCore's core principles:

1. **Descriptive, not prescriptive** - Analyze, don't optimize
2. **Domain-agnostic** - Work with any numeric state representation
3. **Explicit and inspectable** - All behavior is observable
4. **Minimal and composable** - Few primitives, powerful combinations

### Code Patterns

**Good:**
```python
def compute(self, state: StateVector, **params) -> float:
    """Compute metric value for given state.

    Args:
        state: Input state vector
        **params: Additional parameters

    Returns:
        Metric score in [0, 1]
    """
    # Clear, focused implementation
    ...
```

**Avoid:**
```python
def compute(self, state, optimize=True, auto_tune=True, ...):
    # Too many options, unclear purpose
    # Mixing optimization with measurement
    ...
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `EquilibriumSolver`, `BalanceMetric`)
- **Functions/methods**: snake_case (e.g., `compute`, `find_nodes`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_ITERATIONS`)
- **Private**: Prefix with `_` (e.g., `_internal_helper`)

## Testing Guidelines

### Test Requirements

All contributions must include tests:

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test feature combinations
- **Edge cases**: Test boundary conditions
- **Backward compatibility**: Ensure existing tests pass

### Test Structure

```python
def test_feature_name():
    """Test description of what's being tested."""
    # Setup
    input_data = ...
    expected = ...

    # Execute
    result = function_under_test(input_data)

    # Assert
    assert result == expected
    assert additional_condition
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_metrics.py

# Run specific test
uv run pytest tests/test_metrics.py::test_balance_metric

# Run with coverage
make coverage

# Test all Python versions
make tox-all
```

### Test Coverage

- Aim for >90% coverage for new code
- Focus on meaningful tests, not just coverage numbers
- Test both happy paths and error cases

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: int, param2: str) -> bool:
    """One-line summary.

    Longer description if needed. Can span multiple lines
    and include examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is negative

    Example:
        >>> example_function(42, "test")
        True
    """
    ...
```

### Documentation Updates

When adding features, update:
- API documentation (docstrings)
- README.md (if user-facing)
- Relevant RFC documents (if architectural)
- Examples (if helpful for users)

### Writing RFCs

For significant features, write an RFC (Request for Comments):

1. Copy `docs/rfc_template.md` to `docs/rfcN.md`
2. Fill in all sections
3. Submit as PR for discussion
4. Implement after approval

## Community

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/taocore/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/taocore/discussions)
- **Twitter**: [@taocore_dev](https://twitter.com/taocore_dev)

### Communication Guidelines

- Be respectful and constructive
- Assume good intentions
- Focus on ideas, not individuals
- Welcome newcomers

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md
- Release notes
- GitHub contributor graph

Thank you for contributing to TaoCore!

---

**Questions?** Open a [discussion](https://github.com/yourusername/taocore/discussions) or reach out to the maintainers.
