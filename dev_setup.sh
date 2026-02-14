#!/bin/bash

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create virtual environment using uv
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install the project in development mode with all dependencies
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
