# BrowserPilot — common tasks
PYTHON ?= python3
ARGS ?=

.PHONY: install test benchmark

install:  ## Install Python deps + Chromium for Ghost Mode
	$(PYTHON) -m pip install -r requirements.txt
	patchright install chromium

test:  ## Run the test suite
	$(PYTHON) -m pytest tests/ -q

benchmark:  ## Reproduce the stealth benchmark (artifacts -> outputs/benchmark/)
	$(PYTHON) -m backend.benchmark $(ARGS)
