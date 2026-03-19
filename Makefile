.PHONY: dev install test lint format clean example reviewer

# Setup development environment
dev:
	python -m venv .venv
	.venv/bin/pip install -e ".[dev,all]"

# Install package
install:
	pip install -e ".[all]"

# Run tests
test:
	pytest tests/ -v

# Run linter
lint:
	ruff check src/ tests/
	mypy src/xybench/

# Format code
format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# Run basic example
example:
	python examples/basic_review.py

# Run Streamlit reviewer UI
reviewer:
	streamlit run examples/reviewer_app.py

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
