.PHONY: default setup lint lint-fix clean

default: run

.venv:
	UV_TORCH_BACKEND=auto uv sync

.build: .venv
	uv run -m src.cmd.paprika_etl
	echo "build placeholder" >> .build

run: .build
	uv run -m src.cmd.start_app

clean:
	rm -rf resources/chroma

lint:
	uv run ruff check
	uv run mypy .

lint-fix:
	uv run ruff check --fix
	uv run ruff format
	make lint
