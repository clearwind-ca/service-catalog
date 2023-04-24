The Service Catalog is a Django project and installable pretty much anywhere that can meet the requirements.

Requirements:
* Python 3.9+
* Postgres database 14.6+

## Dockerfile

A Dockerfile is provided if you'd like to run it in Docker. To get a running container you'll need to do the following.

```bash
docker build . -t service-catalog
docker run -t service-catalog
```

You will also need a Postgres container to persist your data.

## Environment variables

Where possible configuration is done through environment variables which alter the settings files. Some of these settings are specific to the Service Catalog, but some are [common to all Django projects and the documentation](https://docs.djangoproject.com/en/4.1/ref/settings/) covers those.

|Variable|Effect|Required|Default if not set|
|-|-|-|-|
|ALLOWED_HOSTS|Override the Django `ALLOWED_HOSTS` setting.|Yes, for browser access if not in `DEBUG` mode.|Empty|
|CATALOG_ENV|The path to a file of enviroment variables to load. Environment variables loaded from this file will override variables loaded elsewhere.|No|(see notes below)|
|CRON_USER|The username for a user logged into the Catalog to run background updates against GitHub.|No, however background updates will fail without it|Empty|
|DATABASE_URL|The connection string to the [database using dj-database-url](https://pypi.org/project/dj-database-url/#url-schema)|Yes|Empty|
|DEBUG|Set the Django `DEBUG` mode.|No|False|
|GITHUB_APP_ID|The GitHub app configuration.|Yes|Empty|
|GITHUB_CLIENT_ID|As above.|Yes|Empty|
|GITHUB_CLIENT_SECRET|As above.|Yes|Empty|
|GITHUB_CHECK_REPOSITORY|The repository to send health checks to.|Yes|Otherwise health checks won't work|
|SECRET_KEY|Set the Django `SECRET_KEY` variable.|Yes|Empty|
|SERVICE_SCHEMA|Path on the filesystem to the schema|No|`catalog/schemas/service.json`|

### Catalog Env

The value `CATALOG_ENV` can be set to load variables from a file compatible with [python-dotenv](https://pypi.org/project/python-dotenv/).

If you are using the Dockerfile, then `CATALOG_ENV` can be passed at build time:

```bash
docker build . -t service-catalog --build-arg CATALOG_ENV=staging
```

If `CATALOG_ENV` is one of `development`, `production`, `staging` or `test` then it will find the matching `.env` file in the `catalog/envs` directory. The value can also be a file path to any other file on the filesystem as well, for example `/tmp/some-variables.env`.

If running in continuous integrations, such as Actions, where the `CI` environment variable is set then if no other environment file is specified then `envs/testing.env` will be used.

If no other environment variable is set then it will use the file `envs/development.env` will be used. This does not exist in source code and is where you can place any local development configuration.

## GitHub App

To interact with GitHub you will need to create a GitHub App. This will allow you to login to the catalog, read information from GitHub and so on.

To create an app, follow the documentation on the [GitHub website](https://docs.github.com/en/apps/creating-github-apps/creating-github-apps/creating-a-github-app).

Key settings:

* `GitHub App name`: whatever makes sense for you.
* `Homepage URL`: absolute URL to the Service Catalog that is accessible to the user.
* `Callback URL`: same as above, with the following appended to the URL `/oauth/github/callback`.

Under `Permissions & events`:

* `Repository permissions` 👉 `Contents` 👉 `Access: Read-only`
* `Repository permissions` 👉 `Metadata` 👉 `Access: Read-only`
* `Account permissions` 👉 `Email addresses` 👉 `Access: Read-only`

Once complete, `Generate a new client secret` and the copy the following settings into the environment variables:

* `App ID` into `GITHUB_APP_ID`
* `Client ID` into `GITHUB_CLIENT_ID`
* `Client secret` into `GITHUB_CLIENT_SECRET`

Restart your Service Catalog for the settings to take effect.

## Debug page

To check that your settings are good, a page at `/debug` [^1] is provided that will help you understand what the values of key settings and environment variables are.

[^1]: See [example](https://service-catalog.fly.dev/debug/)

## Background jobs

There are multiple background jobs in the system. If you are using the Dockerfile, then these are set up automatically for you, by installing the `catalog/crontab`.

If you are not using the Dockerfile, then you will need to create these manually.

### Refresh

Command: `python manage.py refresh`

Runs through all the sources in the Catalog and re-fetches the data from GitHub and updates it in the Catalog. It's the same process as hitting the `Refresh` button on the `Source` page.

By default run once per day.

Arguments:

* `--all`: runs through all the sources and refreshes them all from GitHub.
* `--source [SOURCE_SLUG]`: just refreshes the source matching the `SOURCE_SLUG` given.
* `--user`: the username of a user to connect to GitHub, this is the GitHub handle for that user.
* `--quiet`: less logging.

Environment variables:

* `CRON_USER`: If `--user` is not specified, then the command will check to see if the environment variable `CRON_USER` is set and use that.

### Send

Command: `python manage.py send`

Sends health checks to the GitHub Actions repository, so that health checks can be run.

Arguments:

* `--check`: the slug of the check to send.
* `--all-checks`: send all checks. Either `--check` or `--all-checks` must be specified.
* `--service`: the slug of the service to send checks for.
* `--all-services`: send all services. Either `--service` or `--all-services` must be specified.
* `--user`: the username of a user to connect to GitHub, this is the GitHub handle for that user.
* `--quiet`: less logging. 

As an example: `python manage.py send --all-checks --all-services` will run every health check on every service and `python manage.py send --check Log4J --service Website` will only send the health check for `Log4J` for the `Website` service.

### Truncate

Command: `python manage.py truncate`

Removes old `Log` entries in the `SystemLog` table. The default is to remove all logs older than 30 days.

Arguments:

* `--ago`: the number of days to truncate logs too. For example `--ago 30` removes all `Log` entries older than 30 days.
* `--quiet`: less logging.

### Timeout

Command: `python manage.py timeout`

Marks old health check results as `timed out`. The default is to mark logs as timed out after 6 hours.

Arguments:

* `--ago`: the number of hours to make as timed out.
* `--quiet`: less logging.

