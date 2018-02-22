[![CircleCI](https://circleci.com/gh/alvarocavalcanti/pierre-decheck/tree/master.svg?style=svg)](https://circleci.com/gh/alvarocavalcanti/pierre-decheck/tree/master)

# Pierre DeCheck
Pull Request Dependency Check.

It checks for pull requests dependencies, specified using keywords on pull request body or comments.

**Currently supported: dependencies of the same repository only.**

# Installation

1. Checkout/download this repo
1. Publish the app wherever suits you the best (it already has [Heroku](http://www.heroku.com) configuration in place) and take note of the app's URL
1. Go to the repository you want to set it up, then go to **Settings > Webhooks > Add Webhook**
1. Under "Payload URL" enter `<YOUR_APP_URL>/webhook`
1. Under "Content type" select "application/json"
1. Under "Which events would you like to trigger this webhook?" select "Let me select individual events." and then: "Commit comment", "Issue comment", "Pull request" and "Pull request review comment"
1. Finally, make sure "Active" is selected and then create the webhook
1. [Create an access token for your repo](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/)
1. Add the token as an environment variable for you app, labeled `GITHUB_TOKEN`

# Usage

1. Create a pull request on the repository that has *pierre* set up
1. Add the keywords "Depends on #" followed by an issue/pull request number, `Depends on #2`, to the pull request description, or later, as a comment
![Pull Request Checks Example](pull_request_keywords.png)
1. Every time a comment is added or deleted, *pierre* will check the dependencies and update the "Checks" section:
![Pull Request Checks Example](pull_request_checks.png)

## References

1. [Github Repo Statuses](https://developer.github.com/v3/repos/statuses/#create-a-status)
1. [Github Webhooks](https://developer.github.com/webhooks/#delivery-headers)
1. [Github Events](https://developer.github.com/v3/activity/events/)
1. [Github Event Types & Payloads](https://developer.github.com/v3/activity/events/types/#pullrequestreviewcommentevent)
1. [Building a CI Server (Github Guide)](https://developer.github.com/v3/guides/building-a-ci-server/)
