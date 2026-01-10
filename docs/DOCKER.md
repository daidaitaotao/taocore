# Docker Guide for TaoCore

This guide explains how to run TaoCore in Docker containers.

## Prerequisites

- Docker Desktop installed and running
- macOS: Open Docker.app from Applications
- Verify with: `docker --version`

## Quick Start

### Run the Demo

```bash
# Build and run the demo
make docker-build
make docker-demo
```

Or using docker-compose:

```bash
docker compose up taocore
```

### Run Tests

```bash
# Run tests in container
make docker-test
```

Or:

```bash
docker compose up taocore-test
```

## Available Docker Commands

### Basic Commands

| Command | Description |
|---------|-------------|
| `make docker-build` | Build production image |
| `make docker-demo` | Run demo script |
| `make docker-test` | Run test suite |
| `make docker-shell` | Interactive shell with source mounted |
| `make docker-clean` | Remove containers and images |

### Development Commands

| Command | Description |
|---------|-------------|
| `make docker-build-dev` | Build dev image with all dependencies |
| `make docker-dev` | Run development container |
| `dc-dev` | Start interactive dev environment |

### Docker Compose Commands

| Command | Description |
|---------|-------------|
| `dc-up` | Start TaoCore demo service |
| `dc-test` | Run tests via compose |
| `dc-dev` | Interactive development shell |
| `dc-down` | Stop all services |

## Docker Images

### Production Image (`Dockerfile`)

Optimized multi-stage build:
- Base: Python 3.9.25-slim
- Includes: Runtime dependencies only
- Size: ~200MB (optimized)
- Default command: Run demo script

```bash
docker build -t taocore:latest .
docker run --rm taocore:latest
```

### Development Image (`Dockerfile.dev`)

Full development environment:
- Base: Python 3.9.25-slim
- Includes: Dev dependencies (pytest, ruff, mypy)
- Tools: git, make
- Default command: bash shell

```bash
docker build -f Dockerfile.dev -t taocore:dev .
docker run --rm -it taocore:dev
```

## Development Workflow

### Interactive Development

Start a development container with your source code mounted:

```bash
make docker-dev
```

Inside the container:
```bash
# Run tests
pytest tests/ -v

# Lint code
ruff check src/

# Format code
ruff format src/

# Type check
mypy src/

# Run demo
python examples/demo.py
```

### Volume Mounts

Development containers mount source code as read-only:
- `./src:/app/src:ro`
- `./tests:/app/tests:ro`
- `./examples:/app/examples:ro`

Edit files on your host machine, changes reflect in container immediately.

### Shell Access

Get a shell in the running container:

```bash
# Using production image
make docker-shell

# Using development image
make docker-dev
```

## Docker Compose Services

The `docker-compose.yml` defines three services:

### 1. `taocore` (Production)

Runs the demo script:
```bash
docker compose up taocore
```

### 2. `taocore-test`

Runs the test suite:
```bash
docker compose up taocore-test
```

### 3. `taocore-dev`

Interactive development environment:
```bash
docker compose run --rm taocore-dev
```

## Common Tasks

### Build and Test Workflow

```bash
# Build the image
make docker-build

# Run demo to verify
make docker-demo

# Run tests
make docker-test

# Clean up
make docker-clean
```

### Continuous Integration

The Docker setup is CI/CD ready:

```bash
# CI pipeline example
docker build -t taocore:latest .
docker run --rm taocore:latest pytest tests/ -v
```

### Custom Python Commands

Run any Python script in the container:

```bash
docker run --rm -v $(pwd)/examples:/app/examples taocore:latest \
  python examples/demo.py
```

### Install Additional Packages

For experimentation, install packages at runtime:

```bash
docker run --rm -it taocore:dev /bin/bash
# Inside container:
uv add <package-name>
```

## Image Optimization

The production Dockerfile uses multi-stage builds:

1. **Builder stage**: Installs dependencies with uv
2. **Final stage**: Copies only virtual environment and source code

Benefits:
- Smaller final image size
- No build tools in production image
- Faster deployment

## Troubleshooting

### Docker Not Found

If you get `command not found: docker`:
1. Open Docker Desktop from Applications
2. Wait for it to start (whale icon in menu bar)
3. Verify: `docker --version`

### Build Fails

If build fails on dependency resolution:
```bash
# Clean uv cache
make clean

# Rebuild without cache
docker build --no-cache -t taocore:latest .
```

### Container Won't Start

Check logs:
```bash
docker compose logs taocore
```

### Permission Issues

On Linux, you may need to run with sudo or add user to docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

## Best Practices

1. **Use docker-compose** for multi-container setups
2. **Mount volumes** for development, copy for production
3. **Use .dockerignore** to exclude unnecessary files
4. **Tag images** with version numbers for releases
5. **Multi-stage builds** to minimize image size
6. **Non-root user** for production deployments (future enhancement)

## Environment Variables

Set environment variables in docker-compose.yml or via -e flag:

```bash
docker run --rm -e PYTHONUNBUFFERED=1 taocore:latest
```

Available variables:
- `PYTHONUNBUFFERED=1` - Force unbuffered output
- `PYTHONPATH=/app/src` - Python module search path

## Security Notes

- Production image runs as root (consider adding non-root user)
- No secrets in image (use environment variables or Docker secrets)
- Regular updates for base image security patches
- Scan images: `docker scan taocore:latest` (if Docker Scout enabled)

## Next Steps

- Add health checks to Dockerfile
- Implement non-root user for production
- Add Docker image to CI/CD pipeline
- Publish to container registry (Docker Hub, GHCR)
- Add docker-compose.prod.yml for production deployments
