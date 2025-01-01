#!/bin/bash

set -eu

if ! command -v poetry &> /dev/null
then
    echo "Poetry is not installed. Please install Poetry (https://python-poetry.org/docs/#installation)"
    exit 1
fi

poetry install

poetry run python -m proxy_scraper_checker