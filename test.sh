#!/bin/sh

set -e

flake8 --exclude venv
pytest -vs .
