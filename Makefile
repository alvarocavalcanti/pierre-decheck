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
	pip install -r requirements.txt || pip3 install -r requirements.txt

test: setup ## Runs all the tests
	python3 -m unittest tests.test_server.ServerTest

build: ## Build all the docker images
	docker-compose build

run: ## Start a local instance of the service
	docker-compose up

up: ## Start a local instance of the service run as a daemon
	docker-compose up -d

down: ## Ensure the docker-compose pieces are all stopped
	docker-compose down

shell-dev: ## Start a shell on the dev sidecar
	docker-compose run --rm dev bash

shell-app: ## Start a shell on the app container
	docker-compose run --rm app bash

clean: down ## Delete local data and ensure containers are stopped
	rm -rf ./.compose-data
