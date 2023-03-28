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

Where possible configuration is done through environment variables which alter the settings files.

The key environment variable `CATALOG_ENV` determines which environment file to load.

|Variable|Effect|Required|Default if not set|
|-|-|-|-|
|CATALOG_ENV|The path to the file of other enviroments to load.|No|(see notes below)|
|ALLOWED_HOSTS|Override the Django `ALLOWED_HOSTS` setting.|Yes, for browser access if not in `DEBUG` mode.|Empty|
|DATABASE_URL|The connection string to the [database using dj-database-url](https://pypi.org/project/dj-database-url/#url-schema)|Yes|Empty|
|DEBUG|Set the Django `DEBUG` mode.|No|False|
|GITHUB_APP_ID|The GitHub app configuration.|Yes|Empty|
|GITHUB_CLIENT_ID|As above.|Yes|Empty|
|GITHUB_CLIENT_SECRET|As above.|Yes|Empty|
|SECRET_KEY|Set the Django `SECRET_KEY` variable.|Yes|Empty|
|SERVICE_SCHEMA|Path on the filesystem to the schema|No|`catalog/schemas/service.json`|

If running in continuous integrations, such as Actions, where the `CI` environment variable is set then if no other environment file is specified then `envs/testing.env` will be used.

If no other environment variable is set then it will use the file `envs/development.env` will be used. This does not exist in source code and is where you can place any local development configuration.

## GitHub App

To interact with GitHub you will need to create a GitHub App. This will allow you to login to the catalog, read information from GitHub and so on.

This is done using the [app manifest flow](https://docs.github.com/en/apps/creating-github-apps/creating-github-apps/creating-a-github-app-from-a-manifest).