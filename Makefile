.PHONY: install test lint format clean dev demo tox tox-all coverage build check-dist publish publish-test docker-build docker-demo docker-test docker-dev docker-shell docker-clean

install:
	uv sync

dev:
	uv sync --all-extras

test:
	uv run pytest tests/ -v

tox:
	uv run tox -e py39

tox-all:
	uv run tox

tox-lint:
	uv run tox -e lint

tox-type:
	uv run tox -e type

coverage:
	uv run pytest tests/ --cov=src/taocore --cov-report=term-missing --cov-report=html

demo:
	uv run python examples/demo.py

lint:
	uv run ruff check src/

format:
	uv run ruff format src/

typecheck:
	uv run mypy src/

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf .tox
	rm -rf dist/
	rm -rf build/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	@echo "Building package..."
	uv build
	@echo "Build complete! Distributions:"
	@ls -lh dist/

check-dist:
	@echo "Checking package distributions..."
	uv run twine check dist/*

publish-test:
	@echo "Publishing to TestPyPI..."
	@echo "Make sure you have a TestPyPI account and token configured"
	uv run twine upload --repository testpypi dist/*

publish:
	@echo "⚠️  WARNING: This will publish to PyPI!"
	@echo "Make sure you have:"
	@echo "  1. Updated the version in pyproject.toml"
	@echo "  2. Updated CHANGELOG"
	@echo "  3. Run all tests (make test && make tox-all)"
	@echo "  4. Built fresh distributions (make clean && make build)"
	@echo ""
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		uv run twine upload dist/*; \
	else \
		echo "Cancelled."; \
	fi

rfc1: install
	@echo "TaoCore RFC-1 implementation ready"
	@echo "Run 'make test' to verify"

# Docker targets
docker-build:
	docker build -t taocore:latest .

docker-build-dev:
	docker build -f Dockerfile.dev -t taocore:dev .

docker-demo:
	docker run --rm taocore:latest

docker-test:
	docker compose run --rm taocore-test

docker-dev:
	docker compose run --rm taocore-dev

docker-shell:
	docker run --rm -it -v $(PWD)/src:/app/src taocore:latest /bin/bash

docker-clean:
	docker compose down -v
	docker rmi taocore:latest taocore:dev 2>/dev/null || true

# Docker Compose shortcuts
dc-up:
	docker compose up taocore

dc-test:
	docker compose up taocore-test

dc-dev:
	docker compose up -d taocore-dev
	docker compose exec taocore-dev /bin/bash

dc-down:
	docker compose down
