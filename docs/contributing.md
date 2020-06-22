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

## Recommended Development Environment - Docker sidecar

Pierre's `docker-compose.yaml` specifies a "sidecar" container that can be used by IDEs to execute the remote interpreter, and that provides some perks, such as:

1. No hassle dev environment configuration
1. Standardized dev environment across the team
1. Seamless class discovery and navigation
1. Import suggestions and organize imports
1. Running tests directly from the IDE

The sidecar is exposed via SSH and this pattern can be seen as an improvement of the virtual environment pattern (implemented by tools such as `virtualenv` and `pyenv`).

Before trying to configure your IDE:

1. Build the images: `make build`
1. Bring the containers up: `make up` - they'l be executed in the background

### PyCharm Professional Edition

1. In PyCharm > Preferences (CMD + ,) > Project Settings > Project Interpreter
1. Click on the gear icon next to the "Project Interpreter" dropdown > Add
1. Select "SSH Interpreter" > Host: localhost, Port: 9922, Username: root > Password: password > Interpreter: /usr/local/bin/python, Sync folders: Preoject Root -> /pierre-decheck, Disable "Automatically upload..."

Expected results:

1. Code completion works
1. Code navigation works
1. Organize imports works
1. Import suggestions/discovery works
1. Tests (either classes or methods) can be executed by placing the cursor on them and then using `Ctrl+Shift+R`

### Visual Studio Code

1. Install the [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) extension
1. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
1. Open the Command Pallette and type `Remote-Containers`, then select the `Attach to Running Container...` and selecet `pierre-decheck_dev_1` (or similar)
1. VS Code will restart and reload
1. On the `Explorer` sidebar, click the `open a folder` button and then enter `/pierre-decheck` (this will be loaded from the remote container)
1. On the `Extensions` sidebar, select the `Python` extension and install it on the container
1. When prompet on which interppreter to use, select `/usr/local/bin/python`
1. Open the Command Pallette and type `Python: Configure Tests`, then select `unittest` framework

Expected results:

1. Code completion works
1. Code navigation works
1. Organize imports works
1. Import suggestions/discovery works
1. Tests (either classes or methods) will have a new line above their definitions, containing two actions: `Run Test | Debug Test`, and will be executed upon clicking on them
