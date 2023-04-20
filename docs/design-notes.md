Some design notes and project goal.

## Visibility

* The Service Catalog is a single tenant project, in that it's intended to be run by one organisation and only contain the information for that organization.
* Service Catalog pulls all repositories that the GitHub user accessing the site has access to and stores them in the Catalog. This is working on the assumption that all the services pulled into the Catalog are suitable to be shown there. This may not always be the case in some organisations, but recreating GitHub security outside of GitHub is not a project goal.

## GitHub App access

The long term goal is to keep the permissions needed by the GitHub App to the minimum needed to satifsy the needs of the project. Currently they include:

* `Write contents to repo`: because the health checks run GitHub Actions.

## Running health checks

Health checks are passed to an external service, in this case GitHub Actions. This is done because those health checks could involve whatever business logic you need. It could be pulling down, building and running arbitrary code to see if conforms with your standards. By passing this through GitHub Actions, we can use that platform for running any arbitrary code you might like in a safe and controlled environment.

Because GitHub Actions allows self hosted runners, you can send these jobs back to a local system.

Having code run elsewhere, means that we can keep our Docker container simple and focused on it's goal of collecting information about the services in your system.

