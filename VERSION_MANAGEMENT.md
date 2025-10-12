# Version Management

CLIppy uses a centralized version management system with the version stored in two places:

1. `src/clippy/__version__.py` - Python package version
2. `pyproject.toml` - Build system version

Both files are kept in sync automatically using the Makefile commands.

## Version File Structure

### src/clippy/__version__.py
```python
"""Version information for CLIppy."""

__version__ = "0.1.0"
```

### src/clippy/__init__.py
```python
"""CLIppy - A CLI coding agent."""

from .__version__ import __version__

__all__ = ["__version__"]
```

This allows importing the version in Python:
```python
from clippy import __version__
print(__version__)  # 0.1.0
```

## Bumping Versions

Use the Makefile commands to bump versions:

### Patch Version (0.1.0 → 0.1.1)
```bash
make bump-patch
```
Use for bug fixes and small changes.

### Minor Version (0.1.0 → 0.2.0)
```bash
make bump-minor
```
Use for new features that are backward compatible.

### Major Version (0.1.0 → 1.0.0)
```bash
make bump-major
```
Use for breaking changes or major releases.

## Version Bump Process

Each bump command:
1. Reads the current version from `pyproject.toml`
2. Calculates the new version based on the bump type
3. Updates `pyproject.toml` with the new version
4. Updates `src/clippy/__version__.py` with the new version
5. Prints confirmation message

## Custom Python Interpreter

The Makefile uses `python3` by default, but you can override it:

```bash
# Use a specific Python version
make PYTHON=python3.12 bump-patch

# Use python (if available)
make PYTHON=python bump-minor
```

## Manual Version Updates

If you need to manually update the version, make sure to update both files:

1. Edit `src/clippy/__version__.py`:
   ```python
   __version__ = "0.2.0"
   ```

2. Edit `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

## Release Workflow

1. Make your changes
2. Bump the version: `make bump-patch` (or minor/major)
3. Update CHANGELOG.md (when we add it)
4. Commit changes: `git commit -am "chore: bump version to X.Y.Z"`
5. Create a tag: `git tag vX.Y.Z`
6. Push: `git push origin main --tags`
7. Build and publish: `make build && make publish`

## Semantic Versioning

CLIppy follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0) - Incompatible API changes
- **MINOR** (0.X.0) - New functionality, backward compatible
- **PATCH** (0.0.X) - Bug fixes, backward compatible

### Examples

- Bug fix: `0.1.0` → `0.1.1` (use `make bump-patch`)
- New feature: `0.1.1` → `0.2.0` (use `make bump-minor`)
- Breaking change: `0.2.0` → `1.0.0` (use `make bump-major`)
