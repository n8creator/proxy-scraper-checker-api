DIRECTORIES = proxy_scraper_checker/ api/

# Setup
install:
	@poetry install

# Format & Lint Code via Ruff
format:
	@poetry run ruff check $(DIRECTORIES) --select I --fix
	@poetry run ruff format $(DIRECTORIES)

lint:
	@poetry run ruff check $(DIRECTORIES) --fix

# Run FastAPI server
run:
	@poetry run python -m api.main

# System commands for Makefile
MAKEFLAGS += --no-print-directory

# System Makefile commands
.PHONY: install format lint run