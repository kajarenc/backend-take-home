.PHONY: all mock_server start migrate lint install

all: install start

install:
	poetry install

start:
	poetry run uvicorn baseten_backend_take_home.main:app --reload

mock_server:
	poetry run uvicorn baseten_backend_take_home.worklet_mock_server:app --reload --port=8001

test_request:
	poetry run python baseten_backend_take_home/test_script.py

lint:
	poetry run black **/*.py --exclude .venv
	poetry run flake8 --exclude .venv
