DIRECTORIES = proxy_scraper_checker/

# Setup
install:
	@poetry install

# Format & Lint Code via Ruff
format:
	@poetry run ruff check $(DIRECTORIES) --select I --fix
	@poetry run ruff format $(DIRECTORIES)

lint:
	@poetry run ruff check $(DIRECTORIES) --fix

# System commands for Makefile
MAKEFLAGS += --no-print-directory

# System Makefile commands
.PHONY: install format lint