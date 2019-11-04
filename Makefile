SHELL := /bin/bash

help: ## Displays help
	@awk -F ':|##' \
		'/^[^\t].+?:.*?##/ {\
			printf "\033[36m%-30s\033[0m %s\n", $$1, $$NF \
}' $(MAKEFILE_LIST) | sort

create-env: ## Creates the virtual environment folder
	mkdir -p env
	virtualenv env
flake8: ## Linting/static checks
	flake8 .
setup: ## Installs the dependencies
	pip install -r requirements.txt || pip3 install -r requirements
test: setup ## Runs all the tests
	python3 -m unittest tests.test_server.ServerTest
