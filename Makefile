.PHONY: black style validate install serve

install:
	uv sync

black:
	uv run isort virtupy
	uv run black virtupy --line-length 100

validate:
	uv run isort virtupy
	uv run black virtupy --line-length 100
	uv run flake8 virtupy
	uv run mypy virtupy --explicit-package-bases
	npx html-validate@8 gui/*.html
	npx eslint@9 gui/
