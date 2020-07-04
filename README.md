# Pierre DeCheck - A Dependent Pull-Request Checker

[![CircleCI](https://circleci.com/gh/alvarocavalcanti/pierre-decheck/tree/master.svg?style=svg)](https://circleci.com/gh/alvarocavalcanti/pierre-decheck/tree/master)

## Key Features

It checks for dependant pull requests, both same-repo and external, which should be defined by keywords on either pull request's body or comments:

* Same repo: `Depends on #1`
* External:
  * `Depends on alvarocavalcanti/pierre-decheck#1`
  * `Depends on https://github.com/alvarocavalcanti/pierre-decheck/pull/1`

Pierre will perform checks only upon PR creation and Comment Activity (added/removed). In every case it will fetch all the PR's bodies (the PR body itself and from all its comments), extract the dependencies and perform the checks. Thus, it **does not** observe the dependencies themselves and re-run the checks if their status change.

For now, the best way of re-checkind the dependencies statuses is to add a new comment. I suggest `pierre re-check`. :smiley:

## Installation

1. Checkout/download this repo
1. Publish the app wherever suits you the best (it has both [Heroku](http://www.heroku.com) and [AWS Lambda](https://aws.amazon.com/lambda/) configuration in place) and take note of the app's URL
1. Go to the repository you want to set it up, then go to **Settings > Webhooks > Add Webhook**
1. Under "Payload URL" enter `<YOUR_APP_URL>/webhook`
1. Under "Content type" select "application/json"
1. Under "Which events would you like to trigger this webhook?" select "Let me select individual events." and then: "Commit comments", "Issue comments", "Issues", "Pull requests" and "Pull request review comments"
1. Finally, make sure "Active" is selected and then create the webhook
1. [Create an access token for your repo](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/) and grant it with either `repo:status` for _Public_ repos or `repo (Full control of private repositories)` for _Private_ repos.
1. Add the token as an environment variable for you app, labeled `GITHUB_TOKEN`

## Usage

1. Create a pull request on the repository that has *pierre* set up
1. Add the keywords `Depends on #` (for same-repo) or "Depends on `owner/repo#`" (for external) followed by an issue/pull request number, `Depends on #2` or `Depends on owner/repo#2`, to the pull request description, or later, as a comment. (Alternatively, `Depends on <GITHUB_URL_OF_ISSUE_OR_PR>` style can be used) ![Pull Request Checks Example](docs/images/pull_request_keywords.png)
1. Every time a comment is added or deleted, *pierre* will check the dependencies and update the "Checks" section: ![Pull Request Checks Example](docs/images/pull_request_checks.png)

### Optional feature: Depending on a Released PR

Usually when one has external dependencies (other repos) these dependencies requires not only a PR to be merged, but also released. To that extent, _Pierre_ offers an optional configuration: by setting the environment variable `RELEASE_LABEL` to any given value, _Pierre_ will then consider any dependency as met only if its state is `closed` and if it also has the proper label. On the screenshot below it's possible to see how it looks like when the dependency is closed but does not have the release label:

![Pull Request Checks Exemple](docs/images/pull_request_checks_release_label.png)

## Contributing

[Contributing document](docs/contributing.md).

## Code Style

[Code style document](docs/code_style.md).

## Recommended IDEs

1. [PyCharm](https://www.jetbrains.com/pycharm/) - Community edition is free and decent, Professional edition is awesome
1. [VisualStudio Code](https://code.visualstudio.com/) - Completely free, large amount of extensions and great community support

## References

1. [Github Repo Statuses](https://developer.github.com/v3/repos/statuses/#create-a-status)
1. [Github Webhooks](https://developer.github.com/webhooks/#delivery-headers)
1. [Github Events](https://developer.github.com/v3/activity/events/)
1. [Github Event Types & Payloads](https://developer.github.com/v3/activity/events/types/#pullrequestreviewcommentevent)
1. [Building a CI Server (Github Guide)](https://developer.github.com/v3/guides/building-a-ci-server/)
