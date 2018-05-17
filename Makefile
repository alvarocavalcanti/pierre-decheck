SHELL := /bin/bash

create-env:
	mkdir -p env
	virtualenv env
activate-env:
	source env/bin/activate
flake8:
	flake8 .
setup: activate-env
	pip install -r requirements.txt || pip3 install -r requirements
test: setup
	python3 -m unittest tests.test_server.ServerTest
deploy:
	git push heroku master
