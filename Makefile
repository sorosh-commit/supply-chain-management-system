.PHONY: install seed test run

install:
	pip install -r requirements.txt

seed:
	python seed.py

test:
	python test_app.py

run:
	python app.py

all: install seed test run
