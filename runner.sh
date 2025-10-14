#!/usr/bin/bash

# Ensure we are in the script's directory first, regardless of where it's called from
cd "$(dirname "$0")" 

export PYTHONPATH=./src:$PYTHONPATH
# Execute uvicorn from the root, pointing it to src.main:app
poetry run uvicorn src.main:app --reload