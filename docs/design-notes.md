Some design notes and project goal.

## Visibility and Permissions

* The Service Catalog is a single tenant project, in that it's intended to be run by one organisation and only contain the information for that organization.
* Service Catalog pulls all repositories that the GitHub user accessing the site has access to and stores them in the Catalog. This is working on the assumption that all the services pulled into the Catalog are suitable to be shown there. This may not always be the case in some organisations, but recreating GitHub security outside of GitHub is not a project goal.

By default when a user logs in, it checks the organization, if the user is a `Public member` of that organization, they get full access to the Service Catalog with the ability to add, delete and change entries in the Catalog.

If the user is not a `Public member` of that organization, they will have no access.

If the settings `ALLOW_PUBLIC_READ_ACCESS` is set to `True` then the user will have read only access to the Service Catalog and all its contents. They will not able to add, delete and change any entries in the Catalog.

**Note:** be careful about using `ALLOW_PUBLIC_READ_ACCESS`, doing so with `Private` organisations and repositories will expose all the information contained in the catalog.

**Note:** changing `ALLOW_PUBLIC_READ_ACCESS` requires users to logout and login again for changes to happen. A simple way to do this is to alter the `SECRET_KEY` and restart the server.

## GitHub App access

See `/setup/` on your Service Catalog to see what is currently included.

The long term goal is to keep the permissions needed by the GitHub App to the minimum needed to satifsy the needs of the project and cope if you'd like to limit permissions, there are solutions. Currently they include:

* `contents` 👉 `write`: because the health checks run GitHub Actions. If you remove this permission, for example just setting `read` you will have to find another way to trigger the Actions in the health check repository. This could be done through cron jobs or Actions using the `cron` syntax.

* `organization_administration` 👉 `read`: so that the Catalog can find all the places that the app is installed. If you remove this, you can add in each repo individually.

* `pull_requests` 👉 `read`: so that the Catalog can create a pull request with a populated `catalog.json` to make the setup easy.

* `actions` 👉 `write`: so that the Catalog can create a pull request with a pre-populated Action file in the `.github/workflows` directory.

Events:

* `Deployments`: so that the webhooks can be sent from GitHub. If the Service Catalog is at a URL not accessible from the server, then you can manually create these using the [create-event Action](https://github.com/clearwind-ca/create-event), the API, or by polling GitHub.
* `Releases`: same as above for releases.

## Running health checks

Health checks are passed to an external service, in this case GitHub Actions. This is done because those health checks could involve whatever business logic you need. It could be pulling down, building and running arbitrary code to see if conforms with your standards. By passing this through GitHub Actions, we can use that platform for running any arbitrary code you might like in a safe and controlled environment.

Because GitHub Actions allows self hosted runners, you can send these jobs back to a local system.

Having code run elsewhere, means that we can keep our Docker container simple and focused on it's goal of collecting information about the services in your system.

