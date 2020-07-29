install:
	pip install -r requirements.txt

test:
	py.test fa_search_bot/tests

run:
	python3 fa_search_bot/run.py
