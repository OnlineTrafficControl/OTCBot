##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

VENV := .venv
SETUP := bin/setup_linux.sh

PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

export PYTHONPATH := $(CURDIR)

.PHONY: setup tests clean-tests

.DEFAULT_GOAL := run

## Installation
setup:
	source $(SETUP)

## Run bot
run:
	$(PYTHON) -m otc_bot

## Tests with coverage
tests:
	$(PYTEST) tests/ --cov=otc_bot --cov-report=term-missing --cov-report=html

## Remove generated test reports
clean-tests:
	rm -rf .coverage htmlcov .pytest_cache
