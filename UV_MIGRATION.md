# Migration Guide: From Flit to UV

This document describes the migration from `flit` to `uv` for package management and PyPI publishing.

## What Changed?

### Build System
- **Before**: Used `flit_core` as the build backend
- **After**: Uses `hatchling` as the build backend (fully compatible with `uv`)

### Package Management
- **Before**: Used `flit` for development installation and publishing
- **After**: Uses `uv` for all package operations

### Version Management
- **Before**: Version was dynamically read from `swissparlpy/__init__.py` by flit
- **After**: Version is still read from `swissparlpy/__init__.py`, now via hatchling configuration in `pyproject.toml`

## For Package Users

If you just install the package via `pip install swissparlpy`, nothing changes. The package is still published to PyPI and installable the same way.

## For Contributors

### Installing Development Dependencies

**Old way:**
```bash
pip install flit
flit install -s
```

**New way (Option 1 - using uv):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e ".[dev,test]"
```

**New way (Option 2 - using the setup script):**
```bash
./dev_setup.sh
```

**New way (Option 3 - using pip directly):**
```bash
pip install -e ".[dev,test]"
```

### Running Tests

No changes needed:
```bash
./validate.sh
```

Or run components individually:
```bash
python -m black --check --diff swissparlpy examples tests
python -m flake8 --count --show-source --statistics .
python -m pytest tests/
```

## For Maintainers

### Creating a Release

**Version Updates:**
- **Before**: Update version in `swissparlpy/__init__.py`
- **After**: Update version in `pyproject.toml` (also update `__init__.py` to keep them in sync)

**Publishing to PyPI:**
- **Before**: Used `flit publish` with username/password
- **After**: Uses `uv publish` with API token

The GitHub Actions workflow has been updated to use `uv` automatically. You need to:
1. Create a PyPI API token at https://pypi.org/manage/account/token/
2. Add it as a GitHub secret named `PYPI_API_TOKEN` (note: the old `PYPI_USERNAME` and `PYPI_PASSWORD` secrets are no longer used)

### Manual Publishing (if needed)

**Old way:**
```bash
flit publish
```

**New way:**
```bash
uv build
uv publish --token <your-pypi-token>
```

Or set the token as an environment variable:
```bash
export UV_PUBLISH_TOKEN=<your-pypi-token>
uv build
uv publish
```

## Benefits of UV

1. **Faster**: UV is significantly faster than pip and other Python package managers
2. **Modern**: Built in Rust with modern dependency resolution
3. **All-in-one**: Handles virtual environments, package installation, and publishing
4. **Compatible**: Works with standard Python packaging (pyproject.toml)
5. **Active Development**: Maintained by Astral (creators of ruff)

## Compatibility

The migration maintains full backward compatibility:
- The package structure hasn't changed
- Installation via pip still works
- The API is unchanged
- Tests pass without modifications

## Troubleshooting

### UV not found after installation
Make sure to reload your shell or run:
```bash
source $HOME/.cargo/env
```

### Using pip instead of uv
If you prefer not to use `uv`, you can still use `pip` directly:
```bash
pip install -e ".[dev,test]"
```

The package is fully compatible with standard pip installation.

## References

- [UV Documentation](https://github.com/astral-sh/uv)
- [Hatchling Documentation](https://hatch.pypa.io/latest/)
- [Python Packaging Guide](https://packaging.python.org/)
