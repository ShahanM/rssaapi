#!/usr/bin/bash

uvicorn rssa_api.main:app --reload --reload-exclude "tests"
