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
|CATALOG_ENV|The path to a file of enviroment variables to load. Environment variables loaded from this file will override variables loaded elsewhere.|No|(see notes below)|
|ALLOWED_HOSTS|Override the Django `ALLOWED_HOSTS` setting.|Yes, for browser access if not in `DEBUG` mode.|Empty|
|DATABASE_URL|The connection string to the [database using dj-database-url](https://pypi.org/project/dj-database-url/#url-schema)|Yes|Empty|
|DEBUG|Set the Django `DEBUG` mode.|No|False|
|GITHUB_APP_ID|The GitHub app configuration.|Yes|Empty|
|GITHUB_CLIENT_ID|As above.|Yes|Empty|
|GITHUB_CLIENT_SECRET|As above.|Yes|Empty|
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