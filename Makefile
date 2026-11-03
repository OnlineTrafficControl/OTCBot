##################
##              ##
##    OTCBot    ##
## ------------ ##
##################

SHELL   :=  /bin/bash

VENV    :=  .venv
SETUP   :=  bin/setup_linux.sh

PYTHON  :=  $(VENV)/bin/python
PIP     :=  $(VENV)/bin/pip
PYTEST  :=  $(VENV)/bin/pytest

export PYTHONPATH   :=  $(CURDIR)

.PHONY: setup run tests clean-tests clean-logs clean

.DEFAULT_GOAL := run

## Installation
setup:
	source $(SETUP)

## Run bot
run:
	$(PYTHON) otc_bot/main.py

## Tests with coverage
tests:
	$(PYTEST) tests/ --cov=otc_bot --cov-report=term-missing --cov-report=html

## Remove generated test reports
clean-tests:
	rm -rf .coverage htmlcov .pytest_cache

## Remove generated test reports
clean-logs:
	rm -f logs/*

## Global cleaning
clean:  clean-tests clean-logs
