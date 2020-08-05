install:
	pip install -r requirements.txt

test:
	py.test fa_search_bot/tests

run:
	python3 run.py
