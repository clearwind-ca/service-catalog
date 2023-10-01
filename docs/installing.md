The Catalog is a Django project and installable pretty much anywhere that can meet the requirements.

Requirements:
* [Python](https://www.python.org/) 3.9+
* [Postgres](https://www.postgresql.org/) database 14.6+
* [Celery](https://docs.celeryq.dev/en/stable/)

## Dockerfile

A Dockerfile is provided if you'd like to run it in Docker. To get a running container you'll need to do the following.

```bash
docker build . -t service-catalog
docker run -t service-catalog
```

You will also need a Postgres container to persist your data.

Tasks are managed through a celery backend. The docker container installs a non-persisted Redis instance in the container. However you could connect to another celery backend elsewhere.

## Environment variables

Where possible configuration is done through environment variables which alter the settings files. Some of these settings are specific to the Catalog, but some are [common to all Django projects and the documentation](https://docs.djangoproject.com/en/4.1/ref/settings/) covers those.

### Setup page

You will need set the following environment variables for Django to run:

|Variable|Effect|Required|Default if not set|
|-|-|-|-|
|ALLOWED_HOSTS|Override the Django `ALLOWED_HOSTS` setting.|Yes, for browser access if not in `DEBUG` mode.|Empty|
|SECRET_KEY|Set the Django `SECRET_KEY` variable.|Yes|Empty|

Once these are done, you can access the setup page at: `/setup/` on your catalog instance. This will page will guide you through the next steps.

### Environment variables 

The following environment variables provide access to site functionality:

|Variable|Effect|Required|Default if not set|
|-|-|-|-|
|ALLOW_PUBLIC_READ_ACCESS|Allows members outside the organisation to have read only access. See [design-notes](design-notes)|No|False|
|ALLOWED_HOSTS|Override the Django `ALLOWED_HOSTS` setting.|Yes, for browser access if not in `DEBUG` mode.|Empty|
|CATALOG_ENV|The path to a file of enviroment variables to load. Environment variables loaded from this file will override variables loaded elsewhere.|No|(see notes below)|
|CELERY_BROKER_URL|The celery broker backend to connect to|No|`redis://localhost:6379/0`|
|DATABASE_URL|The connection string to the [database using dj-database-url](https://pypi.org/project/dj-database-url/#url-schema)|Yes|Empty|
|DEBUG|Set the Django `DEBUG` mode.|No|False|
|GITHUB_CHECK_REPOSITORY|The repository to send health checks to, see [health checks for more](health-checks.md)|No|Health checks won't work|
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

### GitHub App

To interact with GitHub you will need to create a GitHub App. This will allow you to login to the catalog, read information from GitHub and so on.

Visiting `/setup/` will provide you with a form to create the GitHub App and then you need to populate following environment variables:

|Variable|Effect|Required|Default if not set|
|-|-|-|-|
|GITHUB_APP_ID|The GitHub app configuration.|Yes|Empty|
|GITHUB_CLIENT_ID|As above.|Yes|Empty|
|GITHUB_CLIENT_SECRET|As above.|Yes|Empty|
|GITHUB_PEM|As above.|Yes|Empty|
|GITHUB_WEBHOOK_SECRET|If set, [signature checking](https://docs.github.com/en/webhooks-and-events/webhooks/securing-your-webhooks) will occur on webhooks|No|No signature checking occurs|

**Note:** To allow users to login you must give the GitHub app access to `Account Permissions` 👉 `Email addresses` 👉 `Access: Read-only`. Currently this does not seem possible to set from the manifest process and must be done on https://github.com.

By default, the app is set to private. See [Making a GitHub App public or private](https://docs.github.com/en/apps/creating-github-apps/setting-up-a-github-app/making-a-github-app-public-or-private) for more information.

## Background jobs

There are multiple background jobs in the system. If you are using the Dockerfile, then these are set up automatically for you and run through Celery regularly.

You can also run some of these jobs through management commands.

See [the code for default job schedules and values](catalog/celery.py).

### Refresh

Command: `python manage.py refresh`

Runs through all the sources in the Catalog and re-fetches the data from GitHub and updates it in the Catalog. It's the same process as hitting the `Refresh` button on the `Source` page.

Arguments:

* `--all`: runs through all the sources and refreshes them all from GitHub.
* `--source [SOURCE_SLUG]`: just refreshes the source matching the `SOURCE_SLUG` given.
* `--quiet`: less logging.

### Send

Command: `python manage.py send`

Sends health checks to the GitHub Actions repository, so that health checks can be run.

Arguments:

* `--check`: the slug of the check to send.
* `--all-checks`: send all checks. Either `--check` or `--all-checks` must be specified.
* `--service`: the slug of the service to send checks for.
* `--all-services`: send all services. Either `--service` or `--all-services` must be specified.
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

