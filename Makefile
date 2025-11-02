.PHONY: default setup lint lint-fix clean test
default: run



ARCH ?=

# Conditionally set the extra flag for uv sync
ifeq ($(ARCH),)
    EXTRAS_FLAG :=
else
    EXTRAS_FLAG := --extra $(ARCH)
endif


.venv:
	UV_TORCH_BACKEND=auto uv sync $(EXTRAS_FLAG)

.build: .venv
	uv run -m src.cmd.paprika_etl
	echo "build placeholder" >> .build

run: .build
	uv run -m src.cmd.start_app

clean:
	rm -rf resources/chroma
	rm -f resources/paprika/.*.json .build

lint:
	uv run ruff check
	uv run mypy --cache-fine-grained src

lint-fix:
	uv run ruff check --fix
	uv run ruff format
	make lint

test:
	uv run pytest .
