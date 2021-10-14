#!/bin/bash

[ ! -d pyenv ] && python -m venv pyenv
source pyenv/bin/activate

pip install --upgrade pip
pip install flit
flit install -s
