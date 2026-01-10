# Release Guide

This guide explains how to build and publish TaoCore to PyPI.

## Prerequisites

### 1. Install Development Dependencies

```bash
make dev
```

This installs all required tools including `twine` and `build`.

### 2. Set Up PyPI Accounts

You'll need accounts on:
- **TestPyPI** (https://test.pypi.org): For testing releases
- **PyPI** (https://pypi.org): For production releases

### 3. Configure API Tokens

#### Create API Tokens

1. **TestPyPI**:
   - Go to https://test.pypi.org/manage/account/token/
   - Create a new API token
   - Scope: "Entire account" (for first release) or "taocore" project

2. **PyPI**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Scope: "Entire account" (for first release) or "taocore" project

#### Configure Tokens

Create/edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

**Important**: Keep these tokens secure! Add `~/.pypirc` to your global `.gitignore`.

## Release Process

### Step 1: Pre-Release Checklist

Before creating a release:

- [ ] All tests pass: `make test`
- [ ] All tox environments pass: `make tox-all`
- [ ] Code is formatted: `make format`
- [ ] Linting passes: `make lint`
- [ ] Type checking passes: `make typecheck`
- [ ] Coverage is acceptable: `make coverage` (currently 94%)
- [ ] Documentation is up-to-date
- [ ] Version number is updated in `pyproject.toml`
- [ ] CHANGELOG.md is updated with release notes
- [ ] All changes are committed to git

### Step 2: Update Version Number

Edit `pyproject.toml`:

```toml
[project]
name = "taocore"
version = "0.1.0"  # Update this version
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Add functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:
- `0.1.0` → `0.1.1` (bug fix)
- `0.1.1` → `0.2.0` (new features)
- `0.2.0` → `1.0.0` (stable release)

### Step 3: Update CHANGELOG

Edit `CHANGELOG.md`:

```markdown
## [0.1.1] - 2026-01-15

### Added
- New feature X

### Fixed
- Bug Y

### Changed
- Improvement Z
```

Move items from `[Unreleased]` to the new version section.

### Step 4: Commit Version Changes

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release v0.1.1"
git tag -a v0.1.1 -m "Version 0.1.1"
```

### Step 5: Build the Package

Clean previous builds and create fresh distributions:

```bash
# Clean old builds
make clean
rm -rf dist/

# Build fresh distributions
make build
```

This creates:
- `dist/taocore-X.Y.Z.tar.gz` (source distribution)
- `dist/taocore-X.Y.Z-py3-none-any.whl` (wheel distribution)

### Step 6: Check the Build

Verify the package is properly configured:

```bash
make check-dist
```

This runs `twine check` to validate:
- README renders correctly on PyPI
- Metadata is complete
- No common packaging issues

### Step 7: Test on TestPyPI (Optional but Recommended)

Publish to TestPyPI first to verify everything works:

```bash
make publish-test
```

Then install from TestPyPI to test:

```bash
pip install --index-url https://test.pypi.org/simple/ taocore
```

Test that it works:

```python
from taocore import Node, Graph
# ... test basic functionality
```

### Step 8: Publish to PyPI

Once everything is verified, publish to production PyPI:

```bash
make publish
```

This command:
1. Shows a confirmation prompt with checklist
2. Uploads to PyPI using `twine`
3. Package becomes available at https://pypi.org/project/taocore/

**⚠️ Warning**: You cannot delete or re-upload the same version to PyPI. Make sure everything is correct before publishing!

### Step 9: Push to GitHub

```bash
git push origin main
git push origin v0.1.1  # Push the tag
```

### Step 10: Create GitHub Release

1. Go to https://github.com/yourusername/taocore/releases
2. Click "Draft a new release"
3. Choose the tag you just pushed (v0.1.1)
4. Title: "TaoCore v0.1.1"
5. Copy release notes from CHANGELOG.md
6. Publish release

## Quick Reference

```bash
# Full release workflow
make clean                    # Clean old builds
make test && make tox-all    # Verify all tests pass
make build                   # Build distributions
make check-dist              # Validate package
make publish-test            # Test on TestPyPI (optional)
make publish                 # Publish to PyPI
```

## Troubleshooting

### "File already exists" Error

You've already uploaded this version to PyPI. You must:
1. Increment the version number in `pyproject.toml`
2. Rebuild: `make clean && make build`
3. Publish again

### "Invalid credentials" Error

Check your `~/.pypirc` file:
- Tokens must start with `pypi-`
- Username must be `__token__`
- No extra spaces or quotes

### "README rendering failed"

Your README.md has formatting issues:
- Run `make check-dist` to see specific errors
- Common issues: broken links, invalid markdown syntax
- Test locally with a markdown preview tool

### "Missing required metadata"

Ensure `pyproject.toml` has all required fields:
- `name`, `version`, `description`
- `readme`, `requires-python`
- `license`, `authors`

## Version History

Track all published versions:

```bash
# View all published versions
pip index versions taocore

# View package info
pip show taocore
```

## Rolling Back (Emergency)

If you published a broken release:

1. **Cannot delete from PyPI** - versions are permanent
2. **Quick fix**:
   ```bash
   # Increment patch version
   # e.g., 0.1.1 → 0.1.2
   # Fix the issue
   # Publish new version
   ```
3. **Yank the release** (makes it hard to install):
   - Go to https://pypi.org/project/taocore/
   - Manage project → Releases → Yank
   - Only do this for seriously broken releases

## Automation (Future)

Consider setting up:
- GitHub Actions for automated releases
- Automated version bumping
- Automatic CHANGELOG generation
- Release notes from git commits

## Security

- **Never commit** API tokens to git
- Rotate tokens periodically
- Use scoped tokens (project-specific, not account-wide)
- Enable 2FA on PyPI accounts
