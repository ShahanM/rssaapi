#!/usr/bin/bash

uv run uvicorn rssa_api.main:app --reload --reload-exclude "tests"