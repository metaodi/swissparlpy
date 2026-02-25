#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check black code style
uv run black --check --diff swissparlpy examples tests

# Check PEP-8 code style and McCabe complexity
uv run flake8 --count --show-source --statistics swissparlpy

# Run mypy type checks
uv run mypy swissparlpy

# run tests with test coverage
uv run pytest tests/
