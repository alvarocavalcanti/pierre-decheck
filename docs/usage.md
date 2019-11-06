# Usage

## Basic Feature

1. Create a pull request on the repository that has *pierre* set up
1. Add the keywords `Depends on #` (for same-repo) or "Depends on `owner/repo#`" (for external) followed by an issue/pull request number, `Depends on #2` or `Depends on owner/repo#2`, to the pull request description, or later, as a comment ![Pull Request Checks Example](pull_request_keywords.png)
1. Every time a comment is added or deleted, *pierre* will check the dependencies and update the "Checks" section: ![Pull Request Checks Example](pull_request_checks.png)

## Optional Feature: Depending on a Released PR

Usually when one has external dependencies (other repos) these dependencies requires not only a PR to be merged, but also released. To that extent, _Pierre_ offers an optional configuration: by setting the environment variable `RELEASE_LABEL` to any given value, _Pierre_ will then consider any dependency as met only if its state is `closed` and if it also has the proper label. On the screenshot below it's possible to see how it looks like when the dependency is closed but does not have the release label:

![Pull Request Checks Exemple](pull_request_checks_release_label.png)
