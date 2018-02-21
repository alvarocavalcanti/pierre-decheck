SHELL := /bin/bash

create-env:
	mkdir -p env
	virtualenv env
activate-env:
	source env/bin/activate
flake8:
	flake8 .
setup: activate-env
	pip install -r requirements.txt
test: setup
	python -m unittest tests.py
deploy:
	git push heroku master
