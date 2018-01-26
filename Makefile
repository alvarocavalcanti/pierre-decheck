create-env:
	mkdir -p env
	virtualenv env
activate-env:
	source env/bin/activate
flake8:
	flake8 .