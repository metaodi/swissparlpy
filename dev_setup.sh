#!/bin/bash

[ ! -d pyenv ] && python -m venv pyenv
source pyenv/bin/activate

pip install --upgrade pip
flit install -s
