.PHONY: install venv build typecheck test lint format format-check deptry bandit audit pre-commit pre-push rulesync clean bootstrap
install:
	uv sync 
venv:
	uv venv
test:
	uv run pytest  --cov=rmoji --cov-report=term-missing
build:
	uv build
typecheck:
	uv run mypy rmoji
lint:
	uv run ruff check rmoji 
format:
	uv run ruff format rmoji 
format-check:
	uv run ruff format --check rmoji 
deptry:
	uv run deptry rmoji
audit:
	uv run pip-audit
pre-commit:
	uv run pre-commit run --all-files
pre-push: lint typecheck test bandit audit deptry
rulesync:
	npx rulesync generate
clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage