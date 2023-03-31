Design notes and project goal.

## Visibility

* The Service Catalog is a single tenant project, in that it's intended to be run by one organisation and only contain the information for that organization.
* Service Catalog pulls all repositories that the GitHub user accessing the site has access to and stores them in the Catalog. This is working on the assumption that all the services pulled into the Catalog are suitable to be shown there. This may not always be the case in some organisations, but recreating GitHub security outside of GitHub is not a project goal.

## GitHub App access

* The long term goal is to keep the permissions needed by the GitHub App to the minimum needed to satifsy the needs of the project.