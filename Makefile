install:
	poetry install --no-dev

test:
	py.test fa_search_bot/tests

run:
	python3 run.py
