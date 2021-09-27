#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check PEP-8 code style and McCabe complexity
flake8 . --count --show-source --statistics 

# run tests with test coverage
pytest tests/
