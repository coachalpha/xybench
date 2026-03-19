# Contributing to xybench

Thanks for your interest in contributing! This guide will help you get started.

## Development setup

```bash
# Clone the repo
git clone https://github.com/xybench/xybench.git
cd xybench

# Create a virtual environment and install dev dependencies
make dev

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,all]"
```

## Running tests

```bash
make test
# or
pytest tests/ -v
```

## Code style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check for issues
make lint

# Auto-fix formatting
make format
```

Key conventions:
- Type hints on all public functions
- Docstrings on all public modules, classes, and functions
- No external dependencies in core SDK (optional extras are fine)

## Making changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Add or update tests as needed
4. Run `make test` and `make lint` to verify
5. Submit a pull request

## Pull request guidelines

- Keep PRs focused — one feature or fix per PR
- Write a clear description of what changed and why
- Ensure all tests pass and no lint errors
- Update `CHANGELOG.md` under the `[Unreleased]` section

## Reporting issues

- Use [GitHub Issues](https://github.com/xybench/xybench/issues) to report bugs or request features
- Include steps to reproduce for bug reports
- Check existing issues before opening a new one

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
