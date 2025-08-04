.PHONY: all mock_server start migrate lint install

all: install start

install:
	uv sync

start:
	uv run uvicorn baseten_backend_take_home.main:app --reload

mock_server:
	uv run uvicorn baseten_backend_take_home.worklet_mock_server:app --reload --port=8001

test_request:
	uv run python baseten_backend_take_home/test_script.py

lint:
	black **/*.py --exclude .venv
	flake8 --exclude .venv
