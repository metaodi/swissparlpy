#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check black code style
python -m black --check --diff swissparlpy examples tests

# Check PEP-8 code style and McCabe complexity
python -m flake8 --count --show-source --statistics .

# run tests with test coverage
python -m pytest tests/
