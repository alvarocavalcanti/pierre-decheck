# Contributing

## Architecture

Pierre is built primarly using [Flask](https://www.fullstackpython.com/flask.html), which can be seen on the [`servcer.py`](../server.py) file. The file servers as its standard entry point, but there's also support for [serverless](https://serverless.com/) via the [`serverless.yml`](../serverless.yml) file.

The main implementation resides in [`pierre.py`](../lib/pierre.py).

## Workflow

If you are interested in contributing, please follow these guidelines:

* Have a look at the [open issues](issues/) and make sure there's an issue for the work you want to do. Create one if there isn't
* Fork the repository
* Create a branch for your work, and name it appropriately: try to be descriptive, avoid acronyms and abbreviations. If possible use one of the following templates: `ISSUE-25-details-endpoint-for-external-dependencies` or just `ISSUE-25`
* Keep test coverage as high as possible, meaning:
  * If the work adds new requirements, write tests for them and make sure the existing ones do not break
  * If the work is a refactoring, make sure the existing tests do not break
  * To run the tests locally: `make test`
* Mind the [Code Style](code_style.md)
* Push your changes to your fork and then [create a new pull request](compare/)
  * Keep an eye on Pierre's [Continuos Integration](https://circleci.com/gh/alvarocavalcanti/pierre-decheck) panel, if it fails, fix it

## Development Environment

* As a Python project, Pierre's makes use of the widely used standard of `virtual-env`
* There is a [`Makefile`](../Makefile) with several helpful targets, have a look at them with `make help`
