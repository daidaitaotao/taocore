# TaoCore Publishing Guide

This document explains how TaoCore is packaged and published to PyPI.

## Package Overview

**Package Name**: `taocore`
**Current Version**: `0.1.0`
**License**: MIT
**Python Support**: 3.9, 3.10, 3.11, 3.12, 3.13

## Quick Start: Publishing to PyPI

### Option 1: Automated Script (Recommended)

```bash
# Run the interactive release script
./scripts/release.sh
```

The script will:
1. Run all tests
2. Update version number
3. Build package
4. Optionally publish to TestPyPI or PyPI
5. Create git tags
6. Push to GitHub

### Option 2: Manual Steps

```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md

# 3. Run tests
make test
make tox-all

# 4. Clean and build
make clean
rm -rf dist/
make build

# 5. Check distribution
make check-dist

# 6. Publish to TestPyPI (optional)
make publish-test

# 7. Publish to PyPI
make publish

# 8. Git operations
git add pyproject.toml CHANGELOG.md
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Version X.Y.Z"
git push origin main
git push origin vX.Y.Z
```

## Package Structure

```
taocore/
├── src/taocore/          # Source code
│   ├── __init__.py       # Main exports
│   ├── primitives/       # Node, Edge, Graph, StateVector
│   ├── metrics/          # BalanceMetric, FlowMetric, AttentionMetric
│   ├── solvers/          # EquilibriumSolver
│   └── policies/         # Decider, Decision
├── tests/                # Test suite (76 tests, 94% coverage)
├── docs/                 # Documentation
├── examples/             # Example code
├── pyproject.toml        # Package metadata
├── README.md             # Package description (shown on PyPI)
├── LICENSE               # MIT License
├── CHANGELOG.md          # Version history
└── MANIFEST.in           # Files to include in distribution
```

## Distribution Artifacts

When you run `make build`, two files are created in `dist/`:

1. **Source Distribution** (`taocore-X.Y.Z.tar.gz`)
   - Contains all source code
   - Users can install with: `pip install taocore-X.Y.Z.tar.gz`
   - Used when wheels aren't available

2. **Wheel** (`taocore-X.Y.Z-py3-none-any.whl`)
   - Pre-built binary package
   - Faster installation
   - Pure Python (works on all platforms)

## PyPI Configuration

### Metadata (pyproject.toml)

```toml
[project]
name = "taocore"
version = "0.1.0"
description = "Systems layer for stability, coherence, and dynamics analysis"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [{name = "TaoCore Contributors"}]
keywords = ["graph", "dynamics", "equilibrium", ...]
classifiers = [...]
dependencies = ["numpy>=1.24.0"]
```

### URLs

Update these in `pyproject.toml` with your GitHub username:

```toml
[project.urls]
Homepage = "https://github.com/YOURUSERNAME/taocore"
Repository = "https://github.com/YOURUSERNAME/taocore"
Issues = "https://github.com/YOURUSERNAME/taocore/issues"
Changelog = "https://github.com/YOURUSERNAME/taocore/releases"
```

## Authentication

### Setup PyPI API Tokens

1. **Create accounts**:
   - TestPyPI: https://test.pypi.org/account/register/
   - PyPI: https://pypi.org/account/register/

2. **Generate API tokens**:
   - TestPyPI: https://test.pypi.org/manage/account/token/
   - PyPI: https://pypi.org/manage/account/token/

3. **Configure** (copy `.pypirc.template` to `~/.pypirc`):
   ```ini
   [pypi]
   username = __token__
   password = pypi-YOUR_PRODUCTION_TOKEN_HERE

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-YOUR_TEST_TOKEN_HERE
   ```

**Security**: Never commit `~/.pypirc` to git! It contains sensitive tokens.

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make build` | Build source distribution and wheel |
| `make check-dist` | Validate package with twine |
| `make publish-test` | Publish to TestPyPI |
| `make publish` | Publish to PyPI (production) |
| `make clean` | Remove build artifacts |

## Testing Before Publishing

### 1. TestPyPI (Recommended)

Publish to TestPyPI first to catch issues:

```bash
make publish-test
```

Install from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ taocore
```

Test it works:

```python
from taocore import Node, Graph, AttentionMetric
# ... test functionality
```

### 2. Local Installation

Test the built package locally:

```bash
# Build the package
make build

# Install from local dist
pip install dist/taocore-0.1.0-py3-none-any.whl

# Or install from source
pip install dist/taocore-0.1.0.tar.gz
```

### 3. Check Package

Verify package metadata:

```bash
# Check distributions
make check-dist

# View package info
tar -tzf dist/taocore-0.1.0.tar.gz

# Check wheel contents
unzip -l dist/taocore-0.1.0-py3-none-any.whl
```

## Version Numbering

TaoCore follows [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

- **MAJOR** (1.x.x): Breaking changes, incompatible API
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, backward compatible

**Examples**:
- `0.1.0` → `0.1.1`: Bug fix
- `0.1.1` → `0.2.0`: New AttentionMetric feature
- `0.9.0` → `1.0.0`: Stable API, production ready

**Pre-release versions**:
- `0.1.0a1`: Alpha
- `0.1.0b1`: Beta
- `0.1.0rc1`: Release candidate

## Changelog Management

Keep `CHANGELOG.md` updated with all changes:

```markdown
## [Unreleased]
### Added
- New feature X

## [0.1.0] - 2026-01-10
### Added
- Initial release
```

Move unreleased changes to version section before publishing.

## Common Issues

### "File already exists"
- You uploaded this version already
- Increment version number
- Rebuild and republish

### "Invalid credentials"
- Check `~/.pypirc` format
- Ensure token starts with `pypi-`
- Username must be `__token__`

### "README rendering failed"
- Run `make check-dist` for details
- Fix markdown syntax errors
- Test with GitHub's markdown preview

### "Missing metadata"
- Ensure all required fields in `pyproject.toml`
- Run `make check-dist` to validate

## Post-Release

After publishing to PyPI:

1. **Verify on PyPI**:
   - https://pypi.org/project/taocore/
   - Check metadata, README rendering
   - Test installation: `pip install taocore`

2. **Create GitHub Release**:
   - Go to: https://github.com/YOURUSERNAME/taocore/releases
   - Draft new release
   - Choose the version tag
   - Copy CHANGELOG content

3. **Announce**:
   - Update project documentation
   - Announce on relevant channels
   - Update examples if API changed

## Automation (Future)

Consider adding:
- GitHub Actions for automated releases
- Automated version bumping (bump2version)
- Automated CHANGELOG from commits
- Release drafts from git tags

## Security Best Practices

1. **Never commit credentials**:
   - `~/.pypirc` must stay local
   - Use `.gitignore` to prevent accidents

2. **Use scoped tokens**:
   - Create project-specific tokens
   - Not account-wide tokens

3. **Enable 2FA**:
   - On PyPI account
   - On GitHub account

4. **Rotate tokens**:
   - Every 6-12 months
   - After any security incident

5. **Review permissions**:
   - Grant minimal required access
   - Remove unused tokens

## Resources

- **PyPI Help**: https://pypi.org/help/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Docs**: https://twine.readthedocs.io/
- **Semantic Versioning**: https://semver.org/

## Support

For issues with publishing:
- Check `docs/RELEASING.md` for detailed guide
- Run `make check-dist` to diagnose problems
- Review PyPI's packaging documentation
