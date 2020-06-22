# Contributing

## Architecture

Pierre is built primarly using [Flask](https://www.fullstackpython.com/flask.html), which can be seen on the [`server.py`](../server.py) file. The file servers as its standard entry point, but there's also support for [serverless](https://serverless.com/) via the [`serverless.yml`](../serverless.yml) file.

The main implementation resides in [`pierre.py`](../lib/pierre.py).

## Workflow

If you are interested in contributing, please follow these guidelines:

* Have a look at the [open issues](https://github.com/alvarocavalcanti/pierre-decheck/issues) and make sure there's an issue for the work you want to do. Create one if there isn't
* Assign yourself to that issue
* Fork the repository
* Create a branch for your work, and name it appropriately: try to be descriptive, avoid acronyms and abbreviations. If possible use one of the following templates: `ISSUE-25-details-endpoint-for-external-dependencies` or just `ISSUE-25`
* Keep test coverage as high as possible, meaning:
  * If the work adds new requirements, write tests for them and make sure the existing ones do not break
  * If the work is a refactoring, make sure the existing tests do not break
  * To run the tests locally: `make test`
* Mind the [Code Style](code_style.md)
* **Don't** force push! Fix your merge conflicts and respect commit history. Also, be mindful of cleaning up/squashing smaller commits
* Push your changes to your fork and then [create a new pull request](https://github.com/alvarocavalcanti/pierre-decheck/compare)
  * Keep an eye on Pierre's [Continuous Integration](https://circleci.com/gh/alvarocavalcanti/pierre-decheck) panel, if it fails, fix it

## Development Environment

* As a Python project, Pierre's makes use of the widely used standard of `virtual-env`
* There is a [`Makefile`](../Makefile) with several helpful targets, have a look at them with `make help`

## Recommended Development Environment - PyCharm Professional Edition with Remote Interpreter

Pierre provides a Docker "sidecar" that exposes a Python interpreter via SSH, and thus can be used as a remote interpreter by PyCharm. This approach is an improvement on the "virtualenv" pattern, in which instead of having to create a local environment, the developer can rely on the sidecar's environment.

Here's the steps for setting it up:

1. Build the images: `make build`
1. Bring the containers up: `make up` - they'l be executed in the background
1. In PyCharm > Preferences (CMD + ,) > Project Settings > Project Interpreter
1. Click on the gear icon next to the "Project Interpreter" dropdown > Add
1. Select "SSH Interpreter" > Host: localhost, Port: 9922, Username: root > Password: password > Interpreter: /usr/local/bin/python, Sync folders: Preoject Root -> /pierre-decheck, Disable "Automatically upload..."

### Perks

1. Seamless class discovery and navigation
1. Import suggestions and organize imports
1. Running tests directly from the IDE
