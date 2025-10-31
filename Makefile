.PHONY: default setup lint lint-fix clean

default: setup

setup: 
	make .venv
	
.venv:
	pip install uv
	python3 -m uv sync


build:
	uv run -m src.cmd.import_paprika
# 	uncomment to cache this step
# 	mkdir -p build

clean:
	rm -rf build

lint:
	uv run ruff check
	uv run mypy .

lint-fix:
	uv run ruff check --fix
	uv run ruff format
	make lint
